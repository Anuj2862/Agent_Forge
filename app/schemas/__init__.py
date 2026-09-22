"""
Shared Pydantic Data Contracts for Agent Forge.
"""

from app.schemas.task import TaskSpec, TaskType, ComplexityLevel, Subtask
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

__all__ = [
    "TaskSpec",
    "TaskType",
    "ComplexityLevel",
    "Subtask",
    "ArchitectureSpec",
    "AgentConfigSchema",
    "TopologyType",
    "Connection",
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
]
