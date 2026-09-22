"""
Member 2 Domain: Tool Registry & Execution Capabilities Package.
"""

from app.tools.tool_registry import ToolRegistry, tool_registry
from app.tools.web_search import web_search_tool
from app.tools.python_tool import python_interpreter_tool
from app.tools.document_retriever import document_retriever_tool


def register_default_tools(registry: ToolRegistry = tool_registry) -> ToolRegistry:
    """Helper to register all standard prototype tools into a registry instance."""
    registry.register("web_search", web_search_tool, overwrite=True)
    registry.register("python_tool", python_interpreter_tool, overwrite=True)
    registry.register("document_retriever", document_retriever_tool, overwrite=True)
    return registry


# Automatically populate default global registry
register_default_tools(tool_registry)

__all__ = [
    "ToolRegistry",
    "tool_registry",
    "web_search_tool",
    "python_interpreter_tool",
    "document_retriever_tool",
    "register_default_tools",
]
