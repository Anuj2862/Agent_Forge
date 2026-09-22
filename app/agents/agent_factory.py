"""
Dynamic Agent Factory Subsystem (Owned by Member 2).
Instantiates executable BaseAgent objects from AgentConfigSchema specifications.
"""

import logging
from typing import Callable, Dict, List, Optional, Set
from app.agents.base_agent import BaseAgent
from app.schemas.architecture import AgentConfigSchema, ArchitectureSpec
from app.tools.tool_registry import ToolRegistry, tool_registry

logger = logging.getLogger("agent_forge.agents")

# Explicit mapping from Member 1 capability names to Member 2 registered executable tools
CAPABILITY_TO_TOOL_MAP: Dict[str, str] = {
    "code_execution": "python_tool",
    "information_retrieval": "document_retriever",
    "web_search": "web_search",
    "python_tool": "python_tool",
    "document_retriever": "document_retriever",
}

# Non-executable capabilities produced by Member 1 that do not correspond to executable tools.
# These represent analytical/cognitive capabilities and must NOT raise KeyError or be treated as tools.
NON_EXECUTABLE_CAPABILITIES: Set[str] = {
    "data_analysis",
    "data_loading",
    "table_generation",
}


class AgentFactory:
    """Instantiates dynamic agents from JSON configuration specifications without hardcoded roles."""

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or tool_registry

    def resolve_tools(self, tool_names: List[str]) -> List[Callable]:
        """
        Resolves a list of requested tool or capability names into executable tool callables.

        Rules:
        - Mapped capabilities:
            'code_execution' -> 'python_tool'
            'information_retrieval' -> 'document_retriever'
        - Direct valid tool names:
            'web_search' -> 'web_search'
            'python_tool' -> 'python_tool'
            'document_retriever' -> 'document_retriever'
            (and any other tool directly registered in self.registry)
        - Non-executable capabilities:
            'data_analysis', 'data_loading', 'table_generation'
            Ignored for tool binding with a warning; no KeyError is raised.
        - Unknown tools/capabilities:
            Raise KeyError via self.registry.get_tool().
        """
        resolved: List[Callable] = []
        for name in tool_names:
            if name in NON_EXECUTABLE_CAPABILITIES:
                logger.warning(
                    f"Capability '{name}' is non-executable and will not be bound as an executable tool."
                )
                continue

            target_name = CAPABILITY_TO_TOOL_MAP.get(name, name)
            tool_callable = self.registry.get_tool(target_name)
            resolved.append(tool_callable)

        return resolved

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

        # Resolve requested tools dynamically from registry using capability resolution
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

        Args:
            configs: List of AgentConfigSchema specifications.
            llm_runner: Optional custom LLM runner.

        Returns:
            Dict mapping agent_id -> BaseAgent.
        """
        if not isinstance(configs, list) or not configs:
            raise ValueError("AgentFactory.create_agent_team requires a non-empty list of AgentConfigSchema objects.")

        agents_by_id: Dict[str, BaseAgent] = {}

        for config in configs:
            if config.agent_id in agents_by_id:
                raise ValueError(
                    f"Duplicate agent_id '{config.agent_id}' detected in team configuration. Agent IDs must be unique."
                )
            agents_by_id[config.agent_id] = self.create_agent(config, llm_runner=llm_runner)

        return agents_by_id

    def create_from_architecture(
        self,
        architecture: ArchitectureSpec,
        llm_runner: Optional[Callable] = None,
    ) -> Dict[str, BaseAgent]:
        """
        Instantiates all agents defined within an ArchitectureSpec.

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

        return self.create_agent_team(architecture.agents, llm_runner=llm_runner)
