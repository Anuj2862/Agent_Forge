"""
Execution Event Models and Taxonomy for Real-Time Streaming (Member 2 & 4).
Provides strongly typed execution event models, event taxonomy, and payload sanitization.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExecutionEventType(str, Enum):
    """Documented lifecycle event taxonomy for Agent Forge executions."""

    EXECUTION_QUEUED = "execution.queued"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_STAGE_STARTED = "execution.stage_started"
    AGENT_STARTED = "agent.started"
    AGENT_ACTION = "agent.action"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    AGENT_COMPLETED = "agent.completed"
    EXECUTION_STAGE_COMPLETED = "execution.stage_completed"
    EVALUATION_STARTED = "evaluation.started"
    EVALUATION_COMPLETED = "evaluation.completed"
    EVOLUTION_PROPOSED = "evolution.proposed"
    EVOLUTION_VALIDATED = "evolution.validated"
    EVOLUTION_ACCEPTED = "evolution.accepted"
    EVOLUTION_REJECTED = "evolution.rejected"
    EXECUTION_WARNING = "execution.warning"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_CANCELLED = "execution.cancelled"
    EXECUTION_COMPLETED = "execution.completed"


class ExecutionStage(str, Enum):
    """Lifecycle stages for an execution run."""

    SYNTHESIS = "synthesis"
    GRAPH_COMPILATION = "graph_compilation"
    AGENT_EXECUTION = "agent_execution"
    EVALUATION = "evaluation"
    REFLECTION = "reflection"
    EVOLUTION_DECISION = "evolution_decision"


SENSITIVE_KEY_PATTERN = re.compile(
    r"(api[-_]?key|secret|token|password|auth|credential|gemini[-_]?key|private[-_]?key|environ)",
    re.IGNORECASE,
)


def sanitize_payload(obj: Any, depth: int = 0) -> Any:
    """
    Recursively sanitize dictionaries and lists to prevent leaking
    sensitive API keys, tokens, credentials, or environment dumps.
    """
    if depth > 8:
        return "<max_depth_exceeded>"

    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            k_str = str(k)
            if SENSITIVE_KEY_PATTERN.search(k_str):
                sanitized[k_str] = "[REDACTED_SECRET]"
            else:
                sanitized[k_str] = sanitize_payload(v, depth + 1)
        return sanitized

    if isinstance(obj, (list, tuple, set)):
        return [sanitize_payload(item, depth + 1) for item in obj]

    if isinstance(obj, str):
        # Truncate exceptionally long raw outputs to protect bandwidth
        if len(obj) > 10000:
            return obj[:10000] + "… [truncated]"
        return obj

    return obj


class ExecutionEvent(BaseModel):
    """Strongly typed model for real-time and persisted execution events."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    event_id: str = Field(description="Unique event identifier (e.g. evt_<uuid>)")
    execution_id: str = Field(description="Associated execution identifier")
    task_id: str = Field(description="Associated task identifier")
    sequence_number: int = Field(description="Monotonically increasing sequence number (1-indexed)")
    event_type: ExecutionEventType = Field(description="Event category from the documented taxonomy")
    timestamp: datetime = Field(default_factory=_utc_now, description="UTC event timestamp")
    status: str = Field(default="running", description="Current execution status (queued, running, completed, failed, cancelled)")
    agent_id: Optional[str] = Field(default=None, description="Originating agent ID if applicable")
    stage: str = Field(default=ExecutionStage.AGENT_EXECUTION.value, description="Lifecycle execution stage")
    message: str = Field(description="Concise, human-readable description of this event")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured event-specific details")
    error: Optional[str] = Field(default=None, description="Sanitized error details when relevant")

    def to_sse_message(self) -> str:
        """Serialize event into standard Server-Sent Events (SSE) wire format."""
        import json
        payload = self.model_dump(mode="json")
        data_str = json.dumps(payload, default=str)
        return f"id: {self.sequence_number}\nevent: {self.event_type.value}\ndata: {data_str}\n\n"
