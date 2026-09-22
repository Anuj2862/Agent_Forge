"""
Autonomous Architecture Evolution Integration Test (Phase 8).
Verifies that real Evaluator, FailureAnalyzer, ReflectionEngine, and ArchitectureModifier
cooperate without manual or simulated recommendation injection.
"""

import pytest
import uuid
from app.schemas.task import TaskSpec, TaskType, ComplexityLevel, Subtask
from app.schemas.architecture import ArchitectureSpec, TopologyType
from app.schemas.execution import ExecutionResult, ExecutionStatus
from app.schemas.evaluation import EvaluationResult
from app.schemas.reflection import ReflectionResult
from app.controller.architecture_generator import ArchitectureGenerator
from app.agents.agent_factory import AgentFactory
from app.execution.execution_engine import ExecutionEngine
from app.tools.tool_registry import ToolRegistry
from app.tools import register_default_tools
from app.evaluation.evaluator import Evaluator
from app.evaluation.failure_analyzer import FailureAnalyzer
from app.reflection.reflection_engine import ReflectionEngine
from app.reflection.architecture_modifier import ArchitectureModifier


@pytest.mark.asyncio
async def test_real_reflection_triggers_architecture_evolution():
    """
    Deterministic autonomous evolution test (Phase 8):
    1. Construct a task requiring verification.
    2. Generate ArchitectureSpec (v1).
    3. Execute v1 via ExecutionEngine.
    4. Evaluate v1 via Evaluator.
    5. Run FailureAnalyzer on v1.
    6. Run ReflectionEngine to naturally produce recommendations without injection.
    7. Assert recommendation generated naturally.
    8. Apply recommendation via ArchitectureModifier.
    9. Assert ArchitectureSpec v2 differs structurally from v1.
    10. Validate v2.
    11. Execute v2 via ExecutionEngine.
    12. Evaluate v2 via Evaluator and verify corroboration / improvement.
    """
    # 1. Construct a task requiring factual verification
    task_spec = TaskSpec(
        task_id=f"task_{uuid.uuid4().hex[:8]}",
        user_prompt="Investigate electric vehicle battery safety claims, verify empirical statistics, and synthesize an evidence-backed report.",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.MEDIUM,
        required_capabilities=["web_search", "information_retrieval", "content_synthesis"],
        constraints=["Only cite verified statistics"],
        subtasks=[
            Subtask(
                id="researcher",
                title="EV Claims Retrieval",
                description="Gather published statistics and claims on electric vehicle battery safety.",
                required_capabilities=["web_search", "information_retrieval"],
            ),
            Subtask(
                id="reporter",
                title="Synthesize EV Report",
                description="Draft the summary report based on gathered claims.",
                required_capabilities=["content_synthesis"],
            ),
        ],
    )

    # 2. Generate initial architecture v1 (Member 1)
    generator = ArchitectureGenerator()
    arch_v1 = generator.generate_architecture(task_spec)

    assert isinstance(arch_v1, ArchitectureSpec)
    assert len(arch_v1.agents) == 2
    # Ensure no verifier agent exists initially
    assert not any("verif" in a.role.lower() or "verif" in a.agent_id.lower() for a in arch_v1.agents)

    # Setup execution environment (Member 2)
    registry = ToolRegistry()
    register_default_tools(registry)
    factory = AgentFactory(registry=registry)
    engine = ExecutionEngine(factory=factory)

    # 3. Execute v1 via LangGraph
    exec_v1 = await engine.execute_architecture(
        architecture=arch_v1,
        input_data={"user_prompt": task_spec.user_prompt},
    )
    assert isinstance(exec_v1, ExecutionResult)
    assert exec_v1.status in [ExecutionStatus.SUCCESS, "completed"]

    # 4. Evaluate v1 via Evaluator (Member 3)
    evaluator = Evaluator()
    eval_v1 = evaluator.evaluate(
        task=task_spec,
        architecture=arch_v1,
        execution=exec_v1,
    )
    assert isinstance(eval_v1, EvaluationResult)
    # Because there is no verification agent, verification_status should reflect lack of verification
    assert eval_v1.metrics.verification_status in ("Unverified", "Failed Verification")

    # 5. Run FailureAnalyzer & 6. Run ReflectionEngine (Member 3)
    failure_analyzer = FailureAnalyzer()
    reflection_engine = ReflectionEngine(failure_analyzer=failure_analyzer)

    reflection_v1 = reflection_engine.reflect(
        evaluation_result=eval_v1,
        architecture=arch_v1,
        task=task_spec,
        execution=exec_v1,
    )
    assert isinstance(reflection_v1, ReflectionResult)

    # 7. Assert that a recommendation is generated naturally (NO MANUAL INJECTION)
    assert len(reflection_v1.recommendations) >= 1, (
        f"ReflectionEngine must autonomously produce recommendations for unverified claims. "
        f"Diagnosed issues: {[i.category.value for i in reflection_v1.identified_issues]}"
    )
    top_rec = reflection_v1.recommendations[0]
    assert top_rec.action.upper() in ("ADD_AGENT", "ADD_VERIFICATION_STAGE")

    # 8. Apply recommendation via ArchitectureModifier (Member 3)
    modifier = ArchitectureModifier()
    arch_v2 = modifier.mutate_architecture(arch_v1, reflection_v1)

    # 9. Assert ArchitectureSpec v2 differs from v1
    assert isinstance(arch_v2, ArchitectureSpec)
    assert arch_v2.architecture_id != arch_v1.architecture_id
    assert len(arch_v2.agents) > len(arch_v1.agents)
    assert len(arch_v2.connections) > len(arch_v1.connections)

    # 10. Validate v2 structure (ensure newly added verification agent is present)
    verifier_present = any(
        "verif" in a.role.lower() or "fact" in a.role.lower() or "verif" in a.agent_id.lower()
        for a in arch_v2.agents
    )
    assert verifier_present, "Architecture v2 must contain the newly inserted verification specialist."

    # 11. Execute v2 via LangGraph ExecutionEngine
    exec_v2 = await engine.execute_architecture(
        architecture=arch_v2,
        input_data={"user_prompt": task_spec.user_prompt},
    )
    assert isinstance(exec_v2, ExecutionResult)
    assert exec_v2.status in [ExecutionStatus.SUCCESS, "completed"]

    # 12. Evaluate v2
    eval_v2 = evaluator.evaluate(
        task=task_spec,
        architecture=arch_v2,
        execution=exec_v2,
    )
    assert isinstance(eval_v2, EvaluationResult)
    # The factual accuracy and verification status in v2 should be improved
    assert eval_v2.metrics.accuracy >= eval_v1.metrics.accuracy
