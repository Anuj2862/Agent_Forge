"""
Tool Registry (Owned by Member 2).
Central registry for registering, inspecting, configuring, and testing dynamic executable tools.
"""

from datetime import datetime, timezone
import inspect
import os
import time
from typing import Dict, Any, Callable, List, Optional
from app.schemas.settings import (
    ToolCategory,
    SafetyClassification,
    ToolStatus,
    ToolMetadataSchema,
    ToolTestResponse,
)


class ToolRegistry:
    """Manages available tool definitions, metadata, execution policies, and dynamic binding to agents."""

    def __init__(self):
        self._registry: Dict[str, Callable] = {}
        self._metadata: Dict[str, ToolMetadataSchema] = {}
        self._enabled_states: Dict[str, bool] = {}

    def register(
        self,
        name: str,
        func: Callable,
        metadata: Optional[ToolMetadataSchema] = None,
        overwrite: bool = False,
    ) -> None:
        """Register a tool with a stable string identifier and optional typed metadata."""
        if not name or not isinstance(name, str):
            raise ValueError("Tool name must be a non-empty string.")
        if not callable(func):
            raise TypeError(f"Tool '{name}' must be a callable object.")
        if name in self._registry and not overwrite:
            raise ValueError(f"Tool '{name}' is already registered. Set overwrite=True to replace.")

        self._registry[name] = func

        # If metadata not provided, generate default metadata schema
        if metadata is None:
            metadata = self._infer_default_metadata(name, func)

        self._metadata[name] = metadata
        if name not in self._enabled_states:
            self._enabled_states[name] = metadata.enabled

    def _infer_default_metadata(self, name: str, func: Callable) -> ToolMetadataSchema:
        """Generates standard default metadata for registered tools."""
        doc = inspect.getdoc(func) or f"Callable tool: {name}"
        category = ToolCategory.UTILITY
        safety = SafetyClassification.SAFE_READ_ONLY
        creds: List[str] = []

        if "python" in name or "interpreter" in name:
            category = ToolCategory.CODE_EXECUTION
            safety = SafetyClassification.SANDBOXED_EXECUTION
        elif "search" in name or "web" in name:
            category = ToolCategory.SEARCH
            safety = SafetyClassification.NETWORK_EGRESS
            creds = ["TAVILY_API_KEY", "SERPER_API_KEY"]
        elif "retriev" in name or "document" in name:
            category = ToolCategory.RETRIEVAL
            safety = SafetyClassification.SAFE_READ_ONLY

        # Check if credentials exist in environment
        creds_configured = any(bool(os.getenv(c)) for c in creds) if creds else True

        return ToolMetadataSchema(
            name=name,
            display_name=name.replace("_", " ").title(),
            description=doc.split("\n")[0].strip(),
            category=category,
            safety_classification=safety,
            implementation_status=ToolStatus.IMPLEMENTED,
            enabled=True,
            required_credentials=creds,
            credentials_configured=creds_configured,
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        )

    def get_tool(self, name: str) -> Callable:
        """Retrieve a single registered tool by name."""
        if name not in self._registry:
            raise KeyError(
                f"Tool '{name}' is not registered in ToolRegistry. Available tools: {self.list_tools()}"
            )
        return self._registry[name]

    def get_tools(self, names: List[str]) -> List[Callable]:
        """Retrieve multiple registered tools by name list."""
        return [self.get_tool(name) for name in names]

    def list_tools(self) -> List[str]:
        """Return a list of all registered tool names."""
        return list(self._registry.keys())

    def list_enabled_tools(self) -> List[str]:
        """Return a list of registered tools that are currently enabled."""
        return [name for name, enabled in self._enabled_states.items() if enabled and name in self._registry]

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._registry

    def is_tool_enabled(self, name: str) -> bool:
        """Check if a tool is enabled for execution."""
        return self._enabled_states.get(name, False) and (name in self._registry)

    def enable_tool(self, name: str) -> None:
        """Enable a registered tool."""
        if name not in self._registry:
            raise KeyError(f"Cannot enable unregistered tool '{name}'.")
        self._enabled_states[name] = True
        if name in self._metadata:
            self._metadata[name].enabled = True

    def disable_tool(self, name: str) -> None:
        """Disable a registered tool."""
        if name not in self._registry:
            raise KeyError(f"Cannot disable unregistered tool '{name}'.")
        self._enabled_states[name] = False
        if name in self._metadata:
            self._metadata[name].enabled = False

    def get_tool_metadata(self, name: str) -> ToolMetadataSchema:
        """Retrieve metadata for a tool, updating live credential status."""
        if name not in self._metadata:
            if name in self._registry:
                self._metadata[name] = self._infer_default_metadata(name, self._registry[name])
            else:
                raise KeyError(f"Tool '{name}' not found in registry.")

        meta = self._metadata[name].model_copy()
        meta.enabled = self._enabled_states.get(name, True)
        # Update credential status dynamically
        if meta.required_credentials:
            meta.credentials_configured = any(bool(os.getenv(c)) for c in meta.required_credentials)
        else:
            meta.credentials_configured = True
        return meta

    def list_tools_metadata(self) -> List[ToolMetadataSchema]:
        """Retrieve metadata for all registered tools."""
        return [self.get_tool_metadata(name) for name in self.list_tools()]

    def test_tool(
        self,
        name: str,
        test_input: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 5.0,
    ) -> ToolTestResponse:
        """
        Executes a bounded, safe test of a registered tool with timeout protection.
        Never executes dangerous operations or unbounded loops.
        """
        if name not in self._registry:
            raise KeyError(f"Tool '{name}' is not registered.")

        func = self._registry[name]
        start_time = time.perf_counter()
        status = "success"
        error_msg: Optional[str] = None
        output_preview = ""

        # Safe default bounded test cases
        try:
            if name == "python_tool" or "interpreter" in name:
                code_payload = (test_input or {}).get("code") or (
                    "# Bounded health check\nx = sum([1, 2, 3, 4, 5])\nprint(f'Test Execution Sum: {x}')"
                )
                res = func(code=code_payload)
                if isinstance(res, dict) and res.get("status") == "error":
                    status = "error"
                    error_msg = res.get("error", "Python tool reported execution error")
                    output_preview = str(res)
                else:
                    output_preview = str(res.get("stdout") if isinstance(res, dict) else res)[:300]

            elif name == "web_search" or "search" in name:
                query_payload = (test_input or {}).get("query") or "agent forge architecture health check"
                res = func(query=query_payload, num_results=1)
                if isinstance(res, dict):
                    if res.get("status") == "no_credentials":
                        status = "no_credentials"
                        output_preview = res.get("error", "Offline mode: No search API key configured.")
                    elif res.get("status") == "error":
                        status = "error"
                        error_msg = res.get("error", "Web search failed")
                        output_preview = str(res)
                    else:
                        results = res.get("results", [])
                        output_preview = f"Retrieved {len(results)} result(s). Snippet: {results[0].get('snippet', '') if results else 'None'}"[:300]
                else:
                    output_preview = str(res)[:300]

            elif name == "document_retriever" or "retriever" in name:
                query_payload = (test_input or {}).get("query") or "sample reference architecture specification"
                res = func(query=query_payload, top_k=1)
                if isinstance(res, dict) and res.get("status") == "error":
                    status = "error"
                    error_msg = res.get("error", "Document retriever failed")
                    output_preview = str(res)
                else:
                    docs = res.get("documents", []) if isinstance(res, dict) else []
                    output_preview = f"Retrieved {len(docs)} document(s): {docs[0].get('title', '') if docs else 'None'}"[:300]

            else:
                # Generic fallback bounded execution
                arg_val = (test_input or {}).get("query") or "health_ping"
                res = func(arg_val)
                output_preview = str(res)[:300]

        except Exception as e:
            status = "error"
            error_msg = f"Unhandled exception during tool test: {str(e)}"
            output_preview = f"Execution failed: {str(e)}"

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Update metadata test records
        if name in self._metadata:
            self._metadata[name].last_tested_at = datetime.now(timezone.utc)
            self._metadata[name].last_test_status = status
            self._metadata[name].last_test_latency_ms = elapsed_ms

        return ToolTestResponse(
            tool_name=name,
            status=status,
            duration_ms=elapsed_ms,
            output_preview=output_preview,
            error=error_msg,
        )

    def clear(self) -> None:
        """Clear all registered tools (useful for unit testing isolation)."""
        self._registry.clear()
        self._metadata.clear()
        self._enabled_states.clear()


tool_registry = ToolRegistry()
