"""
Unified Database Repository for Agent Forge.
Persists and retrieves Tasks, Architectures, Executions, Evaluations, and Evolution Decisions.
Provides guaranteed state persistence across server restarts.
"""

import json
from typing import Optional, List, Dict, Any
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.models import (
    TaskRecordORM,
    ArchitectureRecordORM,
    ExecutionRecordORM,
    EvaluationRecordORM,
    EvolutionDecisionORM,
    ExecutionEventORM,
)
from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec
from app.schemas.execution import ExecutionResult
from app.schemas.evaluation import EvaluationResult
from app.schemas.reflection import ReflectionResult
from app.schemas.execution_event import ExecutionEvent, ExecutionEventType, sanitize_payload
from app.evaluation.decision_policy import EvolutionDecision


class DatabaseRepository:
    """Async repository for all Agent Forge entity models."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------- Task Operations ---------------- #

    async def save_task(
        self,
        task_spec: TaskSpec,
        architecture_spec: ArchitectureSpec,
        run_number: int = 1,
        status: str = "architecture_ready",
    ) -> None:
        """Persist or update task record and architecture v1."""
        stmt = select(TaskRecordORM).where(TaskRecordORM.task_id == task_spec.task_id)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            record = TaskRecordORM(
                task_id=task_spec.task_id,
                user_prompt=task_spec.user_prompt,
                status=status,
                run_number=run_number,
                task_spec_json=task_spec.model_dump_json(),
                latest_architecture_id=architecture_spec.architecture_id,
            )
            self.db.add(record)
        else:
            record.status = status
            record.run_number = run_number
            record.task_spec_json = task_spec.model_dump_json()
            record.latest_architecture_id = architecture_spec.architecture_id

        # Also save the architecture specification
        await self.save_architecture(architecture_spec, version="v1")
        await self.db.flush()

    async def update_task_status(
        self,
        task_id: str,
        status: Optional[str] = None,
        run_number: Optional[int] = None,
        latest_architecture_id: Optional[str] = None,
        latest_execution_id: Optional[str] = None,
        latest_evaluation_id: Optional[str] = None,
    ) -> None:
        """Update pointers and status on an existing task."""
        stmt = select(TaskRecordORM).where(TaskRecordORM.task_id == task_id)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            if status:
                record.status = status
            if run_number is not None:
                record.run_number = run_number
            if latest_architecture_id:
                record.latest_architecture_id = latest_architecture_id
            if latest_execution_id:
                record.latest_execution_id = latest_execution_id
            if latest_evaluation_id:
                record.latest_evaluation_id = latest_evaluation_id
            await self.db.flush()

    async def get_task_composite(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch task along with associated architectures, executions, evaluations,
        and evolution decision into a unified dictionary structure.
        """
        stmt = select(TaskRecordORM).where(TaskRecordORM.task_id == task_id)
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            return None

        task_spec_data = json.loads(record.task_spec_json)

        # Fetch architectures for task
        arch_stmt = (
            select(ArchitectureRecordORM)
            .where(ArchitectureRecordORM.task_id == task_id)
            .order_by(ArchitectureRecordORM.created_at.asc())
        )
        arch_rows = (await self.db.execute(arch_stmt)).scalars().all()
        versions: Dict[str, Any] = {}
        arch_spec = None
        for a in arch_rows:
            parsed = json.loads(a.architecture_spec_json)
            versions[a.version] = parsed
            if record.latest_architecture_id == a.architecture_id or not arch_spec:
                arch_spec = parsed

        # Fetch executions
        exec_stmt = (
            select(ExecutionRecordORM)
            .where(ExecutionRecordORM.task_id == task_id)
            .order_by(ExecutionRecordORM.run_number.asc())
        )
        exec_rows = (await self.db.execute(exec_stmt)).scalars().all()
        executions = [json.loads(e.execution_result_json) for e in exec_rows]

        # Fetch evaluations
        eval_stmt = (
            select(EvaluationRecordORM)
            .where(EvaluationRecordORM.task_id == task_id)
            .order_by(EvaluationRecordORM.run_number.asc())
        )
        eval_rows = (await self.db.execute(eval_stmt)).scalars().all()
        evaluations_dict: Dict[str, Any] = {}
        latest_eval_record = None
        for ev in eval_rows:
            ev_dict = {
                "evaluation_result": json.loads(ev.evaluation_result_json),
                "reflection_result": json.loads(ev.reflection_result_json),
                "success_rating": ev.success_rating,
                "run_number": ev.run_number,
                "memory_record_id": ev.memory_record_id,
            }
            evaluations_dict[f"run_{ev.run_number}"] = ev_dict
            latest_eval_record = ev_dict

        # Fetch decision if any
        decision_stmt = select(EvolutionDecisionORM).where(EvolutionDecisionORM.task_id == task_id)
        dec_row = (await self.db.execute(decision_stmt)).scalar_one_or_none()
        decision_data = json.loads(dec_row.decision_json) if dec_row else None

        return {
            "task_id": record.task_id,
            "user_prompt": record.user_prompt,
            "status": record.status,
            "run_number": record.run_number,
            "task_spec": task_spec_data,
            "architecture_spec": arch_spec,
            "architecture_versions": versions,
            "executions": executions,
            "evaluations": evaluations_dict,
            "latest_evaluation": latest_eval_record,
            "latest_evaluation_id": record.latest_evaluation_id,
            "evolution_decision": decision_data,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }

    async def list_tasks(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List tasks ordered by recency."""
        stmt = (
            select(TaskRecordORM)
            .order_by(desc(TaskRecordORM.created_at))
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        results = []
        for r in rows:
            results.append(
                {
                    "task_id": r.task_id,
                    "user_prompt": r.user_prompt,
                    "status": r.status,
                    "run_number": r.run_number,
                    "task_spec": json.loads(r.task_spec_json),
                    "latest_architecture_id": r.latest_architecture_id,
                    "latest_execution_id": r.latest_execution_id,
                    "latest_evaluation_id": r.latest_evaluation_id,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        return results

    # ---------------- Architecture Operations ---------------- #

    async def save_architecture(
        self,
        architecture_spec: ArchitectureSpec,
        version: str = "v1",
        parent_architecture_id: Optional[str] = None,
    ) -> None:
        """Persist an architecture version."""
        stmt = select(ArchitectureRecordORM).where(
            ArchitectureRecordORM.architecture_id == architecture_spec.architecture_id
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if not existing:
            record = ArchitectureRecordORM(
                architecture_id=architecture_spec.architecture_id,
                task_id=architecture_spec.task_id,
                version=version,
                parent_architecture_id=parent_architecture_id,
                topology=architecture_spec.topology.value
                if hasattr(architecture_spec.topology, "value")
                else str(architecture_spec.topology),
                agent_count=len(architecture_spec.agents),
                architecture_spec_json=architecture_spec.model_dump_json(),
            )
            self.db.add(record)
            await self.db.flush()

    async def get_architecture(self, architecture_id: str) -> Optional[ArchitectureSpec]:
        """Fetch architecture by ID."""
        stmt = select(ArchitectureRecordORM).where(
            ArchitectureRecordORM.architecture_id == architecture_id
        )
        row = (await self.db.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        return ArchitectureSpec.model_validate_json(row.architecture_spec_json)

    async def get_architectures_for_task(self, task_id: str) -> List[ArchitectureSpec]:
        """Fetch all architecture versions for a task."""
        stmt = (
            select(ArchitectureRecordORM)
            .where(ArchitectureRecordORM.task_id == task_id)
            .order_by(ArchitectureRecordORM.created_at.asc())
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        return [ArchitectureSpec.model_validate_json(r.architecture_spec_json) for r in rows]

    # ---------------- Execution Operations ---------------- #

    async def save_execution(
        self,
        execution_result: ExecutionResult,
        run_number: int = 1,
    ) -> None:
        """Persist execution results and node traces."""
        stmt = select(ExecutionRecordORM).where(
            ExecutionRecordORM.execution_id == execution_result.execution_id
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if not existing:
            record = ExecutionRecordORM(
                execution_id=execution_result.execution_id,
                task_id=execution_result.task_id,
                architecture_id=execution_result.architecture_id,
                run_number=run_number,
                status=execution_result.status.value
                if hasattr(execution_result.status, "value")
                else str(execution_result.status),
                duration_seconds=execution_result.execution_time_seconds,
                execution_result_json=execution_result.model_dump_json(),
            )
            self.db.add(record)
            await self.db.flush()

    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Fetch execution result as dict."""
        stmt = select(ExecutionRecordORM).where(
            ExecutionRecordORM.execution_id == execution_id
        )
        row = (await self.db.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        return json.loads(row.execution_result_json)

    # ---------------- Execution Event Operations ---------------- #

    async def get_next_event_sequence(self, execution_id: str) -> int:
        """Atomically query next monotonic sequence number for an execution."""
        stmt = select(func.coalesce(func.max(ExecutionEventORM.sequence_number), 0)).where(
            ExecutionEventORM.execution_id == execution_id
        )
        current_max = (await self.db.execute(stmt)).scalar_one()
        return int(current_max) + 1

    async def save_execution_event(self, event: ExecutionEvent) -> ExecutionEvent:
        """Persist an execution lifecycle event with monotonic sequence guarantee."""
        seq = event.sequence_number
        if seq <= 0:
            seq = await self.get_next_event_sequence(event.execution_id)
            event.sequence_number = seq

        sanitized_data = sanitize_payload(event.data)
        record = ExecutionEventORM(
            event_id=event.event_id,
            execution_id=event.execution_id,
            task_id=event.task_id,
            sequence_number=seq,
            event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
            timestamp=event.timestamp,
            status=event.status,
            agent_id=event.agent_id,
            stage=event.stage,
            message=event.message,
            data_json=json.dumps(sanitized_data, default=str),
            error=event.error,
        )
        self.db.add(record)
        await self.db.flush()
        return event

    async def list_execution_events(
        self,
        execution_id: str,
        after_seq: int = 0,
        limit: int = 1000,
    ) -> List[ExecutionEvent]:
        """Fetch chronological execution events strictly after sequence number."""
        stmt = (
            select(ExecutionEventORM)
            .where(
                ExecutionEventORM.execution_id == execution_id,
                ExecutionEventORM.sequence_number > after_seq,
            )
            .order_by(ExecutionEventORM.sequence_number.asc())
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        events: List[ExecutionEvent] = []
        for r in rows:
            events.append(
                ExecutionEvent(
                    event_id=r.event_id,
                    execution_id=r.execution_id,
                    task_id=r.task_id,
                    sequence_number=r.sequence_number,
                    event_type=ExecutionEventType(r.event_type) if r.event_type in [e.value for e in ExecutionEventType] else ExecutionEventType.AGENT_ACTION,
                    timestamp=r.timestamp,
                    status=r.status,
                    agent_id=r.agent_id,
                    stage=r.stage,
                    message=r.message,
                    data=json.loads(r.data_json) if r.data_json else {},
                    error=r.error,
                )
            )
        return events

    async def get_latest_execution_event(self, execution_id: str) -> Optional[ExecutionEvent]:
        """Get the most recent event for an execution."""
        stmt = (
            select(ExecutionEventORM)
            .where(ExecutionEventORM.execution_id == execution_id)
            .order_by(ExecutionEventORM.sequence_number.desc())
            .limit(1)
        )
        r = (await self.db.execute(stmt)).scalar_one_or_none()
        if not r:
            return None
        return ExecutionEvent(
            event_id=r.event_id,
            execution_id=r.execution_id,
            task_id=r.task_id,
            sequence_number=r.sequence_number,
            event_type=ExecutionEventType(r.event_type) if r.event_type in [e.value for e in ExecutionEventType] else ExecutionEventType.AGENT_ACTION,
            timestamp=r.timestamp,
            status=r.status,
            agent_id=r.agent_id,
            stage=r.stage,
            message=r.message,
            data=json.loads(r.data_json) if r.data_json else {},
            error=r.error,
        )

    # ---------------- Evaluation Operations ---------------- #

    async def save_evaluation(
        self,
        evaluation_result: EvaluationResult,
        reflection_result: ReflectionResult,
        run_number: int = 1,
        memory_record_id: Optional[str] = None,
        execution_id: Optional[str] = None,
    ) -> None:
        """Persist evaluation and reflection records."""
        stmt = select(EvaluationRecordORM).where(
            EvaluationRecordORM.evaluation_id == evaluation_result.evaluation_id
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if not existing:
            resolved_exec_id = (
                execution_id
                or getattr(evaluation_result, "execution_id", None)
                or f"exec_{evaluation_result.task_id}"
            )
            record = EvaluationRecordORM(
                evaluation_id=evaluation_result.evaluation_id,
                task_id=evaluation_result.task_id,
                execution_id=resolved_exec_id,
                architecture_id=evaluation_result.architecture_id,
                run_number=run_number,
                success_rating=evaluation_result.overall_score,
                evaluation_result_json=evaluation_result.model_dump_json(),
                reflection_result_json=reflection_result.model_dump_json(),
                memory_record_id=memory_record_id,
            )
            self.db.add(record)
            await self.db.flush()

    async def get_evaluation(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch evaluation and reflection record."""
        stmt = select(EvaluationRecordORM).where(
            EvaluationRecordORM.evaluation_id == evaluation_id
        )
        row = (await self.db.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        return {
            "evaluation_result": json.loads(row.evaluation_result_json),
            "reflection_result": json.loads(row.reflection_result_json),
            "success_rating": row.success_rating,
            "run_number": row.run_number,
            "memory_record_id": row.memory_record_id,
        }

    # ---------------- Evolution Decision Operations ---------------- #

    async def save_decision(self, decision: EvolutionDecision) -> None:
        """Persist deterministic evolution decision."""
        stmt = select(EvolutionDecisionORM).where(
            EvolutionDecisionORM.decision_id == decision.decision_id
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if not existing:
            record = EvolutionDecisionORM(
                decision_id=decision.decision_id,
                task_id=decision.task_id,
                v1_architecture_id=decision.v1_architecture_id,
                v2_architecture_id=decision.v2_architecture_id,
                v1_execution_id=decision.v1_execution_id,
                v2_execution_id=decision.v2_execution_id,
                status=decision.status.value
                if hasattr(decision.status, "value")
                else str(decision.status),
                score_delta=decision.score_delta,
                decision_json=decision.model_dump_json(),
            )
            self.db.add(record)
            await self.db.flush()

    async def get_decision_for_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Fetch evolution decision for a given task."""
        stmt = (
            select(EvolutionDecisionORM)
            .where(EvolutionDecisionORM.task_id == task_id)
            .order_by(desc(EvolutionDecisionORM.created_at))
        )
        row = (await self.db.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        return json.loads(row.decision_json)
