"""
Unit and Integration Tests for Dynamic Settings, Tool Registry, Model Matrix, and Runtime Health.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.settings_manager import settings_manager
from app.schemas.settings import (
    ModelProviderEnum,
    RoleModelConfig,
    ModelMatrixUpdate,
    ExecutionPolicyUpdate,
)
from app.tools.tool_registry import tool_registry
from app.agents.base_agent import BaseAgent
from app.schemas.architecture import AgentConfigSchema
from app.schemas.validator import ArchitectureValidator, ValidationErrorDetail


@pytest.mark.asyncio
async def test_get_settings_summary_redacts_secrets():
    """Verify that settings summary contains metadata but strictly redacts raw secrets."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/settings/")
        assert resp.status_code == 200
        data = resp.json()

        # Tools verification
        assert "tools" in data
        assert len(data["tools"]) >= 3
        for tool in data["tools"]:
            assert "name" in tool
            assert "enabled" in tool
            assert "safety_classification" in tool
            assert "required_credentials" in tool
            # Ensure no secret strings leaked
            assert "api_key" not in tool
            assert "secret" not in tool

        # Model matrix verification
        assert "model_matrix" in data
        assert "roles" in data["model_matrix"]
        for role_name, role_cfg in data["model_matrix"]["roles"].items():
            assert "provider" in role_cfg
            assert "model_identifier" in role_cfg
            assert "credential_status" in role_cfg
            # Raw key must NOT be present
            assert "api_key" not in role_cfg

        # Policies
        assert "execution_policies" in data
        assert data["execution_policies"]["max_agents"] >= 1


@pytest.mark.asyncio
async def test_tool_registry_list_and_toggle():
    """Verify tool listing, toggling enabled/disabled, and persistence."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Check initial tools list
        resp = await client.get("/settings/tools")
        assert resp.status_code == 200
        tools = resp.json()
        tool_names = [t["name"] for t in tools]
        assert "python_tool" in tool_names
        assert "web_search" in tool_names

        # Toggle web_search to disabled
        toggle_resp = await client.post("/settings/tools/web_search/toggle", json={"enabled": False})
        assert toggle_resp.status_code == 200
        assert toggle_resp.json()["enabled"] is False
        assert tool_registry.is_tool_enabled("web_search") is False

        # Toggle back to enabled
        toggle_resp2 = await client.post("/settings/tools/web_search/toggle", json={"enabled": True})
        assert toggle_resp2.status_code == 200
        assert toggle_resp2.json()["enabled"] is True
        assert tool_registry.is_tool_enabled("web_search") is True


@pytest.mark.asyncio
async def test_tool_dispatch_rejection_when_disabled():
    """Verify that disabled tools are rejected during runtime agent dispatch."""
    # Temporarily disable python_tool
    tool_registry.disable_tool("python_tool")
    assert tool_registry.is_tool_enabled("python_tool") is False

    try:
        agent_config = AgentConfigSchema(
            agent_id="agent_calc_1",
            name="Calculator Agent",
            role="Executor",
            objective="Compute factorial of 5 using python_tool",
            system_prompt="You are a calculator agent.",
            tools=["python_tool"],
            input_keys=["task_prompt"],
            output_keys=["calc_output"],
        )
        tool_callable = tool_registry.get_tool("python_tool")
        agent = BaseAgent(config=agent_config, tools=[tool_callable])

        result = await agent.execute({"user_prompt": "Calculate factorial"})
        # Tool calls must be empty because python_tool is disabled!
        assert len(result["tool_calls"]) == 0
    finally:
        # Re-enable for subsequent tests
        tool_registry.enable_tool("python_tool")


@pytest.mark.asyncio
async def test_tool_dispatch_rejection_when_globally_forbidden():
    """Verify that globally forbidden tools in execution policies are not dispatched."""
    # Set web_search in forbidden_tools
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.put(
            "/settings/policies",
            json={"forbidden_tools": ["web_search"]},
        )
        assert resp.status_code == 200
        assert "web_search" in resp.json()["forbidden_tools"]

    try:
        agent_config = AgentConfigSchema(
            agent_id="agent_search_1",
            name="Search Agent",
            role="Researcher",
            objective="Retrieve information using web_search",
            system_prompt="You are a web search researcher agent.",
            tools=["web_search"],
            input_keys=["task_prompt"],
            output_keys=["search_output"],
        )
        search_callable = tool_registry.get_tool("web_search")
        agent = BaseAgent(config=agent_config, tools=[search_callable])

        result = await agent.execute({"user_prompt": "Search quantum computing"})
        # Must not have executed web_search because it is forbidden in policies!
        assert len(result["tool_calls"]) == 0
    finally:
        # Reset forbidden_tools
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.put("/settings/policies", json={"forbidden_tools": []})


@pytest.mark.asyncio
async def test_tool_test_endpoint_success_and_bounded():
    """Verify safe bounded execution of registered tools."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test python_tool
        test_resp = await client.post(
            "/settings/tools/python_tool/test",
            json={"test_input": {"code": "print(10 * 10)"}},
        )
        assert test_resp.status_code == 200
        data = test_resp.json()
        assert data["tool_name"] == "python_tool"
        assert data["status"] == "success"
        assert "100" in data["output_preview"]
        assert data["duration_ms"] > 0.0


