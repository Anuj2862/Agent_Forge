"""
Unit Tests for Shared Pydantic Data Contracts.
"""

from app.schemas.task import TaskSpec, TaskType, ComplexityLevel
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType
from app.schemas.execution import (
    ExecutionStatus,
    AgentStepLog,
    ExecutionState,
    ExecutionStateModel,
    ExecutionResult,
)
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


def test_agent_step_log_creation():
    step_log = AgentStepLog(
        step_id="step_001",
        agent_id="research_agent",
        agent_role="Researcher",
        input_state={"prompt": "test prompt"},
        output_state={"result": "found data"},
        tool_calls=[{"tool": "web_search", "query": "test"}],
        status="completed",
        execution_time_seconds=1.5,
    )
    assert step_log.step_id == "step_001"
    assert step_log.agent_id == "research_agent"
    assert step_log.execution_time_seconds == 1.5
    assert len(step_log.tool_calls) == 1


def test_execution_state_creation():
    state: ExecutionState = {
        "task_id": "task_001",
        "user_prompt": "Research AI",
        "current_agent": "research_agent",
        "messages": [{"role": "user", "content": "Research AI"}],
        "agent_outputs": {"research_agent": "Done"},
        "step_history": [],
        "final_output": "AI research findings",
        "retry_count": 0,
        "metadata": {},
    }
    assert state["task_id"] == "task_001"
    assert state["current_agent"] == "research_agent"

    model = ExecutionStateModel(
        task_id="task_001",
        user_prompt="Research AI",
        current_agent="research_agent",
        final_output="AI research findings",
    )
    assert model.task_id == "task_001"
    assert model.current_agent == "research_agent"


def test_execution_result_creation_and_member3_compatibility():
    step_log = AgentStepLog(
        step_id="step_001",
        agent_id="research_agent",
        agent_role="Researcher",
        tool_calls=[{"tool": "web_search", "query": "test"}],
        status="completed",
        execution_time_seconds=2.0,
    )
    exec_result = ExecutionResult(
        execution_id="exec_001",
        task_id="task_001",
        architecture_id="arch_001",
        status=ExecutionStatus.SUCCESS,
        final_output="Final synthesized research output",
        step_history=[step_log],
        total_steps=1,
        execution_time_seconds=2.0,
        agent_count=1,
        tool_call_count=1,
    )

    assert exec_result.status == ExecutionStatus.SUCCESS
    assert exec_result.execution_time_seconds == 2.0

    # Test compatibility with Member 3 EvaluationMetrics & EvaluationResult
    metrics = EvaluationMetrics(
        task_success=1.0,
        quality=0.9,
        completeness=1.0,
        execution_time_seconds=exec_result.execution_time_seconds,
        agent_count=exec_result.agent_count,
        tool_call_count=exec_result.tool_call_count,
    )
    eval_res = EvaluationResult(
        evaluation_id="eval_001",
        task_id=exec_result.task_id,
        architecture_id=exec_result.architecture_id,
        metrics=metrics,
        feedback_summary="Excellent execution",
        raw_output=exec_result.final_output,
    )

    assert eval_res.metrics.execution_time_seconds == 2.0
    assert eval_res.metrics.agent_count == 1
    assert eval_res.metrics.tool_call_count == 1
    assert eval_res.raw_output == "Final synthesized research output"


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

