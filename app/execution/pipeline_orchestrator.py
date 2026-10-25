"""
Autonomous Pipeline Orchestrator for Agent Forge.
Orchestrates the complete research lifecycle end-to-end:
Task Analysis → Architecture V1 → Run 1 Execution → Run 1 Evaluation →
Failure Diagnosis & Reflection → Architecture Mutation (V2) → Hard-Constraint Validation →
Run 2 Execution → Run 2 Evaluation → Autonomous Decision Gate → Durable Memory Persistence.

Emits live SSE telemetry events for every stage transition and maintains
authoritative state in the database.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.core.logging import logger
from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec
from app.schemas.execution import ExecutionResult
from app.schemas.evaluation import EvaluationResult
from app.schemas.reflection import ReflectionResult
from app.schemas.execution_event import ExecutionEventType, ExecutionStage, sanitize_payload
from app.execution.event_emitter import ExecutionEventEmitter
from app.execution.event_broadcaster import broadcaster
from app.memory.database import AsyncSessionFactory
from app.memory.repository import DatabaseRepository
from app.memory.models import ExecutionRecordORM
from app.memory.memory_schema import EvolutionMemoryRecord
from app.memory.memory_store import MemoryStore
from app.schemas.validator import ArchitectureValidator
from app.evaluation.evaluator import Evaluator
from app.evaluation.failure_analyzer import FailureAnalyzer
from app.reflection.reflection_engine import ReflectionEngine
from app.reflection.architecture_modifier import ArchitectureModifier
from app.evaluation.decision_policy import EvolutionDecisionPolicy, DecisionStatus, EvolutionDecision

# Module-level store sync
from app.api.task_routes import _task_store
from app.api.execution_routes import _execution_store, _execute_pipeline_core
from app.api.evaluation_routes import _evaluation_store


class AutonomousPipelineOrchestrator:
    """
    Executes the self-evolution thesis loop autonomously:
    Executes Run 1, evaluates results, reflects on architectural root causes,
    synthesizes candidate mutation V2 if warranted, enforces hard constraints,
    re-executes Run 2, and renders a deterministic decision verdict.
    """

    def __init__(
        self,
        task_id: str,
        task_spec: TaskSpec,
        architecture_spec: ArchitectureSpec,
        execution_id: Optional[str] = None,
        use_real_engine: bool = True,
    ):
        self.task_id = task_id
        self.task_spec = task_spec
        self.architecture_spec = architecture_spec
        self.execution_id = execution_id or f"exec_{uuid.uuid4().hex[:8]}"
        self.use_real_engine = use_real_engine
        self.max_retries = 1

    async def execute_full_pipeline(self) -> Dict[str, Any]:
        """
        Main autonomous pipeline driver.
        Executes all stages in a dedicated background async context with DB persistence.
        """
        async with AsyncSessionFactory() as db:
            repo = DatabaseRepository(db)
            emitter = ExecutionEventEmitter(
                execution_id=self.execution_id,
                task_id=self.task_id,
                db=db,
                broadcaster_instance=broadcaster,
            )
            await emitter.init_sequence_from_db()

            try:
                # -------------------------------------------------------------
                # STAGE 1: RUN 1 EXECUTION
                # -------------------------------------------------------------
                logger.info(f"[AUTONOMOUS_PIPELINE] Starting Run 1 for task={self.task_id}, exec={self.execution_id}")
                exec_1_dict = await _execute_pipeline_core(
                    exec_id=self.execution_id,
                    task_id=self.task_id,
                    task_spec=self.task_spec,
                    architecture_spec=self.architecture_spec,
                    target_run=1,
                    use_real_engine=self.use_real_engine,
                    db=db,
                    emitter=emitter,
                    is_pipeline_stage=True,
                )
                await db.commit()

                # -------------------------------------------------------------
                # STAGE 2: RUN 1 EVALUATION & REFLECTION
                # -------------------------------------------------------------
                eval_1_res, refl_1_res, score_1 = await self._evaluate_and_reflect(
                    architecture=self.architecture_spec,
                    execution_dict=exec_1_dict,
                    run_number=1,
                    db=db,
                    repo=repo,
                    emitter=emitter,
                )
                await db.commit()

                # -------------------------------------------------------------
                # STAGE 3: FAILURE-DRIVEN SELF-EVOLUTION DECISION
                # -------------------------------------------------------------
                recommendations = refl_1_res.recommendations if refl_1_res else []
                logger.info(
                    f"[AUTONOMOUS_PIPELINE] Run 1 score: {score_1:.2%}, "
                    f"recommendations count: {len(recommendations)}"
                )

                # If no recommendations produced, baseline passed without architectural weakness
                if not recommendations:
                    await emitter.emit(
                        event_type=ExecutionEventType.EXECUTION_COMPLETED,
                        message=f"Autonomous pipeline complete. Baseline architecture satisfied criteria ({score_1:.1%}). No mutation required.",
                        stage=ExecutionStage.SYNTHESIS.value,
                        status="completed",
                        data={"final_score": score_1, "evolved": False},
                    )
                    await db.commit()
                    return {
                        "task_id": self.task_id,
                        "execution_id": self.execution_id,
                        "status": "completed",
                        "evolved": False,
                        "v1_score": score_1,
                    }

                # Self-Evolution triggered: propose candidate mutation
                await emitter.emit(
                    event_type=ExecutionEventType.EVOLUTION_PROPOSED,
                    message=f"Diagnosed {len(refl_1_res.identified_issues)} issues. Proposing architectural mutation ({len(recommendations)} recommendations).",
                    stage=ExecutionStage.REFLECTION.value,
                    data={
                        "recommendations_count": len(recommendations),
                        "top_action": recommendations[0].action if recommendations else "MUTATE",
                        "reason": recommendations[0].reason if recommendations else "Failure recovery",
                    },
                )

                # Mutate architecture V1 -> Candidate V2
                modifier = ArchitectureModifier()
                candidate_v2 = modifier.mutate_architecture(
                    base_architecture=self.architecture_spec,
                    reflection=refl_1_res,
                )

                # -------------------------------------------------------------
                # STAGE 4: HARD CONSTRAINT & INVARIANT VALIDATION
                # -------------------------------------------------------------
                val_result = ArchitectureValidator.validate(candidate_v2, task_spec=self.task_spec)
                constraint_errors: List[str] = list(val_result.error_messages)

                # Check task constraints explicitly
                if self.task_spec:
                    if self.task_spec.max_agents and len(candidate_v2.agents) > self.task_spec.max_agents:
                        constraint_errors.append(
                            f"Agent count ({len(candidate_v2.agents)}) exceeds max_agents limit ({self.task_spec.max_agents})"
                        )
                    if self.task_spec.forbidden_tools:
                        for a in candidate_v2.agents:
                            for ft in self.task_spec.forbidden_tools:
                                if ft in a.tools:
                                    constraint_errors.append(f"Agent '{a.agent_id}' uses forbidden tool '{ft}'")

                if constraint_errors:
                    # Constraint violation: reject candidate evolution
                    logger.warning(
                        f"[AUTONOMOUS_PIPELINE] Candidate architecture violated constraints: {constraint_errors}"
                    )
                    rejection_decision = EvolutionDecision(
                        decision_id=f"dec_{uuid.uuid4().hex[:10]}",
                        task_id=self.task_id,
                        status=DecisionStatus.REJECTED,
                        v1_architecture_id=self.architecture_spec.architecture_id,
                        v2_architecture_id=candidate_v2.architecture_id if candidate_v2 else "",
                        v1_execution_id=self.execution_id,
                        v2_execution_id="",
                        v1_evaluation_id=eval_1_res.evaluation_id,
                        v2_evaluation_id="",
                        v1_overall_score=score_1,
                        v2_overall_score=0.0,
                        score_delta=0.0,
                        metric_deltas={},
                        hard_constraints_satisfied=False,
                        validation_errors=constraint_errors,
                        reason_codes=["HARD_CONSTRAINT_VIOLATED"],
                        rationale=f"Candidate architecture rejected: {'; '.join(constraint_errors)}",
                    )
                    await repo.save_decision(rejection_decision)
                    task_entry = _task_store.get(self.task_id) or {}
                    task_entry["evolution_decision"] = rejection_decision.model_dump()
                    _task_store[self.task_id] = task_entry

                    await emitter.emit(
                        event_type=ExecutionEventType.EVOLUTION_REJECTED,
                        message=f"Candidate architecture rejected: {'; '.join(constraint_errors)}",
                        stage=ExecutionStage.EVOLUTION_DECISION.value,
                        data={
                            "status": "REJECTED",
                            "reason_code": "CONSTRAINT_VIOLATION",
                            "reason_codes": ["HARD_CONSTRAINT_VIOLATED"],
                            "errors": constraint_errors,
                        },
                    )
                    await emitter.emit(
                        event_type=ExecutionEventType.EXECUTION_COMPLETED,
                        message=f"Autonomous pipeline concluded. Candidate rejected due to hard constraint violations.",
                        stage=ExecutionStage.SYNTHESIS.value,
                        status="completed",
                        data={"evolved": False, "rejected_reason": "CONSTRAINT_VIOLATION"},
                    )
                    await db.commit()
                    return {
                        "task_id": self.task_id,
                        "execution_id": self.execution_id,
                        "status": "completed",
                        "evolved": False,
                        "decision": "REJECTED",
                        "errors": constraint_errors,
                    }

                # Candidate is valid! Persist V2 architecture
                await emitter.emit(
                    event_type=ExecutionEventType.EVOLUTION_VALIDATED,
                    message=f"Candidate architecture '{candidate_v2.architecture_id}' passed all invariant and hard-constraint checks.",
                    stage=ExecutionStage.EVOLUTION_DECISION.value,
                    data={"is_valid": True, "agent_count": len(candidate_v2.agents), "topology": candidate_v2.topology.value},
                )

                await repo.save_architecture(
                    candidate_v2,
                    version="v2",
                    parent_architecture_id=self.architecture_spec.architecture_id,
                )
                task_entry = _task_store.get(self.task_id) or {}
                if "architecture_versions" not in task_entry:
                    task_entry["architecture_versions"] = {
                        "v1": self.architecture_spec.model_dump(),
                    }
                task_entry["architecture_versions"]["v2"] = candidate_v2.model_dump()
                task_entry["architecture_spec"] = candidate_v2.model_dump()
                _task_store[self.task_id] = task_entry
                await db.commit()

                # -------------------------------------------------------------
                # STAGE 5: RUN 2 (EVOLVED ARCHITECTURE) EXECUTION
                # -------------------------------------------------------------
                exec_2_id = f"exec_{uuid.uuid4().hex[:8]}"
                await emitter.emit(
                    event_type=ExecutionEventType.EXECUTION_STAGE_STARTED,
                    message=f"Beginning Run 2 execution on evolved architecture '{candidate_v2.architecture_id}' ({len(candidate_v2.agents)} agents)",
                    stage=ExecutionStage.AGENT_EXECUTION.value,
                    data={"run_number": 2, "architecture_id": candidate_v2.architecture_id},
                )

                exec_2_dict = await _execute_pipeline_core(
                    exec_id=exec_2_id,
                    task_id=self.task_id,
                    task_spec=self.task_spec,
                    architecture_spec=candidate_v2,
                    target_run=2,
                    use_real_engine=self.use_real_engine,
                    db=db,
                    emitter=emitter,
                    is_pipeline_stage=True,
                )
                await db.commit()

                # -------------------------------------------------------------
                # STAGE 6: RUN 2 EVALUATION
                # -------------------------------------------------------------
                eval_2_res, refl_2_res, score_2 = await self._evaluate_and_reflect(
                    architecture=candidate_v2,
                    execution_dict=exec_2_dict,
                    run_number=2,
                    db=db,
                    repo=repo,
                    emitter=emitter,
                )
                await db.commit()

                # -------------------------------------------------------------
                # STAGE 7: DETERMINISTIC EVOLUTION DECISION GATE
                # -------------------------------------------------------------
                decision = EvolutionDecisionPolicy.evaluate_evolution(
                    v1_architecture=self.architecture_spec,
                    v2_architecture=candidate_v2,
                    v1_execution=exec_1_dict,
                    v2_execution=exec_2_dict,
                    v1_evaluation=eval_1_res,
                    v2_evaluation=eval_2_res,
                    task_spec=self.task_spec,
                )

                await repo.save_decision(decision)
                decision_dict = decision.model_dump()
                task_entry["evolution_decision"] = decision_dict
                _task_store[self.task_id] = task_entry

                ev_type = (
                    ExecutionEventType.EVOLUTION_ACCEPTED
                    if decision.status.value.upper() == "ACCEPTED"
                    else ExecutionEventType.EVOLUTION_REJECTED
                )
                await emitter.emit(
                    event_type=ev_type,
                    message=f"Evolution decision {decision.status.value}: {decision.rationale}",
                    stage=ExecutionStage.EVOLUTION_DECISION.value,
                    data={
                        "status": decision.status.value,
                        "score_delta": decision.score_delta,
                        "reason_codes": decision.reason_codes,
                        "v1_score": score_1,
                        "v2_score": score_2,
                    },
                )

                # Conclude autonomous pipeline
                await emitter.emit(
                    event_type=ExecutionEventType.EXECUTION_COMPLETED,
                    message=(
                        f"Autonomous research pipeline complete. Verdict: {decision.status.value} "
                        f"(Score: {score_1:.1%} → {score_2:.1%}, Δ={decision.score_delta:+.1%})"
                    ),
                    stage=ExecutionStage.SYNTHESIS.value,
                    status="completed",
                    data={
                        "verdict": decision.status.value,
                        "v1_execution_id": self.execution_id,
                        "v2_execution_id": exec_2_id,
                        "v1_score": score_1,
                        "v2_score": score_2,
                        "score_delta": decision.score_delta,
                        "evolved": True,
                    },
                )
                await db.commit()

                return {
                    "task_id": self.task_id,
                    "v1_execution_id": self.execution_id,
                    "v2_execution_id": exec_2_id,
                    "status": "completed",
                    "evolved": True,
                    "decision": decision.status.value,
                    "v1_score": score_1,
                    "v2_score": score_2,
                    "score_delta": decision.score_delta,
                }

            except Exception as exc:
                logger.error(f"[AUTONOMOUS_PIPELINE] Execution failed for {self.execution_id}: {exc}", exc_info=True)
                await emitter.emit(
                    event_type=ExecutionEventType.EXECUTION_FAILED,
                    message=f"Autonomous pipeline aborted: {str(exc)[:150]}",
                    stage=ExecutionStage.SYNTHESIS.value,
                    status="failed",
                    error=str(exc)[:200],
                )
                await db.commit()
                raise

    async def _evaluate_and_reflect(
        self,
        architecture: ArchitectureSpec,
        execution_dict: Dict[str, Any],
        run_number: int,
        db: Any,
        repo: DatabaseRepository,
        emitter: ExecutionEventEmitter,
    ) -> tuple[EvaluationResult, ReflectionResult, float]:
        """Helper to run evaluation, failure analysis, and reflection."""
        exec_id = execution_dict.get("execution_id", self.execution_id)
        await emitter.emit(
            event_type=ExecutionEventType.EVALUATION_STARTED,
            message=f"Evaluating Run #{run_number} execution against task constraints and metrics",
            stage=ExecutionStage.EVALUATION.value,
            data={"run_number": run_number, "architecture_id": architecture.architecture_id},
        )

        exec_model = (
            execution_dict
            if isinstance(execution_dict, ExecutionResult)
            else ExecutionResult.model_validate(execution_dict)
        )

        evaluator = Evaluator()
        eval_res = evaluator.evaluate(
            task=self.task_spec,
            architecture=architecture,
            execution=exec_model,
        )
        eval_res.execution_id = exec_id

        reflection_engine = ReflectionEngine(failure_analyzer=FailureAnalyzer())
        refl_res = reflection_engine.reflect(
            evaluation_result=eval_res,
            architecture=architecture,
            task=self.task_spec,
            execution=exec_model,
        )

        m = eval_res.metrics
        accuracy_term = getattr(m, "accuracy", m.task_success) or m.task_success
        success_rating = round(
            0.4 * m.task_success + 0.3 * m.quality + 0.2 * m.completeness + 0.1 * accuracy_term, 4
        )

        await emitter.emit(
            event_type=ExecutionEventType.EVALUATION_COMPLETED,
            message=f"Run #{run_number} evaluation finished. Success rating: {success_rating:.1%}",
            stage=ExecutionStage.EVALUATION.value,
            data={
                "run_number": run_number,
                "success_rating": success_rating,
                "metrics": m.model_dump() if hasattr(m, "model_dump") else {},
                "identified_issues_count": len(refl_res.identified_issues),
                "recommendations_count": len(refl_res.recommendations),
            },
        )

        # Save to EvolutionMemory
        rec_summary = None
        if refl_res.recommendations:
            top = refl_res.recommendations[0]
            rec_summary = f"{top.action}: {top.reason or top.details.get('role', '')}"

        memory_record = EvolutionMemoryRecord(
            record_id=f"mem_{uuid.uuid4().hex[:12]}",
            task_spec=self.task_spec,
            architecture_spec=architecture,
            evaluation_result=eval_res,
            reflection_result=refl_res,
            success_rating=success_rating,
            run_number=run_number,
            task_type=self.task_spec.task_type,
            complexity=self.task_spec.complexity,
            timestamp=datetime.now(timezone.utc),
            execution_duration_seconds=float(execution_dict.get("duration_seconds", 0.0)),
            agent_count=len(architecture.agents),
            topology=architecture.topology.value if hasattr(architecture.topology, "value") else str(architecture.topology),
            recommendation_summary=rec_summary,
        )
        mem_store = MemoryStore(db)
        saved_record_id = await mem_store.save_record(memory_record)

        await repo.save_evaluation(
            evaluation_result=eval_res,
            reflection_result=refl_res,
            run_number=run_number,
            memory_record_id=saved_record_id,
            execution_id=exec_id,
        )

        eval_record = {
            "evaluation_result": eval_res.model_dump(),
            "reflection_result": refl_res.model_dump(),
            "memory_record_id": saved_record_id,
            "success_rating": success_rating,
            "run_number": run_number,
            "recommendation_summary": rec_summary,
        }
        _evaluation_store[eval_res.evaluation_id] = eval_record

        task_entry = _task_store.get(self.task_id) or {}
        if "evaluations" not in task_entry:
            task_entry["evaluations"] = {}
        task_entry["evaluations"][f"run_{run_number}"] = eval_record
        task_entry["latest_evaluation_id"] = eval_res.evaluation_id
        task_entry["latest_evaluation"] = eval_record
        _task_store[self.task_id] = task_entry

        return eval_res, refl_res, success_rating
