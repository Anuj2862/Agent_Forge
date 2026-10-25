"""
Shared Pydantic Schemas for Task Definition & Meta Controller Analysis.
"""

from enum import Enum
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


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


class TaskConstraints(BaseModel):
    """Explicit typed operational constraints passed with task submission."""
    max_agents: Optional[int] = Field(default=None, ge=1, description="Hard upper bound on agent count")
    max_execution_time_seconds: Optional[float] = Field(
        default=None, ge=0.0, description="Max allowed execution duration in seconds"
    )
    allowed_tools: List[str] = Field(default_factory=list, description="Explicit whitelist of allowed tools")
    forbidden_tools: List[str] = Field(default_factory=list, description="Explicit blacklist of prohibited tools")
    require_verification: bool = Field(
        default=False, description="Whether an independent verification stage is strictly mandatory"
    )
    constraints: List[str] = Field(default_factory=list, description="Additional constraint statements")

    model_config = ConfigDict(extra="ignore")

    def __len__(self) -> int:
        count = len(self.constraints)
        if self.max_agents is not None:
            count += 1
        if self.max_execution_time_seconds is not None:
            count += 1
        if self.forbidden_tools:
            count += len(self.forbidden_tools)
        if self.allowed_tools:
            count += len(self.allowed_tools)
        if self.require_verification:
            count += 1
        return count

    def __iter__(self):
        items = list(self.constraints)
        if self.max_agents is not None:
            items.append(f"max_agents:{self.max_agents}")
        for ft in self.forbidden_tools:
            items.append(f"forbidden_tool:{ft}")
        for at in self.allowed_tools:
            items.append(f"allowed_tool:{at}")
        if self.require_verification:
            items.append("require_verification")
        return iter(items)


class TaskSpec(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the user task")
    user_prompt: str = Field(..., description="Original raw natural language prompt from the user")
    task_type: TaskType = Field(default=TaskType.GENERAL, description="Categorized task type")
    complexity: ComplexityLevel = Field(default=ComplexityLevel.MEDIUM, description="Assessed complexity level")
    subtasks: List[Subtask] = Field(default_factory=list, description="Decomposed subtasks list")
    required_capabilities: List[str] = Field(
        default_factory=list, description="Extracted capabilities required across all subtasks"
    )
    constraints: Union[TaskConstraints, List[str]] = Field(default_factory=list, description="Identified constraints or guardrails")
    expected_output_format: Optional[str] = Field(
        default=None, description="Target format for the final response (e.g. markdown_report)"
    )

    # Explicit Typed Operational Constraints (P0)
    max_agents: Optional[int] = Field(default=None, ge=1, description="Hard upper bound on agent count")
    max_execution_time_seconds: Optional[float] = Field(
        default=None, ge=0.0, description="Max allowed execution duration in seconds"
    )
    allowed_tools: List[str] = Field(default_factory=list, description="Explicit whitelist of allowed tools")
    forbidden_tools: List[str] = Field(default_factory=list, description="Explicit blacklist of prohibited tools")
    require_verification: bool = Field(
        default=False, description="Whether an independent verification stage is strictly mandatory"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary task metadata and retrieved memories"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task_001",
                "user_prompt": "Research the impact of Generative AI on cybersecurity and produce a verified report.",
                "task_type": "research",
                "complexity": "medium",
                "max_agents": 2,
                "forbidden_tools": ["python_tool"],
                "require_verification": True,
                "subtasks": [
                    {
                        "id": "subtask_1",
                        "title": "Information Gathering",
                        "description": "Collect recent data on GenAI cybersecurity threats",
                        "required_capabilities": ["web_search", "information_retrieval"],
                    }
                ],
                "required_capabilities": ["research", "analysis", "verification", "writing"],
                "constraints": ["Ensure factual accuracy", "max_agents=2"],
                "expected_output_format": "verified_markdown_report",
            }
        }
    )
