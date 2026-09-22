"""
Unit Tests for Evaluator, MetricsCalculator, and QualityScorer.
"""

import pytest
from app.evaluation.evaluator import Evaluator
from app.evaluation.metrics import MetricsCalculator
from app.evaluation.quality_scorer import QualityScorer
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from tests.fixtures.mock_scenarios import (
    get_research_task_spec,
    get_run1_architecture,
    get_run1_execution_result,
    get_run2_execution_result,
    get_failed_execution_result,
)


def test_evaluator_run1_unverified():
    evaluator = Evaluator()
    task = get_research_task_spec()
    arch = get_run1_architecture()
    exec_res = get_run1_execution_result()

    result = evaluator.evaluate(task, arch, exec_res)

    assert isinstance(result, EvaluationResult)
    assert result.task_id == task.task_id
    assert result.architecture_id == arch.architecture_id
    assert result.metrics.task_success > 0.6
    assert result.metrics.verification_status == "Unverified"
    assert result.metrics.accuracy < 0.60
    assert result.overall_score is not None
    assert "Unverified" in result.feedback_summary or "unverified" in result.feedback_summary.lower()


def test_evaluator_run2_verified():
    evaluator = Evaluator()
    task = get_research_task_spec()
    # Evolved arch with 3 agents
    arch = get_run1_architecture()
    from app.schemas.architecture import AgentConfigSchema, Connection
    verifier = AgentConfigSchema(
        agent_id="fact_verification_agent",
        name="Fact Verification Agent",
        role="Factual Verification Specialist",
        objective="Verify factual claims",
        system_prompt="Verify claims against facts",
        tools=["web_search"],
    )
    arch.agents.append(verifier)
    arch.connections.append(Connection(source="research_agent", target="fact_verification_agent"))
    arch.connections.append(Connection(source="fact_verification_agent", target="writer_agent"))

    exec_res = get_run2_execution_result()
    result = evaluator.evaluate(task, arch, exec_res)

    assert result.metrics.verification_status == "Verified"
    assert result.metrics.accuracy >= 0.90
    assert result.metrics.quality > 0.70
    assert result.overall_score > 0.80
    assert "verification" in result.feedback_summary.lower()


def test_evaluator_failed_execution():
    evaluator = Evaluator()
    task = get_research_task_spec()
    arch = get_run1_architecture()
    exec_res = get_failed_execution_result()

    result = evaluator.evaluate(task, arch, exec_res)

    assert result.metrics.task_success < 0.35
    assert result.overall_score < 0.45
    assert "execution issues" in result.feedback_summary.lower() or "encountered" in result.feedback_summary.lower()


def test_evaluator_dict_input_compatibility():
    evaluator = Evaluator()
    arch = get_run1_architecture()

    # Pass plain string for task and plain dict for execution
    raw_dict = {
        "status": "success",
        "final_output": "Comprehensive analysis of cybersecurity threats with clear findings.",
        "total_execution_time": 4.5,
        "tool_call_count": 2,
    }
    result = evaluator.evaluate("task_plain_id", arch, raw_dict)

    assert isinstance(result, EvaluationResult)
    assert result.task_id == "task_plain_id"
    assert result.metrics.task_success > 0.5


def test_quality_scorer_heuristics():
    scorer = QualityScorer()
    sample_text = """# Cyber Security Analysis
## Key Findings
- Attack vectors have evolved significantly.
- Automated defenses are required.

## Conclusion
Organizations must adapt immediately.
"""
    score, breakdown = scorer.score_output(sample_text, user_prompt="Analyze cyber security threat vectors")
    assert 0.0 <= score <= 1.0
    assert breakdown["structure"] > 0.6
    assert breakdown["relevance"] > 0.6
    assert breakdown["clarity"] > 0.7


def test_quality_scorer_empty_text():
    scorer = QualityScorer()
    score, breakdown = scorer.score_output("")
    assert score == 0.0


def test_configurable_weights():
    custom_weights = {
        "task_success": 0.50,
        "quality": 0.20,
        "accuracy": 0.20,
        "completeness": 0.10,
    }
    scorer = QualityScorer(custom_weights=custom_weights)
    metrics = EvaluationMetrics(
        task_success=1.0,
        quality=0.5,
        completeness=0.5,
        execution_time_seconds=5.0,
        agent_count=2,
        accuracy=0.5,
    )
    score = scorer.compute_overall_score(metrics)
    # Expected base: 0.50*1.0 + 0.20*0.5 + 0.20*0.5 + 0.10*0.5 = 0.50 + 0.10 + 0.10 + 0.05 = 0.75
    assert 0.70 <= score <= 0.80
