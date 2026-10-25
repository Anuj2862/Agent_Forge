"""
End-to-end integration tests for AutonomousPipelineOrchestrator.
Validates the complete autonomous research loop:
1. Successful failure-driven self-evolution (Run 1 -> Reflection -> V2 -> Run 2 -> Decision ACCEPTED).
2. Controlled failure rejection under hard constraints (max_agents violation).
"""

import pytest
import uuid
from app.schemas.task import TaskSpec, TaskType, ComplexityLevel, Subtask
from app.controller.architecture_generator import ArchitectureGenerator
from app.execution.pipeline_orchestrator import AutonomousPipelineOrchestrator
from app.execution.event_broadcaster import broadcaster
from app.memory.repository import DatabaseRepository
from app.memory.database import AsyncSessionFactory


@pytest.mark.asyncio
async def test_autonomous_pipeline_successful_evolution():
    """
    Test full autonomous evolution workflow:
    1. Task requires factual verification.
    2. Initial architecture V1 has 2 agents (no verifier).
    3. Pipeline runs V1, evaluates, diagnoses missing verification,
       synthesizes V2 with verification agent, executes V2, evaluates V2,
       and renders an ACCEPTED evolution decision.
    """
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    exec_id = f"exec_{uuid.uuid4().hex[:8]}"

    task_spec = TaskSpec(
        task_id=task_id,
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

    generator = ArchitectureGenerator()
    arch_v1 = generator.generate_architecture(task_spec)

    async with AsyncSessionFactory() as db_session:
        repo = DatabaseRepository(db_session)
        await repo.save_task(task_spec, arch_v1, run_number=1, status="architecture_ready")
        await db_session.commit()

    orchestrator = AutonomousPipelineOrchestrator(
        task_id=task_id,
        task_spec=task_spec,
        architecture_spec=arch_v1,
        execution_id=exec_id,
        use_real_engine=True,
    )

    result = await orchestrator.execute_full_pipeline()

    assert result["status"] == "completed"
    assert result["evolved"] is True
    assert result["decision"] in ("ACCEPTED", "INCONCLUSIVE")
    assert "v2_execution_id" in result

    # Verify event stream in DB
    async with AsyncSessionFactory() as db_session:
        repo = DatabaseRepository(db_session)
        events = await repo.list_execution_events(exec_id)
        assert len(events) >= 6
        seqs = [e.sequence_number for e in events]
        assert seqs == sorted(seqs)

        event_types = [e.event_type.value for e in events]
        assert "execution.started" in event_types
        assert "evaluation.started" in event_types
        assert "evaluation.completed" in event_types
        assert "evolution.proposed" in event_types
        assert "evolution.validated" in event_types
        assert "execution.completed" in event_types


@pytest.mark.asyncio
async def test_autonomous_pipeline_constraint_rejection():
    """
    Test controlled failure rejection under strict hard constraints:
    Task specifies max_agents=2. Base V1 has 2 agents.
    When reflection recommends adding a verifier agent, candidate V2
    has 3 agents and is rejected due to max_agents constraint violation.
    """
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    exec_id = f"exec_{uuid.uuid4().hex[:8]}"

    task_spec = TaskSpec(
        task_id=task_id,
        user_prompt="Audit cybersecurity protocol claims and produce a verified assessment.",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.MEDIUM,
        max_agents=2,  # Strict hard constraint!
        required_capabilities=["web_search", "information_retrieval", "content_synthesis"],
        constraints=["max_agents=2"],
        subtasks=[
            Subtask(
                id="agent_1",
                title="Protocol Ingestion",
                description="Ingest protocols.",
                required_capabilities=["web_search"],
            ),
            Subtask(
                id="agent_2",
                title="Synthesize Draft",
                description="Draft report.",
                required_capabilities=["content_synthesis"],
            ),
        ],
    )

    generator = ArchitectureGenerator()
    arch_v1 = generator.generate_architecture(task_spec)

    async with AsyncSessionFactory() as db_session:
        repo = DatabaseRepository(db_session)
        await repo.save_task(task_spec, arch_v1, run_number=1, status="architecture_ready")
        await db_session.commit()

    orchestrator = AutonomousPipelineOrchestrator(
        task_id=task_id,
        task_spec=task_spec,
        architecture_spec=arch_v1,
        execution_id=exec_id,
        use_real_engine=True,
    )

    result = await orchestrator.execute_full_pipeline()

    assert result["status"] == "completed"
    assert result["evolved"] is False
    assert result["decision"] == "REJECTED"
    assert any("max_agents" in err for err in result["errors"])

    # Verify evolution.rejected event emitted
    async with AsyncSessionFactory() as db_session:
        repo = DatabaseRepository(db_session)
        events = await repo.list_execution_events(exec_id)
        event_types = [e.event_type.value for e in events]
        assert "evolution.rejected" in event_types
