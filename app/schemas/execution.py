"""
Shared Pydantic & TypedDict Schemas for Dynamic Execution Engine & Multi-Agent Traces.
Supports both Member 2 Runtime Execution Engine and Member 3 Evaluator.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field, model_validator


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"


class ToolCallRecord(BaseModel):
    tool_name: str = Field(..., description="Name of the invoked tool")
    input_parameters: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool")
    output: Optional[Any] = Field(default=None, description="Output returned by the tool")
    success: bool = Field(default=True, description="Whether tool execution succeeded")
    error_message: Optional[str] = Field(default=None, description="Error message if tool execution failed")
    duration_seconds: float = Field(default=0.0, ge=0.0, description="Duration of tool invocation in seconds")


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
    Unified execution result schema supporting Member 2 Runtime Execution Engine
    and Member 3 Evaluator and Reflection Engine.
    """
    execution_id: str = Field(..., description="Unique execution instance identifier")
    task_id: str = Field(..., description="Target task identifier")
    architecture_id: str = Field(..., description="Synthesized architecture ID executed")
    status: ExecutionStatus = Field(default=ExecutionStatus.SUCCESS, description="Final execution status")
    final_output: Optional[str] = Field(default=None, description="Final output response generated")

    # Member 2 execution engine fields
    step_history: List[AgentStepLog] = Field(default_factory=list, description="Ordered step logs")
    total_steps: int = Field(default=0, ge=0, description="Total agent steps executed")
    execution_time_seconds: float = Field(default=0.0, ge=0.0, description="Total execution duration in seconds")
    agent_count: int = Field(default=0, ge=0, description="Total active agents involved in execution")
    tool_call_count: int = Field(default=0, ge=0, description="Total tool invocations across all steps")
    error: Optional[str] = Field(default=None, description="Global error detail if execution failed")

    # Member 3 evaluator & reflection fields
    step_outputs: Dict[str, Any] = Field(default_factory=dict, description="Intermediate outputs keyed by agent or step ID")
    agent_traces: List[AgentExecutionTrace] = Field(default_factory=list, description="Ordered execution traces for each agent")
    total_execution_time: float = Field(default=0.0, ge=0.0, description="Total execution wall-clock time in seconds")
    iteration_count: int = Field(default=1, ge=1, description="Number of execution iterations / loops completed")
    total_tool_calls: int = Field(default=0, ge=0, description="Total number of tool calls executed")
    errors: List[str] = Field(default_factory=list, description="List of runtime errors or failure logs")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata and metrics")

    @model_validator(mode="after")
    def sync_interoperability_fields(self) -> "ExecutionResult":
        # Synchronize execution time
        if self.total_execution_time == 0.0 and self.execution_time_seconds > 0.0:
            self.total_execution_time = self.execution_time_seconds
        elif self.execution_time_seconds == 0.0 and self.total_execution_time > 0.0:
            self.execution_time_seconds = self.total_execution_time

        # Synchronize tool call counts
        if self.total_tool_calls == 0 and self.tool_call_count > 0:
            self.total_tool_calls = self.tool_call_count
        elif self.tool_call_count == 0 and self.total_tool_calls > 0:
            self.tool_call_count = self.total_tool_calls

        # Synchronize error representations
        if self.error and not self.errors:
            self.errors = [self.error]
        elif self.errors and not self.error:
            self.error = self.errors[0]

        # Synchronize step_history -> agent_traces if agent_traces empty
        if self.step_history and not self.agent_traces:
            for s in self.step_history:
                tools = []
                for tc in s.tool_calls:
                    tools.append(ToolCallRecord(
                        tool_name=tc.get("tool", tc.get("tool_name", "unknown")),
                        input_parameters=tc.get("parameters", tc.get("args", {})),
                        output=tc.get("output"),
                        success=tc.get("success", True),
                    ))
                self.agent_traces.append(AgentExecutionTrace(
                    agent_id=s.agent_id,
                    role=s.agent_role,
                    duration_seconds=s.execution_time_seconds,
                    tool_calls=tools,
                    output_data=s.output_state,
                    input_data=s.input_state,
                    error_message=s.error,
                ))

        # Synchronize agent_traces -> step_history if step_history empty
        if self.agent_traces and not self.step_history:
            for i, t in enumerate(self.agent_traces):
                self.step_history.append(AgentStepLog(
                    step_id=f"step_{i+1}",
                    agent_id=t.agent_id,
                    agent_role=t.role,
                    input_state=t.input_data,
                    output_state=t.output_data,
                    tool_calls=[tc.model_dump() for tc in t.tool_calls],
                    execution_time_seconds=t.duration_seconds,
                    error=t.error_message,
                ))

        # Total steps count
        if self.total_steps == 0:
            self.total_steps = len(self.step_history) or len(self.agent_traces)

        # Agent count
        if self.agent_count == 0:
            ids = {s.agent_id for s in self.step_history} or {t.agent_id for t in self.agent_traces}
            self.agent_count = len(ids)

        return self
