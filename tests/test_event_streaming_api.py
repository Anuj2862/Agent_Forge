"""
API Integration Tests for Real-Time Execution Streaming (Phase 7).
Tests SSE endpoints, 404 handling, historical replay, sequence resumption, and async starter.
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.memory.database import AsyncSessionFactory
from app.memory.repository import DatabaseRepository
from app.memory.models import ExecutionRecordORM, ExecutionEventORM
from app.schemas.execution_event import ExecutionEvent, ExecutionEventType, ExecutionStage


@pytest.mark.asyncio
async def test_stream_unknown_execution_returns_404():
    """Verify that requesting events for a nonexistent execution returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/execution/nonexistent_exec_12345/events")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stream_historical_events_and_resume():
    """Verify SSE streaming, proper wire format, and sequence-based resumption."""
    import uuid
    suffix = uuid.uuid4().hex[:8]
    exec_id = f"exec_sse_{suffix}"
    task_id = f"task_sse_{suffix}"

    async with AsyncSessionFactory() as db:
        repo = DatabaseRepository(db)
        # Create execution record
        exec_orm = ExecutionRecordORM(
            execution_id=exec_id,
            task_id=task_id,
            architecture_id="arch_sse",
            run_number=1,
            status="completed",
            duration_seconds=1.2,
            execution_result_json='{"status": "completed"}',
        )
        db.add(exec_orm)
        await db.flush()

        # Add 3 sequential events
        await repo.save_execution_event(
            ExecutionEvent(
                event_id=f"evt_s1_{suffix}",
                execution_id=exec_id,
                task_id=task_id,
                sequence_number=1,
                event_type=ExecutionEventType.EXECUTION_STARTED,
                message="Pipeline started",
            )
        )
        await repo.save_execution_event(
            ExecutionEvent(
                event_id=f"evt_s2_{suffix}",
                execution_id=exec_id,
                task_id=task_id,
                sequence_number=2,
                event_type=ExecutionEventType.AGENT_STARTED,
                agent_id="agent_1",
                message="Agent 1 active",
            )
        )
        await repo.save_execution_event(
            ExecutionEvent(
                event_id=f"evt_s3_{suffix}",
                execution_id=exec_id,
                task_id=task_id,
                sequence_number=3,
                event_type=ExecutionEventType.EXECUTION_COMPLETED,
                message="Pipeline done",
                status="completed",
            )
        )
        await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Full stream from beginning
        resp = await client.get(f"/execution/{exec_id}/events")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        body = resp.text
        assert "id: 1\n" in body
        assert "event: execution.started\n" in body
        assert "id: 2\n" in body
        assert "event: agent.started\n" in body
        assert "id: 3\n" in body
        assert "event: execution.completed\n" in body

        # 2. Resume with ?after_seq=2 (should only receive event 3)
        resume_resp = await client.get(f"/execution/{exec_id}/events?after_seq=2")
        assert resume_resp.status_code == 200
        resume_body = resume_resp.text
        assert "id: 1\n" not in resume_body
        assert "id: 2\n" not in resume_body
        assert "id: 3\n" in resume_body
        assert "event: execution.completed\n" in resume_body

        # 3. Resume with Last-Event-ID header
        header_resp = await client.get(
            f"/execution/{exec_id}/events",
            headers={"Last-Event-ID": "2"},
        )
        assert header_resp.status_code == 200
        header_body = header_resp.text
        assert "id: 1\n" not in header_body
        assert "id: 2\n" not in header_body
        assert "id: 3\n" in header_body

        # 4. JSON event history endpoint check
        json_resp = await client.get(f"/execution/{exec_id}/events/history")
        assert json_resp.status_code == 200
        data = json_resp.json()
        assert data["execution_id"] == exec_id
        assert data["count"] == 3
        assert data["events"][0]["sequence_number"] == 1



@pytest.mark.asyncio
async def test_start_execution_async_and_event_stream():
    """Verify POST /execution/start asynchronously queues execution and produces events."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit a task first
        sub_resp = await client.post(
            "/tasks/submit",
            json={
                "user_prompt": "Analyze market trends and calculate portfolio beta",
                "max_agents": 2,
            },
        )
        assert sub_resp.status_code == 200
        task_id = sub_resp.json()["task_id"]

        # Call /execution/start
        start_resp = await client.post(
            "/execution/start",
            json={"task_id": task_id, "run_number": 1, "use_real_engine": False},
        )
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        assert "execution_id" in start_data
        assert start_data["status"] == "running"
        assert "stream_url" in start_data

        exec_id = start_data["execution_id"]

        # Wait briefly for background execution to complete
        await asyncio.sleep(0.5)

        # Check events history
        events_resp = await client.get(f"/execution/{exec_id}/events/history")
        assert events_resp.status_code == 200
        ev_data = events_resp.json()
        assert ev_data["count"] > 0
        event_types = [e["event_type"] for e in ev_data["events"]]
        assert "execution.queued" in event_types
        assert "execution.started" in event_types
        assert "execution.completed" in event_types
