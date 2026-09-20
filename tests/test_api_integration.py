"""
E2E API integration tests using FastAPI TestClient.
Tests the full pipeline: submit task → run execution → evaluate → check memory.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.memory.database import Base, get_db_session


# ---------------------------------------------------------------------------
# Setup: Override DB with in-memory SQLite for tests
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="module")
async def client(test_engine):
    """FastAPI async test client with overridden in-memory DB."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

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
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_check(client):
    """Backend health check should return 200 healthy."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_submit_task(client):
    """POST /tasks/submit should return TaskSpec + ArchitectureSpec."""
    resp = await client.post("/tasks/submit", json={
        "user_prompt": "Research the impact of AI on healthcare"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert "task_spec" in data
    assert "architecture_spec" in data
    assert len(data["architecture_spec"]["agents"]) >= 1
    return data


@pytest.mark.asyncio
async def test_get_task(client):
    """GET /tasks/{task_id} should return the stored task."""
    # Submit first
    submit_resp = await client.post("/tasks/submit", json={
        "user_prompt": "Write a Python function to sort a list"
    })
    task_id = submit_resp.json()["task_id"]

    resp = await client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_spec"]["task_id"] == task_id


@pytest.mark.asyncio
async def test_get_task_not_found(client):
    """GET /tasks/nonexistent should return 404."""
    resp = await client.get("/tasks/nonexistent_task_id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_execution(client):
    """POST /execution/run should return execution results with agent logs."""
    # Submit first
    submit_resp = await client.post("/tasks/submit", json={
        "user_prompt": "Analyze sales data trends for Q4 2025"
    })
    task_id = submit_resp.json()["task_id"]

    resp = await client.post("/execution/run", json={"task_id": task_id, "run_number": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "agent_logs" in data
    assert len(data["agent_logs"]) >= 1
    assert "execution_id" in data
    assert "final_output" in data
    assert data["overall_success_rate"] > 0
    return data


@pytest.mark.asyncio
async def test_execute_nonexistent_task(client):
    """POST /execution/run with unknown task_id should return 404."""
    resp = await client.post("/execution/run", json={"task_id": "bad_task_id"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_full_e2e_pipeline(client):
    """
    Full E2E: submit → execute → evaluate → verify memory stored.
    Simulates the complete Mid-Sem demo flow.
    """
    # Step 1: Submit task
    submit_resp = await client.post("/tasks/submit", json={
        "user_prompt": "Create a content marketing strategy for a fintech startup"
    })
    assert submit_resp.status_code == 200
    task_id = submit_resp.json()["task_id"]

    # Step 2: Run execution
    exec_resp = await client.post("/execution/run", json={"task_id": task_id, "run_number": 1})
    assert exec_resp.status_code == 200
    execution_id = exec_resp.json()["execution_id"]

    # Step 3: Evaluate
    eval_resp = await client.post("/evaluation/evaluate", json={
        "execution_id": execution_id,
        "task_id": task_id,
    })
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert "evaluation_result" in eval_data
    assert "reflection_result" in eval_data
    assert "memory_record_id" in eval_data
    assert eval_data["success_rating"] >= 0

    # Step 4: Verify memory was stored
    memory_record_id = eval_data["memory_record_id"]
    mem_resp = await client.get(f"/memory/{memory_record_id}")
    assert mem_resp.status_code == 200
    mem_data = mem_resp.json()
    assert mem_data["record_id"] == memory_record_id
    assert mem_data["task_spec"]["task_id"] == task_id

    # Step 5: Check memory history
    history_resp = await client.get("/memory/history")
    assert history_resp.status_code == 200
    history_data = history_resp.json()
    assert history_data["total"] >= 1


@pytest.mark.asyncio
async def test_memory_status(client):
    """GET /memory/ should return operational status."""
    resp = await client.get("/memory/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"
    assert "total_records" in data


@pytest.mark.asyncio
async def test_task_type_detection():
    """Test that SimulatedMetaController detects task types correctly."""
    import asyncio
    from app.api.simulate import SimulatedMetaController
    from app.schemas.task import TaskType

    controller = SimulatedMetaController()

    ts, _ = await controller.process_task("Research the history of machine learning")
    assert ts.task_type == TaskType.RESEARCH

    ts2, _ = await controller.process_task("Write a Python script to parse CSV files")
    assert ts2.task_type == TaskType.CODE_GENERATION

    ts3, _ = await controller.process_task("Analyze sales data trends and correlations")
    assert ts3.task_type == TaskType.DATA_ANALYSIS
