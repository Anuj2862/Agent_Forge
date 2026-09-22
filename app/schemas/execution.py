"""
Shared Pydantic & TypedDict Schemas for Dynamic Execution Engine (Member 2).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"


class AgentStepLog(BaseModel):
    step_id: str = Field(..., description="Unique identifier for this step log")
    agent_id: str = Field(..., description="ID of the agent executing this step")
    agent_role: Optional[str] = Field(default=None, description="Role of the executing agent")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the step was executed",
    )
    input_state: Dict[str, Any] = Field(default_factory=dict, description="Input state provided to the agent")
    output_state: Dict[str, Any] = Field(default_factory=dict, description="Output state produced by the agent")
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tool calls made during this execution step"
    )
    status: str = Field(default="completed", description="Status of the step (e.g., completed, failed)")
    execution_time_seconds: float = Field(default=0.0, ge=0.0, description="Step duration in seconds")
    error: Optional[str] = Field(default=None, description="Error message if step failed")


class ExecutionState(TypedDict, total=False):
    """
    TypedDict representing the runtime state passed through LangGraph nodes.
    Designed for practical state mutation and LangGraph reducer compatibility.
    """
    task_id: str
    user_prompt: str
    current_agent: str
    messages: List[Dict[str, Any]]
    agent_outputs: Dict[str, Any]
    step_history: List[Dict[str, Any]]
    final_output: Optional[str]
    error: Optional[str]
    retry_count: int
    metadata: Dict[str, Any]


class ExecutionStateModel(BaseModel):
    """
    Pydantic model equivalent of ExecutionState for validation and API serialization.
    """
    task_id: str = Field(..., description="Target task identifier")
    user_prompt: str = Field(..., description="User prompt / input text")
    current_agent: Optional[str] = Field(default=None, description="Currently active agent_id")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Message log history")
    agent_outputs: Dict[str, Any] = Field(default_factory=dict, description="Latest outputs per agent_id")
    step_history: List[AgentStepLog] = Field(default_factory=list, description="List of recorded step logs")
    final_output: Optional[str] = Field(default=None, description="Final aggregated output text")
    error: Optional[str] = Field(default=None, description="Error details if execution failed")
    retry_count: int = Field(default=0, ge=0, description="Number of execution retries attempted")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional runtime metadata")


class ExecutionResult(BaseModel):
    """
    Structured execution result produced by Member 2 Execution Engine,
    designed for direct consumption by Member 3 (Evaluator).
    """
    execution_id: str = Field(..., description="Unique execution instance identifier")
    task_id: str = Field(..., description="Target task identifier")
    architecture_id: str = Field(..., description="Synthesized architecture ID executed")
    status: ExecutionStatus = Field(default=ExecutionStatus.SUCCESS, description="Final execution status")
    final_output: Optional[str] = Field(default=None, description="Final output response generated")
    step_history: List[AgentStepLog] = Field(default_factory=list, description="Ordered step logs")
    total_steps: int = Field(default=0, ge=0, description="Total agent steps executed")
    execution_time_seconds: float = Field(default=0.0, ge=0.0, description="Total execution duration in seconds")
    agent_count: int = Field(default=0, ge=0, description="Total active agents involved in execution")
    tool_call_count: int = Field(default=0, ge=0, description="Total tool invocations across all steps")
    error: Optional[str] = Field(default=None, description="Global error detail if execution failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata and metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "exec_001",
                "task_id": "task_001",
                "architecture_id": "arch_001",
                "status": "success",
                "final_output": "Generative AI significantly impacts cybersecurity...",
                "step_history": [
                    {
                        "step_id": "step_1",
                        "agent_id": "research_agent",
                        "agent_role": "Researcher",
                        "timestamp": "2026-09-15T15:00:00Z",
                        "input_state": {"user_prompt": "Research GenAI cybersecurity"},
                        "output_state": {"research_data": "Found 5 key threats"},
                        "tool_calls": [{"tool": "web_search", "query": "GenAI threats"}],
                        "status": "completed",
                        "execution_time_seconds": 3.2,
                        "error": None,
                    }
                ],
                "total_steps": 1,
                "execution_time_seconds": 3.2,
                "agent_count": 1,
                "tool_call_count": 1,
                "error": None,
                "metadata": {"token_usage": 450},
            }
        }
