"""
Unit Tests for FailureAnalyzer Subsystem.
"""

from app.evaluation.failure_analyzer import FailureAnalyzer
from app.evaluation.evaluator import Evaluator
from app.schemas.reflection import IssueCategory
from app.schemas.task import TaskSpec, ComplexityLevel
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType, Connection
from tests.fixtures.mock_scenarios import (
    get_research_task_spec,
    get_run1_architecture,
    get_run1_execution_result,
    get_failed_execution_result,
)


def test_diagnose_missing_verification():
    analyzer = FailureAnalyzer()
    evaluator = Evaluator()
    task = get_research_task_spec()
    arch = get_run1_architecture()
    exec_res = get_run1_execution_result()
    eval_res = evaluator.evaluate(task, arch, exec_res)

    issues = analyzer.diagnose(task, arch, exec_res, eval_res)

    categories = [i.category for i in issues]
    assert IssueCategory.INSUFFICIENT_VERIFICATION in categories

    verif_issue = next(i for i in issues if i.category == IssueCategory.INSUFFICIENT_VERIFICATION)
    assert verif_issue.severity == "high"
    assert "verification" in verif_issue.description.lower()
    assert verif_issue.affected_component == "architecture"


def test_diagnose_missing_tool():
    analyzer = FailureAnalyzer()
    evaluator = Evaluator()

    # Task requiring calculation
    task = TaskSpec(
        task_id="task_calc_001",
        user_prompt="Calculate mortgage amortization schedule",
        required_capabilities=["calculation"],
    )
    # Arch with no calculator
    arch = ArchitectureSpec(
        architecture_id="arch_no_calc",
        task_id="task_calc_001",
        agents=[
            AgentConfigSchema(
                agent_id="agent_1",
                name="Agent 1",
                role="Generalist",
                objective="Answer user",
                system_prompt="You are an assistant",
                tools=[],
            )
        ],
    )
    exec_res = get_run1_execution_result()
    eval_res = evaluator.evaluate(task, arch, exec_res)

    issues = analyzer.diagnose(task, arch, exec_res, eval_res)
    categories = [i.category for i in issues]
    assert IssueCategory.MISSING_TOOL in categories


def test_diagnose_redundant_agents():
    analyzer = FailureAnalyzer()
    evaluator = Evaluator()

    task = TaskSpec(
        task_id="task_simple",
        user_prompt="Say hello",
        complexity=ComplexityLevel.LOW,
    )
    # 5 agents for a low complexity task
    agents = [
        AgentConfigSchema(
            agent_id=f"agent_{i}",
            name=f"Agent {i}",
            role=f"Worker {i}",
            objective="Do small work",
            system_prompt="...",
            tools=[],
        )
        for i in range(5)
    ]
    arch = ArchitectureSpec(
        architecture_id="arch_bloated",
        task_id="task_simple",
        agents=agents,
        connections=[Connection(source=f"agent_{i}", target=f"agent_{i+1}") for i in range(4)],
    )
    exec_res = get_run1_execution_result()
    eval_res = evaluator.evaluate(task, arch, exec_res)

    issues = analyzer.diagnose(task, arch, exec_res, eval_res)
    categories = [i.category for i in issues]
    assert IssueCategory.REDUNDANT_AGENTS in categories


def test_diagnose_disconnected_topology():
    analyzer = FailureAnalyzer()
    evaluator = Evaluator()

    task = get_research_task_spec()
    arch = get_run1_architecture()
    # Add a disconnected third agent
    arch.agents.append(
        AgentConfigSchema(
            agent_id="island_agent",
            name="Island Agent",
            role="Observer",
            objective="Observe silently",
            system_prompt="...",
            tools=[],
        )
    )
    exec_res = get_run1_execution_result()
    eval_res = evaluator.evaluate(task, arch, exec_res)

    issues = analyzer.diagnose(task, arch, exec_res, eval_res)
    categories = [i.category for i in issues]
    assert IssueCategory.INCORRECT_TOPOLOGY in categories


def test_diagnose_agent_failure():
    analyzer = FailureAnalyzer()
    evaluator = Evaluator()

    task = get_research_task_spec()
    arch = get_run1_architecture()
    exec_res = get_failed_execution_result()
    eval_res = evaluator.evaluate(task, arch, exec_res)

    issues = analyzer.diagnose(task, arch, exec_res, eval_res)
    categories = [i.category for i in issues]
    assert IssueCategory.AGENT_REASONING_FAILURE in categories


def test_analyze_failures_backward_compatibility():
    analyzer = FailureAnalyzer()
    logs = [{"agent": "a1", "error": "TimeoutError"}, {"agent": "a2", "message": "Success"}]
    errors = analyzer.analyze_failures(logs)
    assert errors == ["TimeoutError"]
