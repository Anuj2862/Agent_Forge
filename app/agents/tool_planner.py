"""
Tool Planner Subsystem (Owned by Member 2).
Plans and resolves tool assignments for dynamic agents specified in an ArchitectureSpec.
"""

import logging
from typing import Dict, List, Optional, Set, Union
from app.schemas.architecture import AgentConfigSchema, ArchitectureSpec
from app.tools.tool_registry import ToolRegistry, tool_registry

logger = logging.getLogger("agent_forge.agents.tool_planner")


class ToolResolutionError(ValueError, KeyError):
    """Raised when an unknown or unregistered tool or capability is requested."""
    pass


# Canonical mapping from capability names to Member 2 registered executable tools
CAPABILITY_TO_TOOL: Dict[str, str] = {
    "code_execution": "python_tool",
    "information_retrieval": "document_retriever",
    "web_search": "web_search",
    "python_tool": "python_tool",
    "document_retriever": "document_retriever",
}

# Non-executable capabilities that represent cognitive/analytical duties.
# These must NOT raise an error and are ignored for executable tool binding.
NON_EXECUTABLE_CAPABILITIES: Set[str] = {
    "data_analysis",
    "data_loading",
    "table_generation",
}


class ToolPlanner:
    """
    Decides and resolves executable tool assignments for agents.

    Accepts capabilities/tool requirements from an ArchitectureSpec (or list of AgentConfigSchema),
    maps abstract capabilities to concrete registered tools, handles non-executable capabilities,
    de-duplicates assignments while preserving order, and validates against ToolRegistry.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or tool_registry

    def resolve_tool_names(self, requirements: List[str]) -> List[str]:
        """
        Resolves a list of tool/capability requirements into validated, registered tool names.

        Rules:
        - Mapped capabilities: mapped via CAPABILITY_TO_TOOL.
        - Direct registered tool names: validated via registry.has_tool().
        - Non-executable capabilities: ignored without error.
        - Unknown/unregistered tools: raises ToolResolutionError.
        - Preserves insertion order and deduplicates.
        """
        resolved: List[str] = []
        seen: Set[str] = set()

        for req in requirements:
            if req in NON_EXECUTABLE_CAPABILITIES:
                logger.debug(
                    f"Requirement '{req}' is a non-executable capability and will not be assigned as an executable tool."
                )
                continue

            target_tool = CAPABILITY_TO_TOOL.get(req, req)

            if not self.registry.has_tool(target_tool):
                raise ToolResolutionError(
                    f"Cannot resolve requirement '{req}'. Tool '{target_tool}' is not registered in ToolRegistry. "
                    f"Available tools: {self.registry.list_tools()}"
                )

            if target_tool not in seen:
                seen.add(target_tool)
                resolved.append(target_tool)

        return resolved

    def plan_for_agent(self, agent_config: AgentConfigSchema) -> List[str]:
        """
        Resolves tool requirements for a single agent configuration into a list of registered tool names.
        Deduplicates while preserving order.
        """
        return self.resolve_tool_names(agent_config.tools)

    def plan(self, architecture: Union[ArchitectureSpec, List[AgentConfigSchema]]) -> Dict[str, List[str]]:
        """
        Plans and resolves executable tool assignments for all agents in an architecture.

        Args:
            architecture: ArchitectureSpec or list of AgentConfigSchema.

        Returns:
            Dict mapping agent_id -> List of resolved registered tool names.
        """
        if isinstance(architecture, ArchitectureSpec):
            agents = architecture.agents
        elif isinstance(architecture, list):
            agents = architecture
        else:
            raise ValueError("ToolPlanner.plan requires an ArchitectureSpec or a list of AgentConfigSchema.")

        assignments: Dict[str, List[str]] = {}
        for agent in agents:
            assignments[agent.agent_id] = self.plan_for_agent(agent)

        return assignments
