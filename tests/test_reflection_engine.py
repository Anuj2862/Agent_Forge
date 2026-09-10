"""
Unit Tests for ReflectionEngine and ImprovementGenerator.
"""

from app.reflection.reflection_engine import ReflectionEngine
from app.reflection.improvement_generator import ImprovementGenerator
from app.evaluation.evaluator import Evaluator
from app.schemas.reflection import IssueCategory, ReflectionResult, ReflectionIssue, ArchitecturalRecommendation
from tests.fixtures.mock_scenarios import (
    get_research_task_spec,
    get_run1_architecture,
    get_run1_execution_result,
)


def test_improvement_generator_missing_verification():
    generator = ImprovementGenerator()
    arch = get_run1_architecture()

    issue = ReflectionIssue(
        category=IssueCategory.INSUFFICIENT_VERIFICATION,
        description="Lacks verification stage",
        severity="high",
        affected_component="architecture",
    )

    recs = generator.generate_recommendations([issue], arch)
    assert len(recs) >= 1

    rec = recs[0]
    assert rec.action == "ADD_AGENT"
    assert "verification" in rec.details["role"].lower()
    assert rec.details["insert_after"] == "research_agent"
    assert rec.details["insert_before"] == "writer_agent"
    assert rec.priority == "high"


def test_improvement_generator_missing_tool():
    generator = ImprovementGenerator()
    arch = get_run1_architecture()

    issue = ReflectionIssue(
        category=IssueCategory.MISSING_TOOL,
        description="Missing tool calculator",
        severity="high",
        affected_agent_id="research_agent",
        affected_component="tools",
    )
    recs = generator.generate_recommendations([issue], arch)
    assert len(recs) >= 1
    assert recs[0].action == "ADD_TOOL"
    assert recs[0].details["tool_name"] == "calculator"


def test_reflection_engine_full_flow():
    engine = ReflectionEngine()
    evaluator = Evaluator()
    task = get_research_task_spec()
    arch = get_run1_architecture()
    exec_res = get_run1_execution_result()

    eval_res = evaluator.evaluate(task, arch, exec_res)
    reflection = engine.reflect(
        evaluation_result=eval_res,
        architecture=arch,
        task=task,
        execution=exec_res,
    )

    assert isinstance(reflection, ReflectionResult)
    assert reflection.task_id == task.task_id
    assert reflection.architecture_id == arch.architecture_id
    assert len(reflection.identified_issues) >= 1
    assert len(reflection.recommendations) >= 1

    # Check 5-question summary answers
    summary = reflection.reflection_summary
    assert "deficiencies" in summary.lower() or "identified" in summary.lower()
    assert "architectural" in summary.lower() or "architecture" in summary.lower()
    assert "recommendation" in summary.lower() or "expected benefit" in summary.lower()