@pytest.mark.asyncio
async def test_tool_test_endpoint_failure_path():
    """Verify structured error reporting when tool test fails safely."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test python_tool with prohibited import (sandbox violation)
        test_resp = await client.post(
            "/settings/tools/python_tool/test",
            json={"test_input": {"code": "import os\nos.system('ls')"}},
        )
        assert test_resp.status_code == 200
        data = test_resp.json()
        assert data["status"] == "error"
        assert "SecurityViolation" in data["error"] or "Prohibited" in data["error"] or "error" in data["output_preview"]


@pytest.mark.asyncio
async def test_model_matrix_validation_rejects_unsupported_provider():
    """Verify that assigning an unsupported provider is rejected with HTTP 400."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.put(
            "/settings/models",
            json={
                "assignments": {
                    "researcher": {
                        "role": "researcher",
                        "provider": "openai",
                        "model_identifier": "gpt-4o",
                    }
                }
            },
        )
        assert resp.status_code == 400
        assert "not supported" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_model_matrix_valid_update():
    """Verify updating role to valid Gemini model succeeds and affects lookup."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.put(
            "/settings/models",
            json={
                "assignments": {
                    "analyst": {
                        "role": "analyst",
                        "provider": "gemini",
                        "model_identifier": "gemini-2.0-flash",
                        "temperature": 0.1,
                    }
                }
            },
        )
        assert resp.status_code == 200
        matrix = resp.json()
        assert matrix["roles"]["analyst"]["model_identifier"] == "gemini-2.0-flash"

        # Check runtime lookup
        provider, model_name = settings_manager.get_model_for_role("analyst")
        assert provider == "gemini"
        assert model_name == "gemini-2.0-flash"


@pytest.mark.asyncio
async def test_execution_policy_validation_conflicts():
    """Verify that conflicting allowed and forbidden tools are rejected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.put(
            "/settings/policies",
            json={
                "allowed_tools": ["python_tool", "web_search"],
                "forbidden_tools": ["web_search"],
            },
        )
        assert resp.status_code == 400
        assert "simultaneously" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_execution_snapshot_immutability():
    """Verify that configuration snapshot is immutable and captures active settings."""
    snap1 = settings_manager.get_execution_snapshot()
    assert "snapshot_id" in snap1
    assert "config_version" in snap1
    assert "policies" in snap1
    assert "model_matrix" in snap1
    assert "enabled_tools" in snap1

    # Verify that changing a policy does not alter previously captured snapshot
    orig_agents = snap1["policies"]["max_agents"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.put("/settings/policies", json={"max_agents": 12})

    snap2 = settings_manager.get_execution_snapshot()
    assert snap2["policies"]["max_agents"] == 12
    # snap1 remains unchanged
    assert snap1["policies"]["max_agents"] == orig_agents

    # Reset max_agents
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.put("/settings/policies", json={"max_agents": orig_agents})


@pytest.mark.asyncio
async def test_runtime_health_diagnostics():
    """Verify runtime health checks return real diagnostic details for all 6 subsystems."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/settings/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "subsystems" in data

        subsystems = data["subsystems"]
        assert "api_service" in subsystems
        assert "database" in subsystems
        assert "model_provider" in subsystems
        assert "tools" in subsystems
        assert "execution_subsystem" in subsystems
        assert "event_streaming" in subsystems

        # Check real values
        assert subsystems["api_service"]["status"] == "healthy"
        assert subsystems["database"]["details"]["dialect"] in ("sqlite", "postgresql")
        assert subsystems["tools"]["details"]["registered_tools_count"] >= 3
