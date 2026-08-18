"""
Tool Registry (Owned by Member 2).
Central registry for registering and retrieving dynamic executable tools.
"""

from typing import Dict, Any, Callable


class ToolRegistry:
    """Manages available tool definitions and dynamic binding to agents."""

    def __init__(self):
        self._registry: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self._registry[name] = func

    def get_tool(self, name: str) -> Callable:
        if name not in self._registry:
            raise KeyError(f"Tool '{name}' is not registered in ToolRegistry.")
        return self._registry[name]


tool_registry = ToolRegistry()
