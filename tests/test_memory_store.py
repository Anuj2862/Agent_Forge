"""
Integration tests for MemoryStore — CRUD operations with SQLite in-memory DB.
"""

import asyncio
import pytest
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.memory.database import Base
from app.memory.memory_store import MemoryStore
from app.memory.memory_schema import EvolutionMemoryRecord
from app.schemas.task import TaskSpec, TaskType, ComplexityLevel, Subtask
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, Connection, TopologyType
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from app.schemas.reflection import ReflectionResult, ReflectionIssue, ArchitecturalRecommendation, IssueCategory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create an in-memory SQLite async session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()


def make_sample_record(record_id: str = "mem_test_001", run_number: int = 1) -> EvolutionMemoryRecord:
    """Build a minimal valid EvolutionMemoryRecord for testing."""
    task_spec = TaskSpec(
        task_id="task_test_001",
        user_prompt="Research AI safety in autonomous systems",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.MEDIUM,
        subtasks=[
            Subtask(id="s1", title="Search", description="Gather info", required_capabilities=["web_search"])
        ],
        required_capabilities=["web_search", "analysis"],
        constraints=["Be factual"],
        expected_output_format="markdown",
    )

    architecture_spec = ArchitectureSpec(
        architecture_id="arch_test_001",
        task_id="task_test_001",
        topology=TopologyType.PIPELINE,
        agents=[
            AgentConfigSchema(
                agent_id="agent_1",
                name="Search Agent",
                role="Researcher",
                objective="Gather info",
                system_prompt="You are a researcher.",
                tools=["web_search"],
                input_keys=["task_prompt"],
                output_keys=["raw_research"],
            )
        ],
        connections=[],
        meta_reasoning="Test architecture",
    )

    evaluation_result = EvaluationResult(
        evaluation_id="eval_test_001",
        task_id="task_test_001",
        architecture_id="arch_test_001",
        metrics=EvaluationMetrics(
            task_success=0.72,
            quality=0.68,
            completeness=0.75,
            execution_time_seconds=14.5,
            agent_count=1,
            tool_call_count=3,
        ),
        feedback_summary="Test evaluation feedback.",
        raw_output="Test output.",
    )

    reflection_result = ReflectionResult(
        reflection_id="refl_test_001",
        task_id="task_test_001",
        architecture_id="arch_test_001",
        identified_issues=[
            ReflectionIssue(
                category=IssueCategory.INSUFFICIENT_VERIFICATION,
                description="Missing verification stage",
            )
        ],
        recommendations=[
            ArchitecturalRecommendation(
                action="ADD_AGENT",
                details={"role": "Verification Agent"},
                priority="high",
            )
        ],
        reflection_summary="Add a verification agent.",
    )

    return EvolutionMemoryRecord(
        record_id=record_id,
        task_spec=task_spec,
        architecture_spec=architecture_spec,
        evaluation_result=evaluation_result,
        reflection_result=reflection_result,
        success_rating=0.71,
        run_number=run_number,
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.MEDIUM,
        timestamp=datetime.utcnow(),
        execution_duration_seconds=14.5,
        agent_count=1,
        topology="pipeline",
        recommendation_summary="ADD_AGENT: Add verification agent.",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_and_get_record(db_session):
    """Test saving and retrieving a single EvolutionMemoryRecord."""
    store = MemoryStore(db_session)
    record = make_sample_record("mem_001")

    saved_id = await store.save_record(record)
    assert saved_id == "mem_001"

    fetched = await store.get_record("mem_001")
    assert fetched is not None
    assert fetched.record_id == "mem_001"
    assert fetched.task_spec.task_id == "task_test_001"
    assert fetched.success_rating == pytest.approx(0.71)
    assert fetched.run_number == 1


@pytest.mark.asyncio
async def test_get_nonexistent_record(db_session):
    """Test that fetching a non-existent record returns None."""
    store = MemoryStore(db_session)
    result = await store.get_record("nonexistent_id")
    assert result is None


@pytest.mark.asyncio
async def test_list_records_empty(db_session):
    """Test listing records when database is empty."""
    store = MemoryStore(db_session)
    records = await store.list_records()
    assert records == []


@pytest.mark.asyncio
async def test_list_records_multiple(db_session):
    """Test listing multiple records."""
    store = MemoryStore(db_session)
    for i in range(5):
        await store.save_record(make_sample_record(f"mem_{i:03d}"))

    records = await store.list_records(limit=10)
    assert len(records) == 5


@pytest.mark.asyncio
async def test_list_records_pagination(db_session):
    """Test pagination of list_records."""
    store = MemoryStore(db_session)
    for i in range(6):
        await store.save_record(make_sample_record(f"mem_{i:03d}"))

    page1 = await store.list_records(limit=4, offset=0)
    page2 = await store.list_records(limit=4, offset=4)
    assert len(page1) == 4
    assert len(page2) == 2


@pytest.mark.asyncio
async def test_count_records(db_session):
    """Test counting records."""
    store = MemoryStore(db_session)
    assert await store.count_records() == 0

    await store.save_record(make_sample_record("mem_001"))
    await store.save_record(make_sample_record("mem_002"))
    assert await store.count_records() == 2


@pytest.mark.asyncio
async def test_delete_record(db_session):
    """Test deleting an existing record."""
    store = MemoryStore(db_session)
    await store.save_record(make_sample_record("mem_001"))

    deleted = await store.delete_record("mem_001")
    assert deleted is True

    fetched = await store.get_record("mem_001")
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_nonexistent_record(db_session):
    """Test deleting a record that does not exist returns False."""
    store = MemoryStore(db_session)
    deleted = await store.delete_record("does_not_exist")
    assert deleted is False


@pytest.mark.asyncio
async def test_get_records_for_task(db_session):
    """Test fetching all run records for a specific task_id."""
    store = MemoryStore(db_session)
    for run in range(1, 4):
        r = make_sample_record(f"mem_run_{run}", run_number=run)
        await store.save_record(r)

    records = await store.get_records_for_task("task_test_001")
    assert len(records) == 3
    assert [r.run_number for r in records] == [1, 2, 3]


@pytest.mark.asyncio
async def test_serialization_roundtrip(db_session):
    """Test that deeply nested Pydantic models survive serialization roundtrip."""
    store = MemoryStore(db_session)
    record = make_sample_record("mem_roundtrip")
    await store.save_record(record)

    fetched = await store.get_record("mem_roundtrip")
    assert fetched.architecture_spec.agents[0].agent_id == "agent_1"
    assert fetched.reflection_result.recommendations[0].action == "ADD_AGENT"
    assert fetched.evaluation_result.metrics.task_success == pytest.approx(0.72)
