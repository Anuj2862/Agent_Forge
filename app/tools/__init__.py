"""
Member 2 Domain: Tool Registry & Execution Capabilities Package.
"""

import os
from app.schemas.settings import (
    ToolCategory,
    SafetyClassification,
    ToolStatus,
    ToolMetadataSchema,
)
from app.tools.tool_registry import ToolRegistry, tool_registry
from app.tools.web_search import web_search_tool
from app.tools.python_tool import python_interpreter_tool
from app.tools.document_retriever import document_retriever_tool


def register_default_tools(registry: ToolRegistry = tool_registry) -> ToolRegistry:
    """Helper to register all standard prototype tools into a registry instance with typed schemas."""
    # 1. Python Interpreter Tool
    registry.register(
        "python_tool",
        python_interpreter_tool,
        metadata=ToolMetadataSchema(
            name="python_tool",
            display_name="Python Code Interpreter",
            description=(
                "Executes Python code in an isolated subprocess with stripped environment, "
                "AST safety validation, timeout bounding, and memory/filesystem sandboxing."
            ),
            category=ToolCategory.CODE_EXECUTION,
            safety_classification=SafetyClassification.SANDBOXED_EXECUTION,
            implementation_status=ToolStatus.IMPLEMENTED,
            enabled=True,
            required_credentials=[],
            credentials_configured=True,
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python source code string to execute safely.",
                    }
                },
                "required": ["code"],
            },
        ),
        overwrite=True,
    )

    # 2. Web Search Tool
    tavily_key = os.getenv("TAVILY_API_KEY") or os.getenv("SERPER_API_KEY")
    registry.register(
        "web_search",
        web_search_tool,
        metadata=ToolMetadataSchema(
            name="web_search",
            display_name="Web Search & Fact Retrieval",
            description=(
                "Performs external web queries via Tavily/Serper HTTP APIs with structured "
                "fallback if credentials are not configured."
            ),
            category=ToolCategory.SEARCH,
            safety_classification=SafetyClassification.NETWORK_EGRESS,
            implementation_status=ToolStatus.IMPLEMENTED,
            enabled=True,
            required_credentials=["TAVILY_API_KEY", "SERPER_API_KEY"],
            credentials_configured=bool(tavily_key),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string to execute.",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Maximum number of search result snippets to retrieve.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        overwrite=True,
    )

    # 3. Document Retriever Tool
    registry.register(
        "document_retriever",
        document_retriever_tool,
        metadata=ToolMetadataSchema(
            name="document_retriever",
            display_name="Document & Knowledge Retriever",
            description=(
                "Retrieves indexed reference documents, architecture papers, and domain "
                "knowledge snippets for RAG augmentation."
            ),
            category=ToolCategory.RETRIEVAL,
            safety_classification=SafetyClassification.SAFE_READ_ONLY,
            implementation_status=ToolStatus.IMPLEMENTED,
            enabled=True,
            required_credentials=[],
            credentials_configured=True,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query string to match against knowledge corpora.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of top matching snippets to retrieve.",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        ),
        overwrite=True,
    )

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
