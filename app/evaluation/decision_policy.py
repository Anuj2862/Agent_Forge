"""
Deterministic Evolution Decision Engine for Agent Forge.
Evaluates Candidate Architecture (V2) vs Base Architecture (V1) using:
- Hard-constraint validation (inviolable)
- Architecture graph validity
- Execution outcome status
- Multi-dimensional metric deltas & regression thresholds
- Resource & complexity trade-offs
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

from app.schemas.task import TaskSpec, TaskConstraints
from app.schemas.architecture import ArchitectureSpec
from app.schemas.execution import ExecutionResult, ExecutionStatus
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from app.schemas.validator import ArchitectureValidator, ValidationResult


class DecisionStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class EvolutionDecision(BaseModel):
    decision_id: str = Field(..., description="Unique decision ID")
    task_id: str
    status: DecisionStatus
    decision_status: Optional[DecisionStatus] = None
    v1_architecture_id: str
    v2_architecture_id: str
    v1_execution_id: Optional[str] = None
    v2_execution_id: Optional[str] = None
    v1_evaluation_id: Optional[str] = None
    v2_evaluation_id: Optional[str] = None
    v1_overall_score: float
    v2_overall_score: float
    score_delta: float
    metric_deltas: Dict[str, float] = Field(default_factory=dict)
    hard_constraints_satisfied: bool
    validation_errors: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    rationale: str
    decision_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policy_version: str = "1.0.0"

    def model_post_init(self, __context: Any) -> None:
        if self.decision_status is None:
            self.decision_status = self.status


class EvolutionDecisionPolicy:
    """
    Evaluates evidence from V1 and V2 runs to produce an evidence-based, explainable evolution decision.
    """

    MIN_ACCEPTANCE_DELTA: float = 0.02
    MATERIAL_REGRESSION_THRESHOLD: float = -0.05
    TASK_SUCCESS_REGRESSION_THRESHOLD: float = -0.10

    @classmethod
    def evaluate_evolution(
        cls,
        v1_architecture: Optional[ArchitectureSpec] = None,
        v2_architecture: Optional[ArchitectureSpec] = None,
        v1_execution: Any = None,
        v2_execution: Any = None,
        v1_evaluation: Optional[EvaluationResult] = None,
        v2_evaluation: Optional[EvaluationResult] = None,
        task_spec: Optional[TaskSpec] = None,
        decision_id: Optional[str] = None,
        # Flexible keyword aliases:
        task_id: Optional[str] = None,
        v1_arch: Optional[ArchitectureSpec] = None,
        v2_arch: Optional[ArchitectureSpec] = None,
        v1_metrics: Optional[EvaluationMetrics] = None,
        v2_metrics: Optional[EvaluationMetrics] = None,
        constraints: Optional[Union[TaskConstraints, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> EvolutionDecision:
        """Classmethod interface for evaluating evolution between V1 and V2."""
        v1_arch_eff = v1_architecture or v1_arch
        v2_arch_eff = v2_architecture or v2_arch

        if v1_arch_eff is None or v2_arch_eff is None:
            raise ValueError("Both v1_architecture and v2_architecture must be provided.")

        t_id = task_id or (getattr(task_spec, "task_id", None) or v1_arch_eff.task_id or "task_synth")

        if task_spec is None:
            t_constraints = constraints if isinstance(constraints, TaskConstraints) else (
                TaskConstraints(**constraints) if isinstance(constraints, dict) else TaskConstraints()
            )
            task_spec = TaskSpec(
                task_id=t_id,
                user_prompt="Task for evolution decision",
                constraints=t_constraints,
                max_agents=t_constraints.max_agents,
                forbidden_tools=t_constraints.forbidden_tools,
                allowed_tools=t_constraints.allowed_tools,
                require_verification=t_constraints.require_verification,
            )
        elif constraints:
            if isinstance(constraints, TaskConstraints):
                task_spec.constraints = constraints
                if constraints.max_agents is not None:
                    task_spec.max_agents = constraints.max_agents
                if constraints.forbidden_tools:
                    task_spec.forbidden_tools = constraints.forbidden_tools
            elif isinstance(constraints, dict):
                task_spec.max_agents = constraints.get("max_agents", task_spec.max_agents)
                task_spec.forbidden_tools = constraints.get("forbidden_tools", task_spec.forbidden_tools)

        if v1_evaluation is None:
            if v1_metrics is not None:
                v1_evaluation = EvaluationResult(
                    evaluation_id="eval_v1_synth",
                    architecture_id=v1_arch_eff.architecture_id,
                    execution_id=getattr(v1_execution, "execution_id", "exec_v1") if v1_execution else "exec_v1",
                    task_id=t_id,
                    metrics=v1_metrics,
                    overall_score=v1_metrics.overall_score,
                    feedback_summary="V1 synthetic evaluation result",
                )
            else:
                raise ValueError("Either v1_evaluation or v1_metrics must be provided.")

        if v2_evaluation is None:
            if v2_metrics is not None:
                v2_evaluation = EvaluationResult(
                    evaluation_id="eval_v2_synth",
                    architecture_id=v2_arch_eff.architecture_id,
                    execution_id=getattr(v2_execution, "execution_id", "exec_v2") if v2_execution else "exec_v2",
                    task_id=t_id,
                    metrics=v2_metrics,
                    overall_score=v2_metrics.overall_score,
                    feedback_summary="V2 synthetic evaluation result",
                )
            else:
                raise ValueError("Either v2_evaluation or v2_metrics must be provided.")

        policy = cls()
        exec1 = v1_execution if isinstance(v1_execution, ExecutionResult) else None
        exec2 = v2_execution if isinstance(v2_execution, ExecutionResult) else None
        return policy.evaluate(
            task_spec=task_spec,
            arch_v1=v1_arch_eff,
            arch_v2=v2_arch_eff,
            exec_v1=exec1,
            exec_v2=exec2,
            eval_v1=v1_evaluation,
            eval_v2=v2_evaluation,
            decision_id=decision_id,
        )

    def evaluate(
        self,
        task_spec: TaskSpec,
        arch_v1: ArchitectureSpec,
        arch_v2: ArchitectureSpec,
        exec_v1: Optional[ExecutionResult],
        exec_v2: Optional[ExecutionResult],
        eval_v1: EvaluationResult,
        eval_v2: EvaluationResult,
        decision_id: Optional[str] = None,
    ) -> EvolutionDecision:
        import uuid

        dec_id = decision_id or f"dec_{uuid.uuid4().hex[:10]}"
        reasons: List[str] = []
        validation_errors: List[str] = []

        m1 = eval_v1.metrics
        m2 = eval_v2.metrics

        s1 = eval_v1.overall_score if eval_v1.overall_score is not None else 0.5
        s2 = eval_v2.overall_score if eval_v2.overall_score is not None else 0.5
        score_delta = round(s2 - s1, 4)

        metric_deltas = {
            "overall_score": score_delta,
            "task_success": round((m2.task_success or 0) - (m1.task_success or 0), 4),
            "quality": round((m2.quality or 0) - (m1.quality or 0), 4),
            "accuracy": round(((m2.accuracy or 0) - (m1.accuracy or 0)), 4) if (m1.accuracy is not None and m2.accuracy is not None) else 0.0,
            "completeness": round((m2.completeness or 0) - (m1.completeness or 0), 4),
            "duration_seconds": round((m2.execution_time_seconds or 0) - (m1.execution_time_seconds or 0), 2),
            "agent_count": (m2.agent_count or 0) - (m1.agent_count or 0),
        }

        def _get_exec_id(ex: Any, fallback_eval: Any) -> Optional[str]:
            if ex is None:
                return getattr(fallback_eval, "execution_id", None)
            if isinstance(ex, dict):
                return ex.get("execution_id") or getattr(fallback_eval, "execution_id", None)
            return getattr(ex, "execution_id", None) or getattr(fallback_eval, "execution_id", None)

        v1_eid = _get_exec_id(exec_v1, eval_v1)
        v2_eid = _get_exec_id(exec_v2, eval_v2)

        # 1. HARD CONSTRAINT VALIDATION
        val_result: ValidationResult = ArchitectureValidator.validate(arch_v2, task_spec)
        if not val_result.is_valid:
            validation_errors = val_result.error_messages
            for err in val_result.errors:
                reasons.append(err.code)

            return EvolutionDecision(
                decision_id=dec_id,
                task_id=task_spec.task_id,
                status=DecisionStatus.REJECTED,
                v1_architecture_id=arch_v1.architecture_id,
                v2_architecture_id=arch_v2.architecture_id,
                v1_execution_id=v1_eid,
                v2_execution_id=v2_eid,
                v1_evaluation_id=eval_v1.evaluation_id,
                v2_evaluation_id=eval_v2.evaluation_id,
                v1_overall_score=s1,
                v2_overall_score=s2,
                score_delta=score_delta,
                metric_deltas=metric_deltas,
                hard_constraints_satisfied=False,
                validation_errors=validation_errors,
                reason_codes=reasons or ["HARD_CONSTRAINT_VIOLATION"],
                rationale=(
                    f"Candidate architecture V2 rejected due to constraint/integrity failure: "
                    f"{'; '.join(validation_errors)}"
                ),
            )

        # 2. CANDIDATE EXECUTION FAILURE CHECK
        if exec_v2 and getattr(exec_v2, "status", None) == ExecutionStatus.FAILED:
            return EvolutionDecision(
                decision_id=dec_id,
                task_id=task_spec.task_id,
                status=DecisionStatus.REJECTED,
                v1_architecture_id=arch_v1.architecture_id,
                v2_architecture_id=arch_v2.architecture_id,
                v1_execution_id=v1_eid,
                v2_execution_id=v2_eid,
                v1_evaluation_id=eval_v1.evaluation_id,
                v2_evaluation_id=eval_v2.evaluation_id,
                v1_overall_score=s1,
                v2_overall_score=s2,
                score_delta=score_delta,
                metric_deltas=metric_deltas,
                hard_constraints_satisfied=True,
                validation_errors=[],
                reason_codes=["CANDIDATE_EXECUTION_FAILED"],
                rationale=f"Candidate architecture V2 execution failed: {getattr(exec_v2, 'error', 'Runtime failure.')}",
            )

        # 3. CRITICAL REGRESSION CHECKS
        task_success_delta = metric_deltas["task_success"]
        if task_success_delta < self.TASK_SUCCESS_REGRESSION_THRESHOLD:
            return EvolutionDecision(
                decision_id=dec_id,
                task_id=task_spec.task_id,
                status=DecisionStatus.REJECTED,
                v1_architecture_id=arch_v1.architecture_id,
                v2_architecture_id=arch_v2.architecture_id,
                v1_execution_id=v1_eid,
                v2_execution_id=v2_eid,
                v1_evaluation_id=eval_v1.evaluation_id,
                v2_evaluation_id=eval_v2.evaluation_id,
                v1_overall_score=s1,
                v2_overall_score=s2,
                score_delta=score_delta,
                metric_deltas=metric_deltas,
                hard_constraints_satisfied=True,
                validation_errors=[],
                reason_codes=["TASK_SUCCESS_REGRESSION"],
                rationale=f"Task success regressed by {task_success_delta:.1%}, falling below acceptable boundary.",
            )

        if score_delta < self.MATERIAL_REGRESSION_THRESHOLD:
            return EvolutionDecision(
                decision_id=dec_id,
                task_id=task_spec.task_id,
                status=DecisionStatus.REJECTED,
                v1_architecture_id=arch_v1.architecture_id,
                v2_architecture_id=arch_v2.architecture_id,
                v1_execution_id=v1_eid,
                v2_execution_id=v2_eid,
                v1_evaluation_id=eval_v1.evaluation_id,
                v2_evaluation_id=eval_v2.evaluation_id,
                v1_overall_score=s1,
                v2_overall_score=s2,
                score_delta=score_delta,
                metric_deltas=metric_deltas,
                hard_constraints_satisfied=True,
                validation_errors=[],
                reason_codes=["MATERIAL_SCORE_REGRESSION"],
                rationale=f"Overall quality score regressed by {score_delta:.2%}.",
            )

        # 4. ACCEPTANCE CONDITIONS
        # A. Statistically/heuristically meaningful score improvement
        # B. Verification achieved (Unverified -> Verified) with non-negative score delta
        verification_improved = (
            m1.verification_status in ("Unverified", "Failed Verification")
            and m2.verification_status in ("Verified", "Partially Verified")
        )

        num_c = len(task_spec.constraints) if hasattr(task_spec.constraints, "__len__") else 0

        if score_delta >= self.MIN_ACCEPTANCE_DELTA:
            reasons.append("QUALITY_IMPROVEMENT")
            if verification_improved:
                reasons.append("VERIFICATION_STAGE_RESOLVED")

            return EvolutionDecision(
                decision_id=dec_id,
                task_id=task_spec.task_id,
                status=DecisionStatus.ACCEPTED,
                v1_architecture_id=arch_v1.architecture_id,
                v2_architecture_id=arch_v2.architecture_id,
                v1_execution_id=v1_eid,
                v2_execution_id=v2_eid,
                v1_evaluation_id=eval_v1.evaluation_id,
                v2_evaluation_id=eval_v2.evaluation_id,
                v1_overall_score=s1,
                v2_overall_score=s2,
                score_delta=score_delta,
                metric_deltas=metric_deltas,
                hard_constraints_satisfied=True,
                validation_errors=[],
                reason_codes=reasons,
                rationale=(
                    f"Candidate V2 accepted: achieved +{score_delta:.2%} overall score improvement "
                    f"while satisfying all {num_c} constraints."
                ),
            )

        if verification_improved and score_delta >= -0.01:
            return EvolutionDecision(
                decision_id=dec_id,
                task_id=task_spec.task_id,
                status=DecisionStatus.ACCEPTED,
                v1_architecture_id=arch_v1.architecture_id,
                v2_architecture_id=arch_v2.architecture_id,
                v1_execution_id=v1_eid,
                v2_execution_id=v2_eid,
                v1_evaluation_id=eval_v1.evaluation_id,
                v2_evaluation_id=eval_v2.evaluation_id,
                v1_overall_score=s1,
                v2_overall_score=s2,
                score_delta=score_delta,
                metric_deltas=metric_deltas,
                hard_constraints_satisfied=True,
                validation_errors=[],
                reason_codes=["VERIFICATION_STAGE_RESOLVED"],
                rationale="Candidate V2 accepted: successfully resolved unverified claims through factual verification.",
            )

        # 5. INCONCLUSIVE (Marginal or ambiguous improvement)
        return EvolutionDecision(
            decision_id=dec_id,
            task_id=task_spec.task_id,
            status=DecisionStatus.INCONCLUSIVE,
            v1_architecture_id=arch_v1.architecture_id,
            v2_architecture_id=arch_v2.architecture_id,
            v1_execution_id=v1_eid,
            v2_execution_id=v2_eid,
            v1_evaluation_id=eval_v1.evaluation_id,
            v2_evaluation_id=eval_v2.evaluation_id,
            v1_overall_score=s1,
            v2_overall_score=s2,
            score_delta=score_delta,
            metric_deltas=metric_deltas,
            hard_constraints_satisfied=True,
            validation_errors=[],
            reason_codes=["MARGINAL_SCORE_DELTA"],
            rationale=(
                f"Candidate V2 performance delta ({score_delta:+.2%}) does not meet the "
                f"+{self.MIN_ACCEPTANCE_DELTA:.2%} threshold for definitive acceptance."
            ),
        )
