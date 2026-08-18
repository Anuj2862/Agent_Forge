"""
Shared Pydantic Data Contracts for Agent Forge.
"""

from app.schemas.task import TaskSpec, TaskType, ComplexityLevel, Subtask
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType, Connection
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
    "EvaluationResult",
    "EvaluationMetrics",
    "ReflectionResult",
    "ReflectionIssue",
    "IssueCategory",
    "ArchitecturalRecommendation",
]
