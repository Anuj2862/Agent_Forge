"""
Shared Pydantic Schemas for Task Definition & Meta Controller Analysis.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    RESEARCH = "research"
    DATA_ANALYSIS = "data_analysis"
    CODE_GENERATION = "code_generation"
    CONTENT_CREATION = "content_creation"
    PROBLEM_SOLVING = "problem_solving"
    GENERAL = "general"


class ComplexityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Subtask(BaseModel):
    id: str = Field(..., description="Unique subtask identifier, e.g. subtask_1")
    title: str = Field(..., description="Short title of the subtask")
    description: str = Field(..., description="Detailed description of what needs to be accomplished")
    required_capabilities: List[str] = Field(
        default_factory=list, description="Capabilities needed to execute this subtask"
    )


class TaskSpec(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the user task")
    user_prompt: str = Field(..., description="Original raw natural language prompt from the user")
    task_type: TaskType = Field(default=TaskType.GENERAL, description="Categorized task type")
    complexity: ComplexityLevel = Field(default=ComplexityLevel.MEDIUM, description="Assessed complexity level")
    subtasks: List[Subtask] = Field(default_factory=list, description="Decomposed subtasks list")
    required_capabilities: List[str] = Field(
        default_factory=list, description="Extracted capabilities required across all subtasks"
    )
    constraints: List[str] = Field(default_factory=list, description="Identified constraints or guardrails")
    expected_output_format: Optional[str] = Field(
        default=None, description="Target format for the final response (e.g. markdown_report)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_001",
                "user_prompt": "Research the impact of Generative AI on cybersecurity and produce a verified report.",
                "task_type": "research",
                "complexity": "medium",
                "subtasks": [
                    {
                        "id": "subtask_1",
                        "title": "Information Gathering",
                        "description": "Collect recent data on GenAI cybersecurity threats",
                        "required_capabilities": ["web_search", "information_retrieval"]
                    }
                ],
                "required_capabilities": ["research", "analysis", "verification", "writing"],
                "constraints": ["Ensure factual accuracy"],
                "expected_output_format": "verified_markdown_report"
            }
        }
