"""
In-Process Execution Event Broadcaster (Member 2 & 4).
Decoupled pub-sub broadcasting for real-time SSE streaming to web clients.
"""

import asyncio
import logging
from typing import AsyncGenerator, Dict, Set
from app.schemas.execution_event import ExecutionEvent

logger = logging.getLogger("agent_forge.streaming")


class ExecutionEventBroadcaster:
    """
    Manages in-memory live event distribution for active executions.
    Safe for multiple concurrent subscribers per execution.
    Bounded queues prevent memory bloat on slow or disconnected consumers.
    """

    def __init__(self, queue_maxsize: int = 200):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
        self._queue_maxsize = queue_maxsize

    async def publish(self, event: ExecutionEvent) -> None:
        """Broadcast an event to all active subscribers for the given execution."""
        execution_id = event.execution_id
        async with self._lock:
            queues = list(self._subscribers.get(execution_id, set()))

        for q in queues:
            try:
                if q.full():
                    # Evict oldest event if subscriber is lagging
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                q.put_nowait(event)
            except Exception as e:
                logger.debug(f"Failed to enqueue event for execution {execution_id}: {e}")

    async def subscribe(self, execution_id: str) -> AsyncGenerator[ExecutionEvent, None]:
        """Async generator yielding real-time events for an execution."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._queue_maxsize)
        async with self._lock:
            if execution_id not in self._subscribers:
                self._subscribers[execution_id] = set()
            self._subscribers[execution_id].add(queue)

        try:
            while True:
                event = await queue.get()
                yield event
                queue.task_done()
                # If terminal event, stop streaming
                if event.event_type.value in (
                    "execution.completed",
                    "execution.failed",
                    "execution.cancelled",
                ):
                    break
        finally:
            async with self._lock:
                if execution_id in self._subscribers:
                    self._subscribers[execution_id].discard(queue)
                    if not self._subscribers[execution_id]:
                        del self._subscribers[execution_id]

    async def active_subscriber_count(self, execution_id: str) -> int:
        """Return the number of active listeners for an execution."""
        async with self._lock:
            return len(self._subscribers.get(execution_id, set()))


# Global singleton instance for the FastAPI process
broadcaster = ExecutionEventBroadcaster()
