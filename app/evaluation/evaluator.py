"""
Evaluator Engine Subsystem for Agent Forge.
Evaluates multi-agent execution output, computes quantitative metrics, and generates explainable feedback summaries.
"""

import uuid
from typing import Dict, Any, Union, Optional
from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec
from app.schemas.execution import ExecutionResult, ExecutionStatus
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from app.evaluation.metrics import MetricsCalculator
from app.evaluation.quality_scorer import QualityScorer
from app.core.logging import logger


class Evaluator:
    """Evaluates agent execution quality, task success, verification, and resource utilization."""

    def __init__(
        self,
        metrics_calculator: Optional[MetricsCalculator] = None,
        quality_scorer: Optional[QualityScorer] = None,
    ):
        self.metrics_calculator = metrics_calculator or MetricsCalculator()
        self.quality_scorer = quality_scorer or QualityScorer()

    def evaluate(
        self,
        task: Union[TaskSpec, str],
        architecture: ArchitectureSpec,
        execution: Union[ExecutionResult, Dict[str, Any]],
    ) -> EvaluationResult:
        """
        Main evaluation entrypoint.
        Accepts TaskSpec (or task_id string), ArchitectureSpec, and ExecutionResult (or dict).
        Returns validated EvaluationResult.
        """
        # 1. Standardize TaskSpec
        if isinstance(task, str):
            task_id = task
            task_spec = None
            user_prompt = None
        else:
            task_id = task.task_id
            task_spec = task
            user_prompt = task.user_prompt

        # 2. Standardize ExecutionResult
        if isinstance(execution, dict):
            execution_result = self._convert_dict_to_execution_result(execution, task_id, architecture.architecture_id)
        else:
            execution_result = execution

        logger.info(f"[EVALUATION] Starting evaluation for task={task_id}, architecture={architecture.architecture_id}")

        # 3. Compute Textual Quality
        raw_output = execution_result.final_output or ""
        quality_score, quality_breakdown = self.quality_scorer.score_output(
            text=raw_output,
            user_prompt=user_prompt,
            context=str(task_spec.constraints) if task_spec else None,
        )

        # 4. Compute Comprehensive Metrics
        metrics, metric_breakdowns = self.metrics_calculator.compute_metrics(
            task_spec=task_spec,
            architecture=architecture,
            execution_result=execution_result,
            quality_score=quality_score,
        )

        # 5. Compute Composite Overall Score
        overall_score = self.quality_scorer.compute_overall_score(metrics)

        # 6. Synthesize Explanatory Feedback Summary
        feedback_summary = self._generate_feedback_summary(
            metrics=metrics,
            architecture=architecture,
            execution_result=execution_result,
            quality_breakdown=quality_breakdown,
        )

        eval_id = f"eval_{uuid.uuid4().hex[:8]}"

        result = EvaluationResult(
            evaluation_id=eval_id,
            task_id=task_id,
            architecture_id=architecture.architecture_id,
            metrics=metrics,
            feedback_summary=feedback_summary,
            raw_output=raw_output,
            overall_score=overall_score,
            breakdown={
                "quality_breakdown": quality_breakdown,
                **metric_breakdowns,
            },
        )

        logger.info(
            f"[EVALUATION] Completed eval_id={eval_id} | Overall score: {overall_score:.2f} "
            f"(Success: {metrics.task_success:.2f}, Quality: {metrics.quality:.2f}, "
            f"Accuracy: {metrics.accuracy:.2f}, Completeness: {metrics.completeness:.2f}, "
            f"Verification: {metrics.verification_status})"
        )

        return result

    def _convert_dict_to_execution_result(
        self, execution_dict: Dict[str, Any], task_id: str, arch_id: str
    ) -> ExecutionResult:
        """Adapts a raw dictionary into an ExecutionResult schema instance."""
        status_str = execution_dict.get("status", "success")
        try:
            status = ExecutionStatus(status_str)
        except Exception:
            status = ExecutionStatus.SUCCESS

        final_out = execution_dict.get("final_output") or execution_dict.get("output") or execution_dict.get("response") or ""
        step_outs = execution_dict.get("step_outputs") or execution_dict.get("steps") or {}
        time_sec = float(execution_dict.get("total_execution_time") or execution_dict.get("execution_time_seconds") or 0.0)
        tool_calls = int(execution_dict.get("total_tool_calls") or execution_dict.get("tool_call_count") or 0)
        errors = execution_dict.get("errors") or []
        traces = execution_dict.get("agent_traces") or []

        return ExecutionResult(
            execution_id=execution_dict.get("execution_id", f"exec_{uuid.uuid4().hex[:8]}"),
            task_id=task_id,
            architecture_id=arch_id,
            status=status,
            final_output=str(final_out) if final_out else None,
            step_outputs=step_outs if isinstance(step_outs, dict) else {},
            agent_traces=traces,
            total_execution_time=time_sec,
            iteration_count=int(execution_dict.get("iteration_count", 1)),
            total_tool_calls=tool_calls,
            errors=errors if isinstance(errors, list) else [str(errors)],
            metadata=execution_dict.get("metadata", {}),
        )

    def _generate_feedback_summary(
        self,
        metrics: EvaluationMetrics,
        architecture: ArchitectureSpec,
        execution_result: ExecutionResult,
        quality_breakdown: Dict[str, Any],
    ) -> str:
        """Constructs an explainable summary highlighting strengths and architectural deficiencies."""
        strengths = []
        deficiencies = []

        # Success analysis
        if metrics.task_success >= 0.8:
            strengths.append(f"Task executed successfully with robust output substance ({len(execution_result.final_output or '')} chars)")
        elif metrics.task_success < 0.6:
            deficiencies.append(f"Task encountered execution issues or brief output (status: {execution_result.status.value})")

        # Completeness analysis
        if metrics.completeness >= 0.8:
            strengths.append("High requirement and subtask coverage")
        elif metrics.completeness < 0.6:
            deficiencies.append("Multiple required subtasks or formatting specifications were unfulfilled")

        # Accuracy & Verification analysis
        if metrics.verification_status == "Verified":
            strengths.append("Output passed independent verification with corroborated claims")
        elif metrics.verification_status == "Unverified":
            deficiencies.append("Architecture lacked an independent verification stage; claims remain unverified")
        elif metrics.verification_status == "Failed Verification":
            deficiencies.append("Verification detected contradictions or uncorroborated assertions in output")

        # Quality analysis
        if metrics.quality >= 0.75:
            strengths.append("Clear structure and strong prompt relevance")
        elif metrics.quality < 0.55:
            deficiencies.append("Output suffered from low relevance, lack of structure, or superficial substance")

        # Resource efficiency analysis
        if metrics.cost_efficiency is not None and metrics.cost_efficiency < 0.5:
            deficiencies.append(f"Resource cost was disproportionate to quality ({metrics.agent_count} agents, {metrics.execution_time_seconds}s)")

        summary_parts = []
        if strengths:
            summary_parts.append("Strengths: " + "; ".join(strengths) + ".")
        if deficiencies:
            summary_parts.append("Deficiencies: " + "; ".join(deficiencies) + ".")
        if not summary_parts:
            summary_parts.append("Execution completed within acceptable parameters.")

        return " ".join(summary_parts)
