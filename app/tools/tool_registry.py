"""
Tool Registry (Owned by Member 2).
Central registry for registering and retrieving dynamic executable tools.
"""

from typing import Dict, Any, Callable, List, Optional


class ToolRegistry:
    """Manages available tool definitions and dynamic binding to agents."""

    def __init__(self):
        self._registry: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable, overwrite: bool = False) -> None:
        """Register a tool with a stable string identifier."""
        if not name or not isinstance(name, str):
            raise ValueError("Tool name must be a non-empty string.")
        if not callable(func):
            raise TypeError(f"Tool '{name}' must be a callable object.")
        if name in self._registry and not overwrite:
            raise ValueError(f"Tool '{name}' is already registered. Set overwrite=True to replace.")
        self._registry[name] = func

    def get_tool(self, name: str) -> Callable:
        """Retrieve a single registered tool by name."""
        if name not in self._registry:
            raise KeyError(
                f"Tool '{name}' is not registered in ToolRegistry. Available tools: {self.list_tools()}"
            )
        return self._registry[name]

    def get_tools(self, names: List[str]) -> List[Callable]:
        """Retrieve multiple registered tools by name list."""
        tools = []
        for name in names:
            tools.append(self.get_tool(name))
        return tools

    def list_tools(self) -> List[str]:
        """Return a list of all registered tool names."""
        return list(self._registry.keys())

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._registry

    def clear(self) -> None:
        """Clear all registered tools (useful for unit testing isolation)."""
        self._registry.clear()


tool_registry = ToolRegistry()
