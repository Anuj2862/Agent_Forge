"""
Web Search Tool Primitive (Owned by Member 2).
Provides web search capabilities with real HTTP API path support and graceful offline test fallback.
"""

import os
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings


def web_search_tool(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Executes a web search query.

    If a search API key (e.g., TAVILY_API_KEY, SERPER_API_KEY) is configured,
    performs a real HTTP search request. Otherwise, returns a clean, structured
    offline response indicating no API key is configured.

    Args:
        query: Search query string.
        num_results: Number of search results to request.

    Returns:
        Structured result dict with status, query, results, and error fields.
    """
    if not isinstance(query, str) or not query.strip():
        return {
            "status": "error",
            "query": query,
            "results": [],
            "error": "Search query must be a non-empty string.",
        }

    api_key = os.getenv("TAVILY_API_KEY") or os.getenv("SERPER_API_KEY") or getattr(settings, "SEARCH_API_KEY", None)

    if not api_key:
        return {
            "status": "no_credentials",
            "query": query,
            "results": [
                {
                    "title": f"Offline Result for '{query}'",
                    "snippet": f"No external search API key configured (TAVILY_API_KEY/SERPER_API_KEY). Query: {query}",
                    "url": "https://example.com/offline-search",
                }
            ],
            "error": "No SEARCH_API_KEY or TAVILY_API_KEY configured in environment.",
        }

    # If Tavily API Key is present
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            response = httpx.post(
                "https://api.tavily.com/search",
                json={"api_key": tavily_key, "query": query, "max_results": num_results},
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            results = [
                {
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "url": item.get("url", ""),
                }
                for item in data.get("results", [])
            ]
            return {
                "status": "success",
                "query": query,
                "results": results,
                "error": None,
            }
        except Exception as e:
            return {
                "status": "error",
                "query": query,
                "results": [],
                "error": f"Search API HTTP error: {str(e)}",
            }

    return {
        "status": "no_credentials",
        "query": query,
        "results": [],
        "error": "Unconfigured search provider.",
    }
