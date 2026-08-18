"""
Unit Tests for Shared Pydantic Data Contracts.
"""

from app.schemas.task import TaskSpec, TaskType, ComplexityLevel
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from app.schemas.reflection import ReflectionResult, ReflectionIssue, IssueCategory, ArchitecturalRecommendation


def test_task_spec_creation():
    task = TaskSpec(
        task_id="task_001",
        user_prompt="Research Generative AI",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.MEDIUM,
        required_capabilities=["research", "analysis"],
    )
    assert task.task_id == "task_001"
    assert task.task_type == TaskType.RESEARCH


def test_architecture_spec_creation():
    agent = AgentConfigSchema(
        agent_id="research_agent",
        name="Research Agent",
        role="Researcher",
        objective="Gather info",
        system_prompt="Research topic...",
        tools=["web_search"],
    )
    arch = ArchitectureSpec(
        architecture_id="arch_001",
        task_id="task_001",
        topology=TopologyType.PIPELINE,
        agents=[agent],
        connections=[],
    )
    assert arch.topology == TopologyType.PIPELINE
    assert len(arch.agents) == 1


def test_evaluation_result_creation():
    metrics = EvaluationMetrics(
        task_success=0.85,
        quality=0.80,
        completeness=0.90,
        execution_time_seconds=12.4,
        agent_count=3,
        tool_call_count=2,
    )
    eval_res = EvaluationResult(
        evaluation_id="eval_001",
        task_id="task_001",
        architecture_id="arch_001",
        metrics=metrics,
        feedback_summary="Good quality execution",
    )
    assert eval_res.metrics.task_success == 0.85


def test_reflection_result_creation():
    issue = ReflectionIssue(
        category=IssueCategory.INSUFFICIENT_VERIFICATION,
        description="Missing verification step",
    )
    rec = ArchitecturalRecommendation(
        action="ADD_AGENT",
        details={"role": "Verification Agent"},
        priority="high",
    )
    reflection = ReflectionResult(
        reflection_id="refl_001",
        task_id="task_001",
        architecture_id="arch_001",
        identified_issues=[issue],
        recommendations=[rec],
        reflection_summary="Add verification agent",
    )
    assert len(reflection.identified_issues) == 1
    assert len(reflection.recommendations) == 1
