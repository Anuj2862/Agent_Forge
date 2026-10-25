"""
Unit & Integration Tests for Execution Event Schema, Sanitization, and Persistence (Phase 7).
"""

import pytest
import asyncio
from datetime import datetime, timezone

from app.schemas.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
    ExecutionStage,
    sanitize_payload,
)
from app.execution.event_broadcaster import ExecutionEventBroadcaster
from app.memory.database import AsyncSessionFactory
from app.memory.repository import DatabaseRepository
from app.memory.models import ExecutionRecordORM


def test_sanitize_payload_redacts_secrets():
    """Verify that sensitive keys are recursively redacted."""
    raw = {
        "user_prompt": "Compute ROI",
        "api_key": "sk-secret12345",
        "nested": {
            "token": "bearer-token-abc",
            "GEMINI_API_KEY": "AIzaSyFakeKey",
            "safe_param": 42,
            "private_key": "-----BEGIN RSA-----",
        },
        "list_items": [
            {"password": "secretPassword"},
            {"role": "researcher"},
        ],
    }

    sanitized = sanitize_payload(raw)
    assert sanitized["user_prompt"] == "Compute ROI"
    assert sanitized["api_key"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["token"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["GEMINI_API_KEY"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["safe_param"] == 42
    assert sanitized["nested"]["private_key"] == "[REDACTED_SECRET]"
    assert sanitized["list_items"][0]["password"] == "[REDACTED_SECRET]"
    assert sanitized["list_items"][1]["role"] == "researcher"


def test_execution_event_model_and_sse_formatting():
    """Verify ExecutionEvent Pydantic model serialization and SSE wire formatting."""
    event = ExecutionEvent(
        event_id="evt_test001",
        execution_id="exec_test_01",
        task_id="task_test_01",
        sequence_number=1,
        event_type=ExecutionEventType.EXECUTION_STARTED,
        stage=ExecutionStage.SYNTHESIS.value,
        message="Execution started",
        data={"agent_count": 3},
    )

    sse_str = event.to_sse_message()
    assert "id: 1\n" in sse_str
    assert "event: execution.started\n" in sse_str
    assert "data: " in sse_str
    assert '"event_id": "evt_test001"' in sse_str
    assert sse_str.endswith("\n\n")


@pytest.mark.asyncio
async def test_event_broadcaster_pub_sub():
    """Verify in-process pub-sub broadcasting and clean disconnection."""
    bc = ExecutionEventBroadcaster(queue_maxsize=10)
    exec_id = "exec_bc_test"

    received_events = []

    async def _subscriber():
        async for ev in bc.subscribe(exec_id):
            received_events.append(ev)

    task = asyncio.create_task(_subscriber())
    await asyncio.sleep(0.01)

    ev1 = ExecutionEvent(
        event_id="evt_1",
        execution_id=exec_id,
        task_id="task_bc",
        sequence_number=1,
        event_type=ExecutionEventType.AGENT_STARTED,
        message="Agent started",
    )
    ev2 = ExecutionEvent(
        event_id="evt_2",
        execution_id=exec_id,
        task_id="task_bc",
        sequence_number=2,
        event_type=ExecutionEventType.EXECUTION_COMPLETED,
        message="Done",
        status="completed",
    )

    await bc.publish(ev1)
    await bc.publish(ev2)
    await task

    assert len(received_events) == 2
    assert received_events[0].event_id == "evt_1"
    assert received_events[1].event_id == "evt_2"
    assert await bc.active_subscriber_count(exec_id) == 0


@pytest.mark.asyncio
async def test_event_persistence_and_sequence_assignment():
    """Verify atomic monotonic sequence assignment and database persistence."""
    exec_id = "exec_persist_test"
    task_id = "task_persist_test"

    async with AsyncSessionFactory() as db:
        repo = DatabaseRepository(db)

        # Ensure parent execution record exists
        exec_orm = ExecutionRecordORM(
            execution_id=exec_id,
            task_id=task_id,
            architecture_id="arch_persist",
            run_number=1,
            status="running",
            duration_seconds=0.0,
            execution_result_json="{}",
        )
        db.add(exec_orm)
        await db.flush()

        # Save event with sequence 0 (should auto-assign 1)
        ev1 = ExecutionEvent(
            event_id="evt_p1",
            execution_id=exec_id,
            task_id=task_id,
            sequence_number=0,
            event_type=ExecutionEventType.EXECUTION_QUEUED,
            message="Queued",
        )
        saved1 = await repo.save_execution_event(ev1)
        assert saved1.sequence_number == 1

        # Save second event with sequence 0 (should auto-assign 2)
        ev2 = ExecutionEvent(
            event_id="evt_p2",
            execution_id=exec_id,
            task_id=task_id,
            sequence_number=0,
            event_type=ExecutionEventType.AGENT_STARTED,
            message="Agent running",
        )
        saved2 = await repo.save_execution_event(ev2)
        assert saved2.sequence_number == 2

        # Replay events
        all_events = await repo.list_execution_events(exec_id, after_seq=0)
        assert len(all_events) == 2
        assert all_events[0].sequence_number == 1
        assert all_events[1].sequence_number == 2

        # Replay with after_seq
        resumed = await repo.list_execution_events(exec_id, after_seq=1)
        assert len(resumed) == 1
        assert resumed[0].sequence_number == 2
        assert resumed[0].event_id == "evt_p2"

        # Rollback test changes
        await db.rollback()
