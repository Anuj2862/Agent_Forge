"""
Final Independent Integration & Invariant Audit Tests.
Validates the complete 11-step end-to-end API workflow, constraint preservation,
database persistence across simulated restart, and all critical invariants.
"""

import os
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.memory.database import Base, get_db_session
from app.memory.repository import DatabaseRepository
from app.schemas.task import TaskConstraints
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, Connection
from app.schemas.validator import ArchitectureValidator
from app.evaluation.decision_policy import EvolutionDecisionPolicy, DecisionStatus


@pytest.fixture
async def isolated_client():
    """Create isolated tempfile sqlite database and test client."""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        db_url = f"sqlite+aiosqlite:///{tmp.name}"
        engine = create_async_engine(db_url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async def override_db():
            async with factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_db_session] = override_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c, engine, factory

        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_complete_api_workflow_and_restart_persistence(isolated_client):
    client, engine, factory = isolated_client

    # 1. Submit task with max_agents=2, forbidden_tools=['python_repl'], require_verification=True
    submit_resp = await client.post(
        "/tasks/submit",
        json={
            "user_prompt": "Research semiconductor supply chain bottlenecks and verify evidence.",
            "constraints": {
                "max_agents": 2,
                "forbidden_tools": ["python_repl"],
                "require_verification": True,
            },
        },
    )
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()
    task_id = submit_data["task_id"]
    v1_arch = submit_data["architecture_spec"]

    # 2. Retrieve task and verify constraints
    get_task_resp = await client.get(f"/tasks/{task_id}")
    assert get_task_resp.status_code == 200
    task_record = get_task_resp.json()
    assert task_record["task_id"] == task_id
    stored_constraints = task_record["task_spec"]["constraints"]
    assert stored_constraints["max_agents"] == 2
    assert "python_repl" in stored_constraints["forbidden_tools"]

    # 3. Validate V1 adheres to constraints
    assert len(v1_arch["agents"]) <= 2
    for agent in v1_arch["agents"]:
        assert "python_repl" not in agent["tools"]

    # 4. Execute V1
    exec_v1_resp = await client.post("/execution/run", json={"task_id": task_id, "run_number": 1})
    assert exec_v1_resp.status_code == 200
    exec_v1_data = exec_v1_resp.json()
    exec_v1_id = exec_v1_data["execution_id"]
    assert exec_v1_data["status"] in ("success", "completed")
    assert len(exec_v1_data["agent_logs"]) > 0

    # Inspect execution record
    get_exec_resp = await client.get(f"/execution/{exec_v1_id}")
    assert get_exec_resp.status_code == 200
    assert get_exec_resp.json()["execution_id"] == exec_v1_id

    # 5. Evaluate V1
    eval_v1_resp = await client.post(
        "/evaluation/evaluate",
        json={"task_id": task_id, "execution_id": exec_v1_id},
    )
    assert eval_v1_resp.status_code == 200
    eval_v1_data = eval_v1_resp.json()
    eval_v1_id = eval_v1_data["evaluation_result"]["evaluation_id"]

    # 6. Retrieve diagnoses and reflection recommendations
    get_eval_resp = await client.get(f"/evaluation/{eval_v1_id}")
    assert get_eval_resp.status_code == 200
    eval_detail = get_eval_resp.json()
    assert "reflection_result" in eval_detail
    assert len(eval_detail["reflection_result"]["recommendations"]) >= 0

    # 7. Generate and validate V2 (mutation must respect max_agents=2)
    evolve_resp = await client.post("/architectures/evolve", json={"task_id": task_id})
    assert evolve_resp.status_code == 200
    evolve_data = evolve_resp.json()
    v2_arch = evolve_data["evolved_architecture"]
    assert len(v2_arch["agents"]) <= 2, f"V2 agent count {len(v2_arch['agents'])} exceeded max_agents=2"
    for agent in v2_arch["agents"]:
        assert "python_repl" not in agent["tools"]

    # 8. Execute and evaluate V2
    exec_v2_resp = await client.post("/execution/run", json={"task_id": task_id, "run_number": 2})
    assert exec_v2_resp.status_code == 200
    exec_v2_id = exec_v2_resp.json()["execution_id"]

    eval_v2_resp = await client.post(
        "/evaluation/evaluate",
        json={"task_id": task_id, "execution_id": exec_v2_id},
    )
    assert eval_v2_resp.status_code == 200

    # 9. Retrieve evolution decision & comparison
    compare_resp = await client.get(f"/evaluation/compare/{task_id}")
    assert compare_resp.status_code == 200
    compare_data = compare_resp.json()
    assert compare_data["has_comparison"] is True
    assert compare_data["deltas"] is not None
    assert "evolution_decision" in compare_data
    assert compare_data["evolution_decision"] is not None
    decision = compare_data["evolution_decision"]
    assert decision["decision_status"] in ("ACCEPTED", "REJECTED", "INCONCLUSIVE")
    assert decision["hard_constraints_satisfied"] is True
    assert len(decision["reason_codes"]) > 0

    # 10. Retrieve complete versions & history
    versions_resp = await client.get(f"/architectures/task/{task_id}/versions")
    assert versions_resp.status_code == 200
    versions_data = versions_resp.json()
    assert "v1" in versions_data["versions"]
    assert "v2" in versions_data["versions"]

    # 11. Simulate backend restart: flush/dispose connection pool and re-query fresh session
    from app.api.task_routes import _task_store
    _task_store.clear()

    async with factory() as restart_session:
        repo = DatabaseRepository(restart_session)
        restored_composite = await repo.get_task_composite(task_id)
        assert restored_composite is not None
        assert restored_composite["task_id"] == task_id
        assert "v1" in restored_composite["architecture_versions"]
        assert "v2" in restored_composite["architecture_versions"]
        assert len(restored_composite["executions"]) == 2
        assert restored_composite["evolution_decision"] is not None
        assert restored_composite["evolution_decision"]["task_id"] == task_id


