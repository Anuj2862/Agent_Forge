"""
Evolution Memory Record Schema (Owned by Member 4).
Extended with persistence metadata for PostgreSQL storage and retrieval indexing.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.task import TaskSpec, TaskType, ComplexityLevel
from app.schemas.architecture import ArchitectureSpec
from app.schemas.evaluation import EvaluationResult
from app.schemas.reflection import ReflectionResult


class EvolutionMemoryRecord(BaseModel):
    """Complete evolution memory record linking TaskSpec → Architecture → Evaluation → Reflection."""

    record_id: str = Field(..., description="Unique memory record ID (UUID)")
    task_spec: TaskSpec = Field(..., description="Target task specification")
    architecture_spec: ArchitectureSpec = Field(..., description="Synthesized architecture specification")
    evaluation_result: EvaluationResult = Field(..., description="Execution evaluation results")
    reflection_result: ReflectionResult = Field(..., description="Reflection and recommendation results")
    success_rating: float = Field(..., ge=0.0, le=1.0, description="Composite success rating (0-1)")

    # Persistence & retrieval metadata (Member 4 additions)
    run_number: int = Field(default=1, ge=1, description="Which run iteration this record belongs to")
    task_type: TaskType = Field(default=TaskType.GENERAL, description="Task type for similarity retrieval")
    complexity: ComplexityLevel = Field(default=ComplexityLevel.MEDIUM, description="Complexity for retrieval")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When this record was created")
    execution_duration_seconds: float = Field(default=0.0, ge=0.0, description="Total E2E duration")
    agent_count: int = Field(default=1, ge=1, description="Number of agents in architecture")
    topology: str = Field(default="pipeline", description="Architecture topology used")
    recommendation_summary: Optional[str] = Field(
        default=None, description="Short summary of top recommendation for display"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "record_id": "mem_001",
                "run_number": 1,
                "task_type": "research",
                "complexity": "medium",
                "success_rating": 0.72,
                "timestamp": "2026-09-20T12:00:00Z",
                "execution_duration_seconds": 14.5,
                "agent_count": 3,
                "topology": "pipeline",
                "recommendation_summary": "Add a Verification Agent between analysis and writing stages."
            }
        }


class MemoryQueryResult(BaseModel):
    """Paginated list of memory records for API responses."""
    records: list[EvolutionMemoryRecord]
    total: int
    page: int
    page_size: int
