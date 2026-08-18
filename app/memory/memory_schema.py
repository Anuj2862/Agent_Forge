"""
Evolution Memory Record Schema (Owned by Member 4).
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec
from app.schemas.evaluation import EvaluationResult
from app.schemas.reflection import ReflectionResult


class EvolutionMemoryRecord(BaseModel):
    record_id: str = Field(..., description="Unique memory record ID")
    task_spec: TaskSpec = Field(..., description="Target task specification")
    architecture_spec: ArchitectureSpec = Field(..., description="Synthesized architecture specification")
    evaluation_result: EvaluationResult = Field(..., description="Execution evaluation results")
    reflection_result: ReflectionResult = Field(..., description="Reflection and recommendation results")
    success_rating: float = Field(..., description="Final success rating")