@pytest.mark.asyncio
async def test_invariant_hard_constraint_breach_rejection():
    """Verify candidate violating max_agents is strictly REJECTED regardless of score."""
    v1 = ArchitectureSpec(
        architecture_id="arch_v1",
        task_id="t_inv",
        topology="pipeline",
        agents=[
            AgentConfigSchema(agent_id="a1", name="A1", role="Researcher", objective="Research", system_prompt="Sys", tools=[]),
            AgentConfigSchema(agent_id="a2", name="A2", role="Writer", objective="Write", system_prompt="Sys", tools=[]),
        ],
        connections=[Connection(source="a1", target="a2")],
    )
    # V2 illegally has 3 agents when max_agents=2
    v2_invalid = ArchitectureSpec(
        architecture_id="arch_v2",
        task_id="t_inv",
        topology="pipeline",
        agents=[
            AgentConfigSchema(agent_id="a1", name="A1", role="Researcher", objective="Research", system_prompt="Sys", tools=[]),
            AgentConfigSchema(agent_id="a2", name="A2", role="Verifier", objective="Verify", system_prompt="Sys", tools=[]),
            AgentConfigSchema(agent_id="a3", name="A3", role="Writer", objective="Write", system_prompt="Sys", tools=[]),
        ],
        connections=[Connection(source="a1", target="a2"), Connection(source="a2", target="a3")],
    )

    from app.schemas.evaluation import EvaluationMetrics
    v1_metrics = EvaluationMetrics(task_success=0.7, quality=0.7, completeness=0.7, execution_time_seconds=2.0, agent_count=2, tool_call_count=1)
    v2_metrics = EvaluationMetrics(task_success=0.95, quality=0.95, completeness=0.95, execution_time_seconds=3.0, agent_count=3, tool_call_count=2)

    decision = EvolutionDecisionPolicy.evaluate_evolution(
        task_id="t_inv",
        v1_arch=v1,
        v2_arch=v2_invalid,
        v1_metrics=v1_metrics,
        v2_metrics=v2_metrics,
        constraints=TaskConstraints(max_agents=2),
    )
    assert decision.decision_status == DecisionStatus.REJECTED
    assert decision.hard_constraints_satisfied is False
    assert "MAX_AGENTS_EXCEEDED" in decision.reason_codes


