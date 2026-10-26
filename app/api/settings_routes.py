"""
FastAPI Routes for Platform Settings, Tool Registry, Model Matrix, and Runtime Health.
All endpoints redact sensitive credentials, enforce strict server-side validation,
and operate against real platform components.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings_manager import settings_manager
from app.memory.database import get_db_session
from app.schemas.settings import (
    ToolMetadataSchema,
    ToolToggleRequest,
    ToolTestRequest,
    ToolTestResponse,
    ModelMatrixConfig,
    ModelMatrixUpdate,
    ExecutionPolicyConfig,
    ExecutionPolicyUpdate,
    SystemHealthResponse,
    SettingsSummaryResponse,
)
from app.tools.tool_registry import tool_registry

router = APIRouter(prefix="/settings", tags=["Settings & Platform Diagnostics"])


@router.get(
    "/",
    response_model=SettingsSummaryResponse,
    summary="Get Consolidated Platform Settings Summary",
    description="Returns complete settings including tools, model matrix, policies, and health diagnostics.",
)
async def get_settings_summary():
    return await settings_manager.get_summary()


# ---------------------------------------------------------------------------
# Tool Registry Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/tools",
    response_model=List[ToolMetadataSchema],
    summary="List Registered Tools",
    description="Returns all registered tools with implementation status, category, schema, and safety classification.",
)
async def list_tools():
    return tool_registry.list_tools_metadata()


@router.get(
    "/tools/{tool_name}",
    response_model=ToolMetadataSchema,
    summary="Inspect Tool Schema & Configuration",
    description="Inspect a specific registered tool's input schema and configuration without secret exposure.",
)
async def get_tool_metadata(tool_name: str):
    if not tool_registry.has_tool(tool_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' is not registered in ToolRegistry.",
        )
    return tool_registry.get_tool_metadata(tool_name)


@router.post(
    "/tools/{tool_name}/toggle",
    response_model=ToolMetadataSchema,
    summary="Enable or Disable a Tool",
    description="Enables or disables a tool for runtime dispatch. State is persisted.",
)
async def toggle_tool(
    tool_name: str,
    payload: ToolToggleRequest,
    db: AsyncSession = Depends(get_db_session),
):
    if not tool_registry.has_tool(tool_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' is not registered in ToolRegistry.",
        )

    if payload.enabled:
        tool_registry.enable_tool(tool_name)
    else:
        tool_registry.disable_tool(tool_name)

    await settings_manager.persist_tool_states(db=db)
    return tool_registry.get_tool_metadata(tool_name)


@router.post(
    "/tools/{tool_name}/test",
    response_model=ToolTestResponse,
    summary="Test Tool Execution",
    description="Executes a safe, bounded test of a registered tool with timeout and sandbox enforcement.",
)
async def test_tool(tool_name: str, payload: Optional[ToolTestRequest] = None):
    if not tool_registry.has_tool(tool_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' is not registered in ToolRegistry.",
        )

    test_input = payload.test_input if payload else None
    result = tool_registry.test_tool(name=tool_name, test_input=test_input, timeout_seconds=5.0)
    return result


# ---------------------------------------------------------------------------
# Model Matrix Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/models",
    response_model=ModelMatrixConfig,
    summary="Get Model Matrix by Role",
    description="Returns model configurations mapped by agent role, distinguishing supported from planned providers.",
)
async def get_model_matrix():
    return settings_manager.get_model_matrix()


@router.put(
    "/models",
    response_model=ModelMatrixConfig,
    summary="Update Model Matrix Assignments",
    description="Updates role-to-model assignments with server-side validation against supported providers.",
)
async def update_model_matrix(
    update: ModelMatrixUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await settings_manager.update_model_matrix(update, db=db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Execution Policy Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/policies",
    response_model=ExecutionPolicyConfig,
    summary="Get Execution Policies",
    description="Returns platform-wide execution policies (max agents, duration, tool call limits, allowed/forbidden tools).",
)
async def get_execution_policies():
    return settings_manager.get_execution_policies()


@router.put(
    "/policies",
    response_model=ExecutionPolicyConfig,
    summary="Update Execution Policies",
    description="Updates execution policies with validation against conflict rules and numeric limits.",
)
async def update_execution_policies(
    update: ExecutionPolicyUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await settings_manager.update_execution_policies(update, db=db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Runtime Health Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=SystemHealthResponse,
    summary="Comprehensive Runtime Health Diagnostics",
    description="Performs live checks on API, database engine, model connectivity, tools sandbox, and event streaming.",
)
async def get_runtime_health():
    return await settings_manager.check_runtime_health()
