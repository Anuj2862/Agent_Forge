"""
Execution Event Emitter (Member 2 & 4).
Coordinates atomic sequence generation, durable DB persistence, and real-time pub-sub broadcasting.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
import uuid
from typing import Any, Callable, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
    ExecutionStage,
    sanitize_payload,
)
from app.execution.event_broadcaster import broadcaster

logger = logging.getLogger("agent_forge.streaming")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExecutionEventEmitter:
    """
    Convenience emitter bound to a specific execution and task.
    Ensures monotonic sequence numbering, database persistence, and SSE broadcast.
    """

    def __init__(
        self,
        execution_id: str,
        task_id: str,
        db: Optional[AsyncSession] = None,
        broadcaster_instance=broadcaster,
    ):
        self.execution_id = execution_id
        self.task_id = task_id
        self.db = db
        self.broadcaster = broadcaster_instance
        self._seq = 0
        self._lock = asyncio.Lock()

    async def init_sequence_from_db(self) -> None:
        """Initialize starting sequence number from database if events already exist."""
        if self.db:
            try:
                from app.memory.repository import DatabaseRepository
                repo = DatabaseRepository(self.db)
                self._seq = await repo.get_next_event_sequence(self.execution_id) - 1
            except Exception as e:
                logger.debug(f"Could not initialize sequence from DB for {self.execution_id}: {e}")

    async def emit(
        self,
        event_type: ExecutionEventType,
        message: str,
        stage: str = ExecutionStage.AGENT_EXECUTION.value,
        agent_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        status: str = "running",
    ) -> ExecutionEvent:
        """
        Create, persist, and broadcast an execution event.
        """
        async with self._lock:
            self._seq += 1
            seq = self._seq

        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        clean_data = sanitize_payload(data or {})

        event = ExecutionEvent(
            event_id=event_id,
            execution_id=self.execution_id,
            task_id=self.task_id,
            sequence_number=seq,
            event_type=event_type,
            timestamp=_utc_now(),
            status=status,
            agent_id=agent_id,
            stage=stage,
            message=message,
            data=clean_data,
            error=error,
        )

        # 1. Persist to database if session is present
        if self.db:
            try:
                from app.memory.models import ExecutionEventORM
                record = ExecutionEventORM(
                    event_id=event.event_id,
                    execution_id=event.execution_id,
                    task_id=event.task_id,
                    sequence_number=event.sequence_number,
                    event_type=event.event_type.value,
                    timestamp=event.timestamp,
                    status=event.status,
                    agent_id=event.agent_id,
                    stage=event.stage,
                    message=event.message,
                    data_json=json.dumps(event.data, default=str),
                    error=event.error,
                )
                self.db.add(record)
                await self.db.flush()
                await self.db.commit()
            except Exception as db_err:
                logger.warning(f"Failed to persist event {event.event_id} to DB: {db_err}")

        # 2. Publish to live SSE broadcaster
        try:
            await self.broadcaster.publish(event)
        except Exception as bc_err:
            logger.warning(f"Failed to broadcast event {event.event_id}: {bc_err}")

        return event

    def emit_sync(
        self,
        event_type: ExecutionEventType,
        message: str,
        stage: str = ExecutionStage.AGENT_EXECUTION.value,
        agent_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        status: str = "running",
    ) -> None:
        """
        Synchronous emission bridge for use inside synchronous LangGraph node runners.
        Schedules emission on the running asyncio event loop if active.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.emit(
                        event_type=event_type,
                        message=message,
                        stage=stage,
                        agent_id=agent_id,
                        data=data,
                        error=error,
                        status=status,
                    ),
                    loop,
                )
            else:
                loop.run_until_complete(
                    self.emit(
                        event_type=event_type,
                        message=message,
                        stage=stage,
                        agent_id=agent_id,
                        data=data,
                        error=error,
                        status=status,
                    )
                )
        except Exception as e:
            logger.debug(f"emit_sync failed for {event_type}: {e}")