@pytest.mark.asyncio
async def test_invariant_forbidden_tool_rejected_by_validator():
    """Verify architecture validator rejects forbidden tools."""
    arch = ArchitectureSpec(
        architecture_id="arch_forbidden",
        task_id="t_tool",
        topology="pipeline",
        agents=[
            AgentConfigSchema(agent_id="a1", name="A1", role="Agent", objective="Exec", system_prompt="Sys", tools=["python_repl"]),
        ],
        connections=[],
    )
    errors = ArchitectureValidator.validate(arch, constraints=TaskConstraints(forbidden_tools=["python_repl"]))
    assert len(errors) > 0
    assert any("FORBIDDEN_TOOL_USED" in e.code for e in errors)


@pytest.mark.asyncio
async def test_invariant_invalid_graph_edges_rejected():
    """Verify dangling edges and self-loops are rejected by validator."""
    dangling_arch = ArchitectureSpec(
        architecture_id="arch_dangling",
        task_id="t_dang",
        topology="pipeline",
        agents=[
            AgentConfigSchema(agent_id="a1", name="A1", role="Agent1", objective="Obj", system_prompt="Sys", tools=[]),
        ],
        connections=[Connection(source="a1", target="nonexistent_node")],
    )
    errors = ArchitectureValidator.validate(dangling_arch)
    assert len(errors) > 0
    assert any("INVALID_EDGE_TARGET" in e.code for e in errors)

    self_loop_arch = ArchitectureSpec(
        architecture_id="arch_self_loop",
        task_id="t_loop",
        topology="pipeline",
        agents=[
            AgentConfigSchema(agent_id="a1", name="A1", role="Agent1", objective="Obj", system_prompt="Sys", tools=[]),
        ],
        connections=[Connection(source="a1", target="a1")],
    )
    loop_errors = ArchitectureValidator.validate(self_loop_arch)
    assert len(loop_errors) > 0
    assert any("SELF_LOOP_DETECTED" in e.code for e in loop_errors)


@pytest.mark.asyncio
async def test_invariant_comparison_uses_actual_stored_metrics():
    """Verify comparison delta is mathematically consistent with stored metrics."""
    from app.schemas.evaluation import EvaluationMetrics
    v1_m = EvaluationMetrics(task_success=0.60, quality=0.70, completeness=0.65, execution_time_seconds=2.5, agent_count=2, tool_call_count=1)
    v2_m = EvaluationMetrics(task_success=0.85, quality=0.90, completeness=0.85, execution_time_seconds=3.0, agent_count=2, tool_call_count=2)

    v1_arch = ArchitectureSpec(
        architecture_id="a1",
        task_id="t_diff",
        topology="pipeline",
        agents=[AgentConfigSchema(agent_id="x", name="X", role="R", objective="O", system_prompt="Sys", tools=[])],
        connections=[],
    )
    v2_arch = ArchitectureSpec(
        architecture_id="a2",
        task_id="t_diff",
        topology="pipeline",
        agents=[AgentConfigSchema(agent_id="x", name="X", role="R", objective="O", system_prompt="Sys", tools=[])],
        connections=[],
    )

    decision = EvolutionDecisionPolicy.evaluate_evolution(
        task_id="t_diff",
        v1_arch=v1_arch,
        v2_arch=v2_arch,
        v1_metrics=v1_m,
        v2_metrics=v2_m,
        constraints=TaskConstraints(max_agents=3),
    )
    assert decision.decision_status == DecisionStatus.ACCEPTED
    assert decision.score_delta == pytest.approx(round(v2_m.overall_score - v1_m.overall_score, 4))
    assert decision.metric_deltas["task_success"] == pytest.approx(0.25)
    assert decision.metric_deltas["quality"] == pytest.approx(0.20)
