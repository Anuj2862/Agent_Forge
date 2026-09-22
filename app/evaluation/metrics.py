"""
Metrics Calculator for Agent Forge Evaluation Pipeline.
Computes deterministic and explainable metrics from TaskSpec, ArchitectureSpec, and ExecutionResult.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.task import TaskSpec, ComplexityLevel
from app.schemas.architecture import ArchitectureSpec
from app.schemas.execution import ExecutionResult, ExecutionStatus, AgentExecutionTrace
from app.schemas.evaluation import EvaluationMetrics
from app.core.logging import logger


class MetricsCalculator:
    """Computes explainable, deterministic metrics across performance dimensions."""

    # Benchmark execution times in seconds based on task complexity
    COMPLEXITY_TIME_BENCHMARKS = {
        ComplexityLevel.LOW: 5.0,
        ComplexityLevel.MEDIUM: 15.0,
        ComplexityLevel.HIGH: 30.0,
        ComplexityLevel.VERY_HIGH: 60.0,
    }

    def compute_metrics(
        self,
        task_spec: Optional[TaskSpec],
        architecture: ArchitectureSpec,
        execution_result: ExecutionResult,
        quality_score: float,
    ) -> Tuple[EvaluationMetrics, Dict[str, Any]]:
        """
        Compute full quantitative metrics payload and detailed calculation breakdown.
        """
        agent_count = max(len(architecture.agents), 1)
        tool_call_count = execution_result.total_tool_calls
        if tool_call_count == 0 and execution_result.agent_traces:
            tool_call_count = sum(len(trace.tool_calls) for trace in execution_result.agent_traces)

        execution_time = execution_result.total_execution_time
        if execution_time <= 0.0 and execution_result.agent_traces:
            execution_time = sum(trace.duration_seconds for trace in execution_result.agent_traces)

        # 1. Task Success
        task_success, success_breakdown = self.calculate_task_success(task_spec, execution_result)

        # 2. Completeness
        completeness, completeness_breakdown = self.calculate_completeness(task_spec, execution_result)

        # 3. Accuracy / Verification
        accuracy, verification_status, accuracy_breakdown = self.calculate_accuracy_verification(
            task_spec, architecture, execution_result
        )

        # 4. Tool Efficiency
        tool_efficiency, tool_breakdown = self.calculate_tool_efficiency(execution_result, tool_call_count)

        # 5. Cost vs Quality Efficiency
        cost_efficiency, cost_breakdown = self.calculate_cost_efficiency(
            quality_score=quality_score,
            agent_count=agent_count,
            execution_time=execution_time,
            task_spec=task_spec,
        )

        metrics = EvaluationMetrics(
            task_success=round(task_success, 4),
            quality=round(quality_score, 4),
            completeness=round(completeness, 4),
            execution_time_seconds=round(execution_time, 2),
            agent_count=agent_count,
            tool_call_count=tool_call_count,
            accuracy=round(accuracy, 4),
            verification_status=verification_status,
            tool_efficiency=round(tool_efficiency, 4),
            iteration_count=max(execution_result.iteration_count, 1),
            cost_efficiency=round(cost_efficiency, 4),
        )

        breakdown = {
            "task_success": success_breakdown,
            "completeness": completeness_breakdown,
            "accuracy": accuracy_breakdown,
            "tool_efficiency": tool_breakdown,
            "cost_efficiency": cost_breakdown,
        }

        return metrics, breakdown

    def calculate_task_success(
        self, task_spec: Optional[TaskSpec], execution_result: ExecutionResult
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluates task success using execution status, output presence, errors, and constraints.
        Score = 0.40 * status_score + 0.35 * output_substance + 0.25 * error_penalty_factor
        """
        # Status score
        if execution_result.status == ExecutionStatus.SUCCESS:
            status_score = 1.0
        elif execution_result.status == ExecutionStatus.PARTIAL:
            status_score = 0.5
        else:
            status_score = 0.0

        # Output substance
        output = execution_result.final_output or ""
        output_len = len(output.strip())
        if output_len > 250:
            output_substance = 1.0
        elif output_len > 50:
            output_substance = 0.6
        elif output_len > 0:
            output_substance = 0.2
        else:
            output_substance = 0.0

        # Error penalty
        error_count = len(execution_result.errors)
        failed_traces = sum(1 for t in execution_result.agent_traces if t.status == ExecutionStatus.FAILED)
        total_errors = error_count + failed_traces
        error_factor = max(0.0, 1.0 - (total_errors * 0.25))

        score = (0.40 * status_score) + (0.35 * output_substance) + (0.25 * error_factor)
        score = max(0.0, min(1.0, score))

        breakdown = {
            "status": execution_result.status.value,
            "status_score": status_score,
            "output_length": output_len,
            "output_substance": output_substance,
            "error_count": total_errors,
            "error_factor": error_factor,
            "score": round(score, 4),
        }
        return score, breakdown

    def calculate_completeness(
        self, task_spec: Optional[TaskSpec], execution_result: ExecutionResult
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Checks requirement coverage from TaskSpec: subtasks, expected format, step outputs.
        """
        if not task_spec or not task_spec.subtasks:
            # Fallback when subtasks are not decomposed
            if execution_result.final_output and len(execution_result.final_output.strip()) > 100:
                return 0.85, {"mode": "heuristic_fallback", "score": 0.85}
            return 0.5, {"mode": "heuristic_fallback", "score": 0.5}

        total_subtasks = len(task_spec.subtasks)
        fulfilled_count = 0
        output_text = (execution_result.final_output or "").lower()
        step_outputs = execution_result.step_outputs or {}

        # Look for evidence of each subtask in step outputs or final text
        for subtask in task_spec.subtasks:
            subtask_found = False
            title_terms = [w.lower() for w in subtask.title.split() if len(w) > 3]

            # Check in step_outputs keys or values
            for k, v in step_outputs.items():
                str_v = str(v).lower()
                if subtask.id.lower() in k.lower() or any(term in str_v for term in title_terms):
                    subtask_found = True
                    break

            # Check in traces
            if not subtask_found:
                for trace in execution_result.agent_traces:
                    trace_out = str(trace.output_data).lower()
                    if any(term in trace_out for term in title_terms):
                        subtask_found = True
                        break

            # Check in final output text
            if not subtask_found and title_terms:
                matches = sum(1 for term in title_terms if term in output_text)
                if matches >= max(1, len(title_terms) // 2):
                    subtask_found = True

            if subtask_found:
                fulfilled_count += 1

        subtask_ratio = fulfilled_count / total_subtasks if total_subtasks > 0 else 1.0

        # Format adherence
        format_adherence = 1.0
        if task_spec.expected_output_format:
            fmt = task_spec.expected_output_format.lower()
            if "report" in fmt or "markdown" in fmt:
                # Expect headers or bullet points
                if "#" in output_text or "- " in output_text or "* " in output_text:
                    format_adherence = 1.0
                else:
                    format_adherence = 0.6
            elif "json" in fmt:
                if "{" in output_text and "}" in output_text:
                    format_adherence = 1.0
                else:
                    format_adherence = 0.4

        score = (0.75 * subtask_ratio) + (0.25 * format_adherence)
        score = max(0.0, min(1.0, score))

        breakdown = {
            "total_subtasks": total_subtasks,
            "fulfilled_subtasks": fulfilled_count,
            "subtask_ratio": round(subtask_ratio, 4),
            "expected_format": task_spec.expected_output_format,
            "format_adherence": round(format_adherence, 4),
            "score": round(score, 4),
        }
        return score, breakdown

    def calculate_accuracy_verification(
        self,
        task_spec: Optional[TaskSpec],
        architecture: ArchitectureSpec,
        execution_result: ExecutionResult,
    ) -> Tuple[float, str, Dict[str, Any]]:
        """
        Determines accuracy and verification status:
        - Verified (high accuracy: 0.85 - 1.0)
        - Partially Verified (moderate accuracy: 0.60 - 0.75)
        - Unverified (neutral/cautionary: 0.40 - 0.55)
        - Failed Verification (low accuracy: 0.0 - 0.35)
        """
        # 1. Inspect architecture for verification agent presence
        verifier_agent_ids = [
            agent.agent_id
            for agent in architecture.agents
            if any(
                term in (agent.role + " " + agent.name + " " + agent.objective).lower()
                for term in ["verif", "fact_check", "validator", "critic", "cross_reference", "evaluat"]
            )
        ]
        has_verifier_in_arch = len(verifier_agent_ids) > 0

        # 2. Inspect execution traces for verification evidence
        verified_claims_count = 0
        unverified_claims_count = 0
        contradictions_count = 0
        verifier_executed = False

        for trace in execution_result.agent_traces:
            if trace.agent_id in verifier_agent_ids or any(
                term in (trace.role or "").lower() for term in ["verif", "fact", "valid"]
            ):
                verifier_executed = True

            if trace.verified_claims:
                verified_claims_count += len(trace.verified_claims)
            if trace.unverified_claims:
                unverified_claims_count += len(trace.unverified_claims)
            if trace.contradictions_found:
                contradictions_count += len(trace.contradictions_found)

            # Look for flags inside output_data dict
            out = trace.output_data
            if isinstance(out, dict):
                if out.get("verification_status") == "failed" or out.get("verified") is False:
                    contradictions_count += 1
                elif out.get("verification_status") in ("passed", "verified") or out.get("verified") is True:
                    verified_claims_count += 1

        # Check metadata or step outputs if agent_traces empty
        if not verifier_executed:
            for k, v in execution_result.step_outputs.items():
                if any(term in k.lower() for term in ["verif", "fact", "valid"]):
                    verifier_executed = True
                    if isinstance(v, dict):
                        if v.get("verified") is False or v.get("errors"):
                            contradictions_count += 1
                        else:
                            verified_claims_count += 1

        # 3. Categorize verification status and compute score
        if contradictions_count > 0:
            status = "Failed Verification"
            score = max(0.1, 0.4 - (contradictions_count * 0.15))
        elif verifier_executed and verified_claims_count > 0 and unverified_claims_count == 0:
            status = "Verified"
            score = 0.95
        elif verifier_executed and verified_claims_count > 0 and unverified_claims_count > 0:
            status = "Partially Verified"
            ratio = verified_claims_count / (verified_claims_count + unverified_claims_count)
            score = 0.60 + (0.25 * ratio)
        elif has_verifier_in_arch and not verifier_executed:
            status = "Unverified"
            score = 0.50
        elif not has_verifier_in_arch:
            # Architecture lacked verification stage
            status = "Unverified"
            # If task explicitly required verification, penalize heavily
            task_needs_verification = False
            if task_spec:
                task_text = (task_spec.user_prompt + " " + " ".join(task_spec.required_capabilities)).lower()
                task_needs_verification = any(term in task_text for term in ["verif", "factual", "accurate", "reliable"])
            score = 0.40 if task_needs_verification else 0.55
        else:
            status = "Unverified"
            score = 0.50

        breakdown = {
            "has_verifier_in_arch": has_verifier_in_arch,
            "verifier_agent_ids": verifier_agent_ids,
            "verifier_executed": verifier_executed,
            "verified_claims_count": verified_claims_count,
            "unverified_claims_count": unverified_claims_count,
            "contradictions_count": contradictions_count,
            "verification_status": status,
            "score": round(score, 4),
        }
        return score, status, breakdown

    def calculate_tool_efficiency(
        self, execution_result: ExecutionResult, tool_call_count: int
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Computes tool efficiency from invocation success rates and invocation necessity.
        """
        if tool_call_count == 0:
            # If no tools were called, neutral efficiency
            return 1.0, {"tool_call_count": 0, "successful_tool_calls": 0, "success_rate": 1.0, "score": 1.0}

        successful_calls = 0
        failed_calls = 0
        for trace in execution_result.agent_traces:
            for tool_record in trace.tool_calls:
                if tool_record.success:
                    successful_calls += 1
                else:
                    failed_calls += 1

        if successful_calls + failed_calls > 0:
            success_rate = successful_calls / (successful_calls + failed_calls)
        else:
            success_rate = 1.0

        # Frequency penalty if extreme redundant calls (> 20 for single prompt)
        redundancy_penalty = 0.0
        if tool_call_count > 20:
            redundancy_penalty = min(0.3, (tool_call_count - 20) * 0.015)

        score = max(0.0, min(1.0, success_rate - redundancy_penalty))
        breakdown = {
            "total_calls": tool_call_count,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": round(success_rate, 4),
            "redundancy_penalty": round(redundancy_penalty, 4),
            "score": round(score, 4),
        }
        return score, breakdown

    def calculate_cost_efficiency(
        self,
        quality_score: float,
        agent_count: int,
        execution_time: float,
        task_spec: Optional[TaskSpec],
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Evaluates Quality vs Resource Utilization.
        A larger architecture is not simply penalized; it is rewarded if quality is high.
        Efficiency = Quality / NormalizedCost.
        """
        complexity = task_spec.complexity if task_spec else ComplexityLevel.MEDIUM
        benchmark_time = self.COMPLEXITY_TIME_BENCHMARKS.get(complexity, 15.0)

        # Expected agents based on complexity
        expected_agents = {
            ComplexityLevel.LOW: 1,
            ComplexityLevel.MEDIUM: 3,
            ComplexityLevel.HIGH: 4,
            ComplexityLevel.VERY_HIGH: 6,
        }.get(complexity, 3)

        # Time ratio relative to benchmark
        time_ratio = max(0.5, execution_time / benchmark_time) if benchmark_time > 0 else 1.0
        # Agent ratio relative to expected
        agent_ratio = max(0.5, agent_count / expected_agents) if expected_agents > 0 else 1.0

        # Normalized cost factor (1.0 means expected resources consumed)
        resource_cost_factor = (0.5 * min(3.0, time_ratio)) + (0.5 * min(3.0, agent_ratio))

        # Quality vs Cost ratio
        # When quality is high (>0.8), higher resource cost is largely justified
        if quality_score >= 0.8:
            score = max(0.6, 1.0 - (0.15 * max(0.0, resource_cost_factor - 1.0)))
        else:
            # Low quality with high cost is heavily penalized
            score = max(0.1, quality_score / max(1.0, resource_cost_factor))

        score = max(0.0, min(1.0, score))

        breakdown = {
            "complexity": complexity.value if hasattr(complexity, "value") else str(complexity),
            "benchmark_time_seconds": benchmark_time,
            "actual_time_seconds": execution_time,
            "expected_agents": expected_agents,
            "actual_agents": agent_count,
            "resource_cost_factor": round(resource_cost_factor, 4),
            "score": round(score, 4),
        }
        return score, breakdown
