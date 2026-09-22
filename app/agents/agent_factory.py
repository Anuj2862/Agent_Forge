"""
Dynamic Agent Factory Subsystem (Owned by Member 2).
Instantiates executable BaseAgent objects from AgentConfigSchema specifications.
"""

import logging
from typing import Callable, Dict, List, Optional, Set
from app.agents.base_agent import BaseAgent
from app.agents.tool_planner import (
    ToolPlanner,
    ToolResolutionError,
    CAPABILITY_TO_TOOL,
    NON_EXECUTABLE_CAPABILITIES,
)
from app.schemas.architecture import AgentConfigSchema, ArchitectureSpec
from app.tools.tool_registry import ToolRegistry, tool_registry

logger = logging.getLogger("agent_forge.agents")

# Backward-compatible alias
CAPABILITY_TO_TOOL_MAP: Dict[str, str] = CAPABILITY_TO_TOOL


class AgentFactory:
    """Instantiates dynamic agents from JSON configuration specifications without hardcoded roles."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        planner: Optional[ToolPlanner] = None,
    ):
        self.registry = registry or tool_registry
        self.planner = planner or ToolPlanner(registry=self.registry)

    def resolve_tools(self, tool_names: List[str]) -> List[Callable]:
        """
        Resolves a list of requested tool or capability names into executable tool callables.
        Delegates resolution to the ToolPlanner.
        """
        resolved_tool_names = self.planner.resolve_tool_names(tool_names)
        return [self.registry.get_tool(name) for name in resolved_tool_names]

    def create_agent(
        self,
        config: AgentConfigSchema,
        llm_runner: Optional[Callable] = None,
    ) -> BaseAgent:
        """
        Dynamically instantiates a BaseAgent from an AgentConfigSchema.

        Args:
            config: AgentConfigSchema specification.
            llm_runner: Optional custom LLM runner for testing/mocking.

        Returns:
            Instantiated BaseAgent with resolved tools.
        """
        if not isinstance(config, AgentConfigSchema):
            raise ValueError("AgentFactory.create_agent requires an AgentConfigSchema instance.")
        if not config.agent_id or not config.agent_id.strip():
            raise ValueError("AgentConfigSchema agent_id must be a non-empty string.")
        if not config.role or not config.role.strip():
            raise ValueError("AgentConfigSchema role must be a non-empty string.")

        # Resolve requested tools dynamically from registry using ToolPlanner
        tools: List[Callable] = []
        if config.tools:
            tools = self.resolve_tools(config.tools)

        return BaseAgent(config=config, tools=tools, llm_runner=llm_runner)

    def create_agent_team(
        self,
        configs: List[AgentConfigSchema],
        llm_runner: Optional[Callable] = None,
    ) -> Dict[str, BaseAgent]:
        """
        Instantiates a team of agents keyed by agent_id.
        Plans tool assignments once for the team via ToolPlanner.

        Args:
            configs: List of AgentConfigSchema specifications.
            llm_runner: Optional custom LLM runner.

        Returns:
            Dict mapping agent_id -> BaseAgent.
        """
        if not isinstance(configs, list) or not configs:
            raise ValueError("AgentFactory.create_agent_team requires a non-empty list of AgentConfigSchema objects.")

        # Plan tool assignments ONCE for all agents in the team
        tool_assignments: Dict[str, List[str]] = self.planner.plan(configs)

        agents_by_id: Dict[str, BaseAgent] = {}
        for config in configs:
            if config.agent_id in agents_by_id:
                raise ValueError(
                    f"Duplicate agent_id '{config.agent_id}' detected in team configuration. Agent IDs must be unique."
                )
            resolved_names = tool_assignments.get(config.agent_id, [])
            resolved_tools = [self.registry.get_tool(name) for name in resolved_names]
            agents_by_id[config.agent_id] = BaseAgent(
                config=config,
                tools=resolved_tools,
                llm_runner=llm_runner,
            )

        return agents_by_id

    def create_from_architecture(
        self,
        architecture: ArchitectureSpec,
        llm_runner: Optional[Callable] = None,
    ) -> Dict[str, BaseAgent]:
        """
        Instantiates all agents defined within an ArchitectureSpec.
        Plans tool assignments ONCE for the entire architecture via ToolPlanner.

        Args:
            architecture: Target ArchitectureSpec synthesized by Member 1.
            llm_runner: Optional custom LLM runner.

        Returns:
            Dict mapping agent_id -> BaseAgent.
        """
        if not isinstance(architecture, ArchitectureSpec):
            raise ValueError("AgentFactory.create_from_architecture requires an ArchitectureSpec instance.")
        if not architecture.agents:
            raise ValueError(f"ArchitectureSpec '{architecture.architecture_id}' contains no agent definitions.")

        # Plan tool assignments ONCE for the entire architecture
        tool_assignments: Dict[str, List[str]] = self.planner.plan(architecture)

        agents_by_id: Dict[str, BaseAgent] = {}
        for config in architecture.agents:
            if config.agent_id in agents_by_id:
                raise ValueError(
                    f"Duplicate agent_id '{config.agent_id}' detected in team configuration. Agent IDs must be unique."
                )
            resolved_names = tool_assignments.get(config.agent_id, [])
            resolved_tools = [self.registry.get_tool(name) for name in resolved_names]
            agents_by_id[config.agent_id] = BaseAgent(
                config=config,
                tools=resolved_tools,
                llm_runner=llm_runner,
            )

        return agents_by_id
