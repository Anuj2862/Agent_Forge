"""
Shared Pydantic Schemas for Multi-Agent Graph Execution Trace & Results.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ToolCallRecord(BaseModel):
    tool_name: str = Field(..., description="Name of the invoked tool")
    input_parameters: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool")
    output: Optional[Any] = Field(default=None, description="Output returned by the tool")
    success: bool = Field(default=True, description="Whether tool execution succeeded")
    error_message: Optional[str] = Field(default=None, description="Error message if tool execution failed")
    duration_seconds: float = Field(default=0.0, ge=0.0, description="Duration of tool invocation in seconds")


class AgentExecutionTrace(BaseModel):
    agent_id: str = Field(..., description="ID of the executed agent")
    agent_name: Optional[str] = Field(default=None, description="Human-readable name of the agent")
    role: Optional[str] = Field(default=None, description="Role of the agent")
    status: ExecutionStatus = Field(default=ExecutionStatus.SUCCESS, description="Status of agent execution")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input payload provided to this agent")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Output payload produced by this agent")
    tool_calls: List[ToolCallRecord] = Field(default_factory=list, description="Tool invocations performed by this agent")
    duration_seconds: float = Field(default=0.0, ge=0.0, description="Execution time spent by this agent")
    error_message: Optional[str] = Field(default=None, description="Error detail if execution encountered failure")
    verified_claims: Optional[List[str]] = Field(default=None, description="Claims formally verified by this agent")
    unverified_claims: Optional[List[str]] = Field(default=None, description="Claims flagged as unsupported or unverified")
    contradictions_found: Optional[List[str]] = Field(default=None, description="Contradictions identified in content")


class ExecutionResult(BaseModel):
    execution_id: str = Field(..., description="Unique execution instance ID")
    task_id: str = Field(..., description="Target task ID")
    architecture_id: str = Field(..., description="Architecture spec ID executed")
    status: ExecutionStatus = Field(default=ExecutionStatus.SUCCESS, description="Overall execution status")
    final_output: Optional[str] = Field(default=None, description="Aggregated final response text")
    step_outputs: Dict[str, Any] = Field(default_factory=dict, description="Intermediate outputs keyed by agent or step ID")
    agent_traces: List[AgentExecutionTrace] = Field(default_factory=list, description="Ordered execution traces for each agent")
    total_execution_time: float = Field(default=0.0, ge=0.0, description="Total execution wall-clock time in seconds")
    iteration_count: int = Field(default=1, ge=1, description="Number of execution iterations / loops completed")
    total_tool_calls: int = Field(default=0, ge=0, description="Total number of tool calls executed")
    errors: List[str] = Field(default_factory=list, description="List of runtime errors or failure logs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary run metadata (tokens, model, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "exec_001",
                "task_id": "task_001",
                "architecture_id": "arch_001",
                "status": "success",
                "final_output": "Generative AI significantly alters the threat landscape in cybersecurity...",
                "step_outputs": {
                    "research_agent": {"findings": "GenAI enables sophisticated phishing at scale."},
                    "writer_agent": {"report": "Generative AI significantly alters the threat landscape..."}
                },
                "agent_traces": [
                    {
                        "agent_id": "research_agent",
                        "status": "success",
                        "duration_seconds": 3.2,
                        "tool_calls": [{"tool_name": "web_search", "success": True, "duration_seconds": 1.1}]
                    }
                ],
                "total_execution_time": 6.5,
                "iteration_count": 1,
                "total_tool_calls": 1,
                "errors": []
            }
        }
