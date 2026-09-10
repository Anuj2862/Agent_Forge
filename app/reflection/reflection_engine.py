"""
Reflection Engine Subsystem for Agent Forge.
Analyzes evaluation results and failure diagnoses to synthesize architectural reflections and evolution directives.
"""

import uuid
from typing import List, Optional
from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec
from app.schemas.execution import ExecutionResult
from app.schemas.evaluation import EvaluationResult
from app.schemas.reflection import ReflectionResult, ReflectionIssue, ArchitecturalRecommendation
from app.evaluation.failure_analyzer import FailureAnalyzer
from app.reflection.improvement_generator import ImprovementGenerator
from app.core.logging import logger


class ReflectionEngine:
    """Diagnoses architectural root causes and formulates structured evolution recommendations."""

    def __init__(
        self,
        failure_analyzer: Optional[FailureAnalyzer] = None,
        improvement_generator: Optional[ImprovementGenerator] = None,
    ):
        self.failure_analyzer = failure_analyzer or FailureAnalyzer()
        self.improvement_generator = improvement_generator or ImprovementGenerator()

    def reflect(
        self,
        evaluation_result: EvaluationResult,
        architecture: Optional[ArchitectureSpec] = None,
        task: Optional[TaskSpec] = None,
        execution: Optional[ExecutionResult] = None,
        diagnosed_issues: Optional[List[ReflectionIssue]] = None,
    ) -> ReflectionResult:
        """
        Main reflection entrypoint.
        Answers 5 key architectural questions:
        1. What went wrong?
        2. Why did it happen?
        3. Which architectural component is responsible?
        4. What should change?
        5. What expected benefit will the change provide?
        """
        task_id = evaluation_result.task_id
        arch_id = evaluation_result.architecture_id
        logger.info(f"[REFLECTION] Initiating reflection for task={task_id}, architecture={arch_id}")

        # 1. Obtain failure analysis issues
        if diagnosed_issues is None and architecture is not None and execution is not None:
            issues = self.failure_analyzer.diagnose(
                task_spec=task,
                architecture=architecture,
                execution_result=execution,
                evaluation_result=evaluation_result,
            )
        elif diagnosed_issues is not None:
            issues = diagnosed_issues
        else:
            # Fallback when execution/arch not provided directly
            issues = []
            if evaluation_result.metrics.verification_status in ("Unverified", "Failed Verification"):
                from app.schemas.reflection import IssueCategory
                issues.append(
                    ReflectionIssue(
                        category=IssueCategory.INSUFFICIENT_VERIFICATION,
                        description="Execution output lacked independent factual verification.",
                        severity="high",
                        evidence=f"Verification status: {evaluation_result.metrics.verification_status}",
                        affected_component="architecture",
                    )
                )

        # 2. Generate architectural recommendations
        recommendations = self.improvement_generator.generate_recommendations(
            issues=issues,
            architecture=architecture,
        )

        # 3. Synthesize comprehensive 5-point reflection summary
        reflection_summary = self._synthesize_reflection_summary(
            evaluation_result=evaluation_result,
            issues=issues,
            recommendations=recommendations,
        )

        reflection_id = f"refl_{uuid.uuid4().hex[:8]}"
        result = ReflectionResult(
            reflection_id=reflection_id,
            task_id=task_id,
            architecture_id=arch_id,
            identified_issues=issues,
            recommendations=recommendations,
            reflection_summary=reflection_summary,
        )

        logger.info(
            f"[REFLECTION] Completed reflection_id={reflection_id} | "
            f"{len(issues)} issues identified, {len(recommendations)} recommendations produced."
        )

        return result

    def _synthesize_reflection_summary(
        self,
        evaluation_result: EvaluationResult,
        issues: List[ReflectionIssue],
        recommendations: List[ArchitecturalRecommendation],
    ) -> str:
        """
        Constructs an answer to:
        1. What went wrong?
        2. Why did it happen?
        3. Which architectural component is responsible?
        4. What should change?
        5. What expected benefit will the change provide?
        """
        if not issues:
            return (
                f"Architecture achieved a satisfactory overall score of "
                f"{evaluation_result.overall_score or evaluation_result.metrics.task_success:.2f}. "
                f"No critical architectural vulnerabilities were identified."
            )

        # 1 & 2: What went wrong & Why did it happen?
        problem_descriptions = [f"{iss.description} (Evidence: {iss.evidence or 'observed in trace'})" for iss in issues]
        what_went_wrong = "Identified deficiencies: " + "; ".join(problem_descriptions)

        # 3: Responsible component
        components = sorted(list({iss.affected_component for iss in issues}))
        responsible_component = f"Responsible architectural layer(s): {', '.join(components)}."

        # 4 & 5: What should change & Expected benefit
        changes = []
        for rec in recommendations:
            changes.append(f"{rec.action}: {rec.reason} -> Expected Benefit: {rec.expected_benefit}")
        action_plan = "Evolution recommendations: " + "; ".join(changes) if changes else "No actions required."

        return f"{what_went_wrong} | {responsible_component} | {action_plan}"
