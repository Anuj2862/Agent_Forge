"""
Shared Pydantic Data Contracts for Agent Forge.
"""

from app.schemas.task import TaskSpec, TaskType, ComplexityLevel, Subtask, TaskConstraints
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType, Connection
from app.schemas.execution import (
    ExecutionStatus,
    AgentStepLog,
    AgentExecutionTrace,
    ToolCallRecord,
    ExecutionState,
    ExecutionStateModel,
    ExecutionResult,
)
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from app.schemas.reflection import ReflectionResult, ReflectionIssue, IssueCategory, ArchitecturalRecommendation
from app.schemas.validator import ArchitectureValidator, ValidationResult, ValidationErrorDetail
from app.schemas.execution_event import ExecutionEvent, ExecutionEventType, ExecutionStage, sanitize_payload

__all__ = [
    "TaskSpec",
    "TaskConstraints",
    "TaskType",
    "ComplexityLevel",
    "Subtask",
    "ArchitectureSpec",
    "AgentConfigSchema",
    "TopologyType",
    "Connection",
    "ArchitectureValidator",
    "ValidationResult",
    "ValidationErrorDetail",
    "ExecutionStatus",
    "AgentStepLog",
    "AgentExecutionTrace",
    "ToolCallRecord",
    "ExecutionState",
    "ExecutionStateModel",
    "ExecutionResult",
    "EvaluationResult",
    "EvaluationMetrics",
    "ReflectionResult",
    "ReflectionIssue",
    "IssueCategory",
    "ArchitecturalRecommendation",
    "ExecutionEvent",
    "ExecutionEventType",
    "ExecutionStage",
    "sanitize_payload",
]
