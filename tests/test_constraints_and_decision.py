"""
Unit Tests for Constraint-Aware Architecture Generation and Deterministic Evolution Decision Policy.
"""

import pytest
from app.controller.architecture_generator import ArchitectureGenerator
from app.schemas.task import TaskSpec, TaskType, ComplexityLevel, Subtask
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType
from app.schemas.execution import ExecutionResult, ExecutionStatus
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from app.evaluation.decision_policy import EvolutionDecisionPolicy, DecisionStatus


def test_architecture_generator_enforces_max_agents_by_clustering():
    """Verify that specifying max_agents=2 with 4 subtasks clusters into exactly 2 agents."""
    generator = ArchitectureGenerator()
    task_spec = TaskSpec(
        task_id="task_cluster_test",
        user_prompt="Run full 4-stage pipeline",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.HIGH,
        max_agents=2,
        subtasks=[
            Subtask(id="st_1", title="Gather Data", description="Gather raw data", required_capabilities=["web_search"]),
            Subtask(id="st_2", title="Extract Data", description="Extract entities", required_capabilities=["document_retriever"]),
            Subtask(id="st_3", title="Analyze Data", description="Analyze statistical trends", required_capabilities=["python_tool"]),
            Subtask(id="st_4", title="Draft Report", description="Write summary report", required_capabilities=["report_generator"]),
        ],
    )
    arch = generator.generate_architecture(task_spec)
    assert len(arch.agents) == 2
    assert arch.agents[0].agent_id.startswith("agent_merged") or arch.agents[0].agent_id == "st_1"


def test_architecture_generator_filters_forbidden_tools():
    """Verify that forbidden_tools are removed from assigned tools."""
    generator = ArchitectureGenerator()
    task_spec = TaskSpec(
        task_id="task_filter_tools",
        user_prompt="Perform offline calculation without internet",
        task_type=TaskType.DATA_ANALYSIS,
        forbidden_tools=["web_search"],
        allowed_tools=["python_tool"],
        subtasks=[
            Subtask(
                id="st_1",
                title="Compute",
                description="Run calculation",
                required_capabilities=["web_search", "python_tool"],
            )
        ],
    )
    arch = generator.generate_architecture(task_spec)
    assert "web_search" not in arch.agents[0].tools
    assert "python_tool" in arch.agents[0].tools


def test_decision_policy_rejects_candidate_violating_max_agents():
    """A candidate with higher score MUST be rejected if it violates max_agents."""
    task_spec = TaskSpec(
        task_id="task_dec_1",
        user_prompt="Strict 2-agent limit",
        max_agents=2,
    )
    arch_v1 = ArchitectureSpec(
        architecture_id="arch_v1",
        task_id="task_dec_1",
        topology=TopologyType.PIPELINE,
        agents=[
            AgentConfigSchema(agent_id="a1", name="Agent 1", role="Role 1", objective="Obj 1", system_prompt="Prompt 1"),
            AgentConfigSchema(agent_id="a2", name="Agent 2", role="Role 2", objective="Obj 2", system_prompt="Prompt 2"),
        ],
        connections=[],
    )
    # V2 has 3 agents (violates max_agents=2)
    arch_v2 = ArchitectureSpec(
        architecture_id="arch_v2",
        task_id="task_dec_1",
        topology=TopologyType.PIPELINE,
        agents=[
            AgentConfigSchema(agent_id="a1", name="Agent 1", role="Role 1", objective="Obj 1", system_prompt="Prompt 1"),
            AgentConfigSchema(agent_id="a2", name="Agent 2", role="Role 2", objective="Obj 2", system_prompt="Prompt 2"),
            AgentConfigSchema(agent_id="a3", name="Agent 3", role="Role 3", objective="Obj 3", system_prompt="Prompt 3"),
        ],
        connections=[],
    )
    eval_v1 = EvaluationResult(
        evaluation_id="eval_1",
        task_id="task_dec_1",
        architecture_id="arch_v1",
        metrics=EvaluationMetrics(
            task_success=0.6,
            quality=0.6,
            accuracy=0.6,
            completeness=0.6,
            execution_time_seconds=1.0,
            agent_count=2,
        ),
        overall_score=0.6,
        feedback_summary="V1 summary",
    )
    # V2 score is higher, but violates max_agents
    eval_v2 = EvaluationResult(
        evaluation_id="eval_2",
        task_id="task_dec_1",
        architecture_id="arch_v2",
        metrics=EvaluationMetrics(
            task_success=0.9,
            quality=0.9,
            accuracy=0.9,
            completeness=0.9,
            execution_time_seconds=1.2,
            agent_count=3,
        ),
        overall_score=0.9,
        feedback_summary="V2 summary",
    )
    decision = EvolutionDecisionPolicy.evaluate_evolution(
        v1_architecture=arch_v1,
        v2_architecture=arch_v2,
        v1_execution=None,
        v2_execution=None,
        v1_evaluation=eval_v1,
        v2_evaluation=eval_v2,
        task_spec=task_spec,
    )
    assert decision.status == DecisionStatus.REJECTED
    assert "MAX_AGENTS_EXCEEDED" in decision.reason_codes
    assert not decision.hard_constraints_satisfied


def test_decision_policy_accepts_valid_improved_candidate():
    """Valid candidate with score improvement >= 0.02 is ACCEPTED."""
    task_spec = TaskSpec(
        task_id="task_dec_accept",
        user_prompt="Improve summarization accuracy",
        max_agents=2,
    )
    arch_v1 = ArchitectureSpec(
        architecture_id="arch_v1",
        task_id="task_dec_accept",
        topology=TopologyType.PIPELINE,
        agents=[AgentConfigSchema(agent_id="a1", name="Agent 1", role="Writer", objective="Write", system_prompt="Prompt")],
        connections=[],
    )
    arch_v2 = ArchitectureSpec(
        architecture_id="arch_v2",
        task_id="task_dec_accept",
        topology=TopologyType.PIPELINE,
        agents=[
            AgentConfigSchema(agent_id="a1", name="Agent 1", role="Writer", objective="Write", system_prompt="Prompt"),
            AgentConfigSchema(agent_id="a2", name="Agent 2", role="Verifier", objective="Verify", system_prompt="Verify"),
        ],
        connections=[],
    )
    eval_v1 = EvaluationResult(
        evaluation_id="eval_1",
        task_id="task_dec_accept",
        architecture_id="arch_v1",
        metrics=EvaluationMetrics(
            task_success=0.6,
            quality=0.6,
            accuracy=0.5,
            completeness=0.7,
            execution_time_seconds=1.0,
            agent_count=1,
        ),
        overall_score=0.6,
        feedback_summary="V1 summary",
    )
    eval_v2 = EvaluationResult(
        evaluation_id="eval_2",
        task_id="task_dec_accept",
        architecture_id="arch_v2",
        metrics=EvaluationMetrics(
            task_success=0.85,
            quality=0.88,
            accuracy=0.9,
            completeness=0.9,
            execution_time_seconds=1.4,
            agent_count=2,
        ),
        overall_score=0.87,
        feedback_summary="V2 summary",
    )
    decision = EvolutionDecisionPolicy.evaluate_evolution(
        v1_architecture=arch_v1,
        v2_architecture=arch_v2,
        v1_execution=None,
        v2_execution=None,
        v1_evaluation=eval_v1,
        v2_evaluation=eval_v2,
        task_spec=task_spec,
    )
    assert decision.status == DecisionStatus.ACCEPTED
    assert "QUALITY_IMPROVEMENT" in decision.reason_codes
    assert decision.score_delta > 0.2
