"""
Verification Test for Backend Restart Persistence (Section 6 & 16 Audit).
Verifies that all entity states (Tasks, Architectures V1/V2, Executions, Evaluations,
Reflections, and Evolution Decisions) survive complete application process reboot.
"""

import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.memory.database import Base
from app.memory.repository import DatabaseRepository
from app.schemas.task import TaskSpec, TaskType, ComplexityLevel
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType
from app.schemas.execution import ExecutionResult, ExecutionStatus
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from app.schemas.reflection import ReflectionResult, ReflectionIssue, IssueCategory, ArchitecturalRecommendation
from app.evaluation.decision_policy import EvolutionDecisionPolicy, EvolutionDecision, DecisionStatus
from app.api.task_routes import _task_store
from app.api.execution_routes import _execution_store
from app.api.evaluation_routes import _evaluation_store


@pytest.mark.asyncio
async def test_restart_persistence_lifecycle(tmp_path):
    """
    Simulates full workflow persistence across server shutdown and reboot:
    1. Submit Task + Constraints
    2. Synthesize V1 Architecture
    3. Execute V1
    4. Evaluate V1
    5. Mutate to V2 Architecture
    6. Execute V2
    7. Evaluate V2
    8. Decide Evolution (ACCEPTED/REJECTED)
    9. Shutdown backend (close DB, wipe in-memory dicts)
    10. Reboot backend (open new DB connection)
    11. Validate all records, links, and metrics are intact.
    """
    db_file = tmp_path / "restart_test.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    import app.memory.models  # ensure models registered
    from app.memory.memory_store import EvolutionMemoryORM

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    task_id = f"task_{uuid.uuid4().hex[:8]}"
    v1_arch_id = f"arch_v1_{uuid.uuid4().hex[:6]}"
    v2_arch_id = f"arch_v2_{uuid.uuid4().hex[:6]}"
    exec1_id = f"exec_1_{uuid.uuid4().hex[:6]}"
    exec2_id = f"exec_2_{uuid.uuid4().hex[:6]}"
    eval1_id = f"eval_1_{uuid.uuid4().hex[:6]}"
    eval2_id = f"eval_2_{uuid.uuid4().hex[:6]}"
    refl1_id = f"refl_1_{uuid.uuid4().hex[:6]}"
    refl2_id = f"refl_2_{uuid.uuid4().hex[:6]}"

    # --- Session 1: Pre-restart execution pipeline ---
    async with async_session() as session:
        repo = DatabaseRepository(session)

        # 1. Task Spec
        task_spec = TaskSpec(
            task_id=task_id,
            user_prompt="Analyze quarterly logistics telemetry and optimize routing",
            task_type=TaskType.DATA_ANALYSIS,
            complexity=ComplexityLevel.MEDIUM,
            max_agents=3,
            allowed_tools=["python_tool"],
            forbidden_tools=["web_search"],
            require_verification=True,
        )

        # 2. V1 Architecture
        v1_agent = AgentConfigSchema(
            agent_id="agent_analyst",
            name="Analyst Agent",
            role="Data Analyst",
            objective="Analyze logistics CSVs",
            system_prompt="Analyze route data",
            tools=["python_tool"],
        )
        arch_v1 = ArchitectureSpec(
            architecture_id=v1_arch_id,
            task_id=task_id,
            topology=TopologyType.PIPELINE,
            agents=[v1_agent],
            connections=[],
            version="v1",
        )
        await repo.save_task(task_spec, arch_v1, run_number=1, status="architecture_ready")

        # 3. Execution 1
        exec1 = ExecutionResult(
            execution_id=exec1_id,
            task_id=task_id,
            architecture_id=v1_arch_id,
            status=ExecutionStatus.SUCCESS,
            total_steps=1,
            execution_time_seconds=1.2,
            agent_count=1,
            final_output="Analysis complete but unverified.",
        )
        await repo.save_execution(exec1, run_number=1)

        # 4. Evaluation 1
        eval1 = EvaluationResult(
            evaluation_id=eval1_id,
            task_id=task_id,
            architecture_id=v1_arch_id,
            metrics=EvaluationMetrics(
                task_success=0.6,
                quality=0.6,
                accuracy=0.5,
                completeness=0.8,
                verification=0.0,
                execution_time_seconds=1.2,
                agent_count=1,
            ),
            overall_score=0.55,
            feedback_summary="V1 logistics telemetry baseline evaluation",
        )
        refl1 = ReflectionResult(
            reflection_id=refl1_id,
            task_id=task_id,
            architecture_id=v1_arch_id,
            reflection_summary="Lacks verification agent",
            recommendations=[
                ArchitecturalRecommendation(
                    action="ADD_AGENT",
                    priority="high",
                    reason="Add verification agent for telemetry",
                    details={"role": "Verifier"},
                )
            ],
        )
        await repo.save_evaluation(eval1, refl1, run_number=1, execution_id=exec1_id)

        # 5. V2 Architecture Mutation
        v2_agent = AgentConfigSchema(
            agent_id="agent_verifier",
            name="Verifier Agent",
            role="Verifier",
            objective="Verify telemetry routes",
            system_prompt="Verify output facts",
            tools=["python_tool"],
        )
        arch_v2 = ArchitectureSpec(
            architecture_id=v2_arch_id,
            task_id=task_id,
            topology=TopologyType.PIPELINE,
            agents=[v1_agent, v2_agent],
            connections=[],
            version="v2",
            parent_architecture_id=v1_arch_id,
        )
        await repo.save_architecture(arch_v2, version="v2", parent_architecture_id=v1_arch_id)

        # 6. Execution 2
        exec2 = ExecutionResult(
            execution_id=exec2_id,
            task_id=task_id,
            architecture_id=v2_arch_id,
            status=ExecutionStatus.SUCCESS,
            total_steps=2,
            execution_time_seconds=1.8,
            agent_count=2,
            final_output="Verified optimal routing: saved 14% fuel.",
        )
        await repo.save_execution(exec2, run_number=2)

        # 7. Evaluation 2
        eval2 = EvaluationResult(
            evaluation_id=eval2_id,
            task_id=task_id,
            architecture_id=v2_arch_id,
            metrics=EvaluationMetrics(
                task_success=0.9,
                quality=0.92,
                accuracy=0.95,
                completeness=0.95,
                verification=1.0,
                execution_time_seconds=1.8,
                agent_count=2,
            ),
            overall_score=0.91,
            feedback_summary="V2 verified logistics evaluation",
        )
        refl2 = ReflectionResult(
            reflection_id=refl2_id,
            task_id=task_id,
            architecture_id=v2_arch_id,
            reflection_summary="Verified architecture performs well",
            recommendations=[],
        )
        await repo.save_evaluation(eval2, refl2, run_number=2, execution_id=exec2_id)

        # 8. Decision Policy
        decision = EvolutionDecisionPolicy.evaluate_evolution(
            v1_architecture=arch_v1,
            v2_architecture=arch_v2,
            v1_execution=exec1,
            v2_execution=exec2,
            v1_evaluation=eval1,
            v2_evaluation=eval2,
            task_spec=task_spec,
        )
        await repo.save_decision(decision)
        await session.commit()

    # --- SIMULATE PROCESS SHUTDOWN AND REBOOT ---
    await engine.dispose()
    _task_store.clear()
    _execution_store.clear()
    _evaluation_store.clear()

    # --- Session 2: After reboot, retrieve directly from persistent store ---
    reboot_engine = create_async_engine(db_url, echo=False)
    reboot_session_maker = async_sessionmaker(reboot_engine, class_=AsyncSession, expire_on_commit=False)

    async with reboot_session_maker() as session:
        repo = DatabaseRepository(session)
        recovered_task = await repo.get_task_composite(task_id)

        assert recovered_task is not None
        assert recovered_task["task_id"] == task_id
        assert recovered_task["user_prompt"] == "Analyze quarterly logistics telemetry and optimize routing"
        assert recovered_task["task_spec"]["max_agents"] == 3
        assert recovered_task["task_spec"]["forbidden_tools"] == ["web_search"]

        # Validate architecture versions
        versions = recovered_task["architecture_versions"]
        assert "v1" in versions
        assert "v2" in versions
        assert versions["v1"]["architecture_id"] == v1_arch_id
        assert versions["v2"]["architecture_id"] == v2_arch_id
        assert len(versions["v2"]["agents"]) == 2

        # Validate executions
        execs = recovered_task["executions"]
        assert len(execs) == 2
        assert execs[0]["execution_id"] == exec1_id
        assert execs[1]["execution_id"] == exec2_id

        # Validate evaluations
        evals = recovered_task["evaluations"]
        assert "run_1" in evals
        assert "run_2" in evals
        assert evals["run_1"]["evaluation_result"]["overall_score"] == 0.55
        assert evals["run_2"]["evaluation_result"]["overall_score"] == 0.91

        # Validate deterministic decision
        dec = recovered_task["evolution_decision"]
        assert dec is not None
        assert dec["status"] == "ACCEPTED"
        assert dec["v1_architecture_id"] == v1_arch_id
        assert dec["v2_architecture_id"] == v2_arch_id
        assert dec["score_delta"] > 0.3

    await reboot_engine.dispose()
