"""
Integration tests for MemoryRetriever — tiered similarity-based retrieval.
"""

import asyncio
import pytest
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.memory.database import Base
from app.memory.memory_store import MemoryStore
from app.memory.memory_retriever import MemoryRetriever
from app.memory.memory_schema import EvolutionMemoryRecord
from app.schemas.task import TaskSpec, TaskType, ComplexityLevel, Subtask
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from app.schemas.reflection import ReflectionResult


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def seeded_db():
    """DB pre-seeded with 6 records across different task types and complexities."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        store = MemoryStore(session)
        records = [
            _make_record("r1", TaskType.RESEARCH,       ComplexityLevel.MEDIUM, success=0.90),
            _make_record("r2", TaskType.RESEARCH,       ComplexityLevel.MEDIUM, success=0.75),
            _make_record("r3", TaskType.RESEARCH,       ComplexityLevel.HIGH,   success=0.80),
            _make_record("r4", TaskType.CODE_GENERATION,ComplexityLevel.MEDIUM, success=0.85),
            _make_record("r5", TaskType.DATA_ANALYSIS,  ComplexityLevel.LOW,    success=0.60),
            _make_record("r6", TaskType.GENERAL,        ComplexityLevel.MEDIUM, success=0.50),
        ]
        for rec in records:
            await store.save_record(rec)
        await session.commit()
        yield session

    await engine.dispose()


def _make_record(record_id: str, task_type: TaskType, complexity: ComplexityLevel, success: float) -> EvolutionMemoryRecord:
    task_spec = TaskSpec(
        task_id=f"task_{record_id}",
        user_prompt="Test prompt",
        task_type=task_type,
        complexity=complexity,
    )
    arch_spec = ArchitectureSpec(
        architecture_id=f"arch_{record_id}",
        task_id=f"task_{record_id}",
        topology=TopologyType.PIPELINE,
        agents=[AgentConfigSchema(
            agent_id="a1", name="Agent", role="Role",
            objective="Obj", system_prompt="Sys",
        )],
        connections=[],
    )
    eval_result = EvaluationResult(
        evaluation_id=f"eval_{record_id}",
        task_id=f"task_{record_id}",
        architecture_id=f"arch_{record_id}",
        metrics=EvaluationMetrics(
            task_success=success, quality=success, completeness=success,
            execution_time_seconds=10.0, agent_count=1, tool_call_count=0,
        ),
        feedback_summary="OK",
    )
    refl_result = ReflectionResult(
        reflection_id=f"refl_{record_id}",
        task_id=f"task_{record_id}",
        architecture_id=f"arch_{record_id}",
        identified_issues=[],
        recommendations=[],
        reflection_summary="All good.",
    )
    return EvolutionMemoryRecord(
        record_id=record_id,
        task_spec=task_spec,
        architecture_spec=arch_spec,
        evaluation_result=eval_result,
        reflection_result=refl_result,
        success_rating=success,
        run_number=1,
        task_type=task_type,
        complexity=complexity,
        timestamp=datetime.utcnow(),
        execution_duration_seconds=10.0,
        agent_count=1,
        topology="pipeline",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retrieve_exact_type_and_complexity(seeded_db):
    """Should return RESEARCH/MEDIUM records sorted by success rating DESC."""
    query_spec = TaskSpec(
        task_id="q1", user_prompt="Research query",
        task_type=TaskType.RESEARCH, complexity=ComplexityLevel.MEDIUM,
    )
    retriever = MemoryRetriever(seeded_db)
    results = await retriever.retrieve_similar_experiences(query_spec, limit=3)

    assert len(results) >= 1
    # Top result should be r1 (success=0.90) or r2 (success=0.75) — both RESEARCH/MEDIUM
    research_medium_ids = {"r1", "r2"}
    assert results[0].record_id in research_medium_ids
    # Results should be sorted by success_rating descending
    ratings = [r.success_rating for r in results]
    assert ratings == sorted(ratings, reverse=True)


@pytest.mark.asyncio
async def test_retrieve_falls_back_to_same_type(seeded_db):
    """When no records match complexity, should fall back to same task_type."""
    query_spec = TaskSpec(
        task_id="q2", user_prompt="Low complexity research",
        task_type=TaskType.RESEARCH, complexity=ComplexityLevel.LOW,  # no LOW records for RESEARCH
    )
    retriever = MemoryRetriever(seeded_db)
    results = await retriever.retrieve_similar_experiences(query_spec, limit=3)

    assert len(results) >= 1
    # All results should be RESEARCH type
    for r in results:
        assert r.task_type == TaskType.RESEARCH


@pytest.mark.asyncio
async def test_retrieve_falls_back_to_global(seeded_db):
    """When no records match task_type, should fall back to global best-rated."""
    query_spec = TaskSpec(
        task_id="q3", user_prompt="Problem solving query",
        task_type=TaskType.PROBLEM_SOLVING, complexity=ComplexityLevel.VERY_HIGH,
    )
    retriever = MemoryRetriever(seeded_db)
    results = await retriever.retrieve_similar_experiences(query_spec, limit=3)

    # Should still get results via global fallback
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_retrieve_respects_limit(seeded_db):
    """Should not return more results than limit."""
    query_spec = TaskSpec(
        task_id="q4", user_prompt="Any query",
        task_type=TaskType.RESEARCH, complexity=ComplexityLevel.MEDIUM,
    )
    retriever = MemoryRetriever(seeded_db)
    results = await retriever.retrieve_similar_experiences(query_spec, limit=1)
    assert len(results) <= 1


@pytest.mark.asyncio
async def test_get_best_architecture(seeded_db):
    """Should return the highest-rated record for exact type+complexity match."""
    retriever = MemoryRetriever(seeded_db)
    best = await retriever.get_best_architecture_for_task(
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.MEDIUM,
    )
    assert best is not None
    assert best.record_id == "r1"  # highest success_rating (0.90)
    assert best.task_type == TaskType.RESEARCH


@pytest.mark.asyncio
async def test_get_best_architecture_no_match(seeded_db):
    """Should return None when there are no records for the given profile."""
    retriever = MemoryRetriever(seeded_db)
    best = await retriever.get_best_architecture_for_task(
        task_type=TaskType.CONTENT_CREATION,
        complexity=ComplexityLevel.VERY_HIGH,
    )
    assert best is None


@pytest.mark.asyncio
async def test_get_evolution_history_for_task(seeded_db):
    """Should return all run records for a task ordered by run_number."""
    # Add 3 runs for the same task
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        store = MemoryStore(session)
        for run in [1, 2, 3]:
            r = _make_record(f"hist_{run}", TaskType.DATA_ANALYSIS, ComplexityLevel.LOW, success=0.5 + run * 0.1)
            r = r.model_copy(update={"run_number": run, "task_spec": r.task_spec.model_copy(update={"task_id": "shared_task"})})
            # Patch task_id in nested fields via re-creation
            from app.schemas.task import TaskSpec as TS
            r2 = EvolutionMemoryRecord(
                record_id=f"hist_{run}",
                task_spec=TS(task_id="shared_task", user_prompt="p", task_type=TaskType.DATA_ANALYSIS, complexity=ComplexityLevel.LOW),
                architecture_spec=r.architecture_spec,
                evaluation_result=r.evaluation_result,
                reflection_result=r.reflection_result,
                success_rating=r.success_rating,
                run_number=run,
                task_type=r.task_type,
                complexity=r.complexity,
                timestamp=datetime.utcnow(),
                execution_duration_seconds=10.0,
                agent_count=1,
                topology="pipeline",
            )
            await store.save_record(r2)
        await session.commit()

        retriever = MemoryRetriever(session)
        history = await retriever.get_evolution_history_for_task("shared_task")
        assert len(history) == 3
        assert [h.run_number for h in history] == [1, 2, 3]

    await engine.dispose()
