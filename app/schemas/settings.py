"""
Pydantic Schemas for Platform Settings, Tool Registry, Model Matrix, and Runtime Health.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ToolCategory(str, Enum):
    SEARCH = "search"
    CODE_EXECUTION = "code_execution"
    RETRIEVAL = "retrieval"
    DATABASE = "database"
    UTILITY = "utility"


class SafetyClassification(str, Enum):
    SAFE_READ_ONLY = "safe_read_only"
    SANDBOXED_EXECUTION = "sandboxed_execution"
    NETWORK_EGRESS = "network_egress"
    UNRESTRICTED = "unrestricted"


class ToolStatus(str, Enum):
    IMPLEMENTED = "implemented"
    PROTOTYPE = "prototype"
    PLANNED = "planned"


class ToolMetadataSchema(BaseModel):
    name: str = Field(..., description="Unique tool identifier")
    display_name: str = Field(..., description="Human-readable tool title")
    description: str = Field(..., description="Functional summary of the tool")
    category: ToolCategory = Field(..., description="Tool category")
    safety_classification: SafetyClassification = Field(..., description="Safety and sandbox level")
    implementation_status: ToolStatus = Field(default=ToolStatus.IMPLEMENTED)
    enabled: bool = Field(default=True, description="Whether tool is enabled for runtime dispatch")
    required_credentials: List[str] = Field(default_factory=list, description="Environment variables needed")
    credentials_configured: bool = Field(default=False, description="Whether required credentials exist (secrets never exposed)")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for inputs")
    last_tested_at: Optional[datetime] = Field(default=None)
    last_test_status: Optional[str] = Field(default=None)
    last_test_latency_ms: Optional[float] = Field(default=None)

    model_config = ConfigDict(extra="ignore")


class ToolToggleRequest(BaseModel):
    enabled: bool = Field(..., description="New enabled state for the tool")


class ToolTestRequest(BaseModel):
    test_input: Optional[Dict[str, Any]] = Field(default=None, description="Optional custom test payload")


class ToolTestResponse(BaseModel):
    tool_name: str
    status: str = Field(..., description="'success', 'error', or 'no_credentials'")
    duration_ms: float
    output_preview: str
    error: Optional[str] = None
    tested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Model Matrix Schemas
# ---------------------------------------------------------------------------

class AgentRoleEnum(str, Enum):
    META_CONTROLLER = "meta_controller"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    PLANNER = "planner"
    EXECUTOR = "executor"
    VERIFIER = "verifier"
    CRITIC = "critic"
    ARCHITECTURE_MUTATOR = "architecture_mutator"


class ModelProviderEnum(str, Enum):
    GEMINI = "gemini"
    MOCK_DETERMINISTIC = "mock_deterministic"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


# Set of providers actually implemented and supported for execution
SUPPORTED_PROVIDERS = {ModelProviderEnum.GEMINI, ModelProviderEnum.MOCK_DETERMINISTIC}
UNSUPPORTED_PROVIDERS = {ModelProviderEnum.OPENAI, ModelProviderEnum.ANTHROPIC, ModelProviderEnum.OLLAMA}


class RoleModelConfig(BaseModel):
    role: AgentRoleEnum
    provider: ModelProviderEnum
    model_identifier: str = Field(..., min_length=1)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    is_supported: bool = Field(default=True)
    credential_status: str = Field(default="configured", description="'configured', 'missing', or 'offline'")

    model_config = ConfigDict(extra="ignore")


class ModelMatrixConfig(BaseModel):
    roles: Dict[AgentRoleEnum, RoleModelConfig] = Field(
        default_factory=dict,
        description="Model configuration keyed by agent role"
    )
    supported_providers: List[str] = Field(default_factory=lambda: [p.value for p in SUPPORTED_PROVIDERS])
    unsupported_providers: List[str] = Field(default_factory=lambda: [p.value for p in UNSUPPORTED_PROVIDERS])


class ModelMatrixUpdate(BaseModel):
    assignments: Dict[str, RoleModelConfig] = Field(
        ...,
        description="Role-to-model assignments to update"
    )


# ---------------------------------------------------------------------------
# Execution Policy Schemas
# ---------------------------------------------------------------------------

class ExecutionPolicyConfig(BaseModel):
    max_agents: int = Field(default=8, ge=1, le=20, description="Platform upper limit on total agent nodes")
    max_execution_duration_seconds: float = Field(
        default=60.0, ge=5.0, le=300.0, description="Maximum execution duration before timeout"
    )
    max_tool_calls_per_agent: int = Field(
        default=5, ge=1, le=20, description="Maximum tool calls an agent can execute per run"
    )
    allowed_tools: List[str] = Field(
        default_factory=lambda: ["python_tool", "web_search", "document_retriever"],
        description="Global whitelist of allowable tools"
    )
    forbidden_tools: List[str] = Field(
        default_factory=list,
        description="Global blacklist of strictly prohibited tools"
    )
    require_verification_by_default: bool = Field(
        default=False,
        description="Whether an independent verification agent is strictly mandatory for all tasks"
    )
    sandbox_isolation_enabled: bool = Field(
        default=True,
        description="Enforces subprocess isolation and AST safety validation for Python code execution"
    )

    model_config = ConfigDict(extra="ignore")


class ExecutionPolicyUpdate(BaseModel):
    max_agents: Optional[int] = Field(default=None, ge=1, le=20)
    max_execution_duration_seconds: Optional[float] = Field(default=None, ge=5.0, le=300.0)
    max_tool_calls_per_agent: Optional[int] = Field(default=None, ge=1, le=20)
    allowed_tools: Optional[List[str]] = Field(default=None)
    forbidden_tools: Optional[List[str]] = Field(default=None)
    require_verification_by_default: Optional[bool] = Field(default=None)
    sandbox_isolation_enabled: Optional[bool] = Field(default=None)


# ---------------------------------------------------------------------------
# Runtime Health Schemas
# ---------------------------------------------------------------------------

class SubsystemHealth(BaseModel):
    name: str
    status: str = Field(..., description="'healthy', 'degraded', 'unavailable'")
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SystemHealthResponse(BaseModel):
    overall_status: str = Field(..., description="'healthy', 'degraded', 'unavailable'")
    version: str = "0.2.0"
    environment: str = "development"
    subsystems: Dict[str, SubsystemHealth]
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Combined Settings Summary Schema
# ---------------------------------------------------------------------------

class SettingsSummaryResponse(BaseModel):
    version: str = "0.2.0"
    tools: List[ToolMetadataSchema]
    model_matrix: ModelMatrixConfig
    execution_policies: ExecutionPolicyConfig
    health_summary: SystemHealthResponse
