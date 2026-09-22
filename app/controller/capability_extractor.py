"""
Capability Extractor Subsystem (Owned by Member 1).

Extracts the capabilities/tools required to complete a task.
"""

import json
from typing import List

from google import genai

from app.core.config import settings
from app.core.logging import logger


class CapabilityExtractor:
    """Extracts required agent capabilities from a natural-language task."""

    def __init__(self):
        if settings.GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self.model = settings.GEMINI_MODEL
            except Exception as e:
                logger.warning(f"[CapabilityExtractor] Failed to initialize Gemini client: {e}. Using heuristic extractor.")
                self.client = None
                self.model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro")
        else:
            self.client = None
            self.model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro")

    def _heuristic_extract(self, prompt: str) -> List[str]:
        prompt_lower = prompt.lower()
        capabilities: List[str] = []
        if any(w in prompt_lower for w in ["search", "research", "find", "ev", "electric vehicle", "web"]):
            capabilities.append("web_search")
            capabilities.append("information_retrieval")
        if any(w in prompt_lower for w in ["data", "trend", "sales", "quarterly", "metric", "calc", "python", "code", "script"]):
            capabilities.append("python_tool")
            capabilities.append("data_analysis")
        if any(w in prompt_lower for w in ["doc", "pdf", "file", "document"]):
            capabilities.append("document_retriever")
        if any(w in prompt_lower for w in ["write", "report", "summar", "synthes", "format"]):
            capabilities.append("content_synthesis")
        if not capabilities:
            capabilities = ["web_search", "content_synthesis"]
        return capabilities

    def extract_capabilities(self, prompt: str) -> List[str]:
        """
        Extract the capabilities/tools required to complete a task.
        Falls back to transparent heuristic extraction if offline or API key absent.
        """
        if not prompt or not prompt.strip():
            raise ValueError("prompt cannot be empty.")

        if not self.client:
            return self._heuristic_extract(prompt)

        extraction_prompt = f"""
You are the Capability Extractor component of an AI agent
orchestration system.

Identify the capabilities and tools required to complete the
following task.

USER TASK:
{prompt}

Return ONLY valid JSON using exactly this structure:

{{
    "capabilities": [
        "capability_1",
        "capability_2"
    ]
}}

Instructions:

1. Identify the concrete capabilities required to complete the task.
2. Include tools or abilities that an AI agent would need.
3. Use concise, reusable capability names.
4. Prefer names such as:
   - web_search
   - information_retrieval
   - data_analysis
   - csv_parsing
   - data_aggregation
   - data_visualization
   - python_execution
   - code_generation
   - code_analysis
   - text_generation
   - summarization
   - document_generation
   - database_query
5. Do not include capabilities that are unrelated to the task.
6. Avoid duplicate capabilities.
7. Return only the JSON object.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=extraction_prompt,
                config={
                    "response_mime_type": "application/json",
                },
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            result = json.loads(response.text)
            capabilities = result.get("capabilities")

            if not isinstance(capabilities, list):
                raise ValueError("Gemini response must contain a 'capabilities' list.")

            cleaned_capabilities = []
            for capability in capabilities:
                if isinstance(capability, str):
                    capability = capability.strip().lower()
                    if capability and capability not in cleaned_capabilities:
                        cleaned_capabilities.append(capability)

            return cleaned_capabilities or self._heuristic_extract(prompt)
        except Exception as exc:
            logger.warning(
                f"[CapabilityExtractor] Gemini extraction failed: {exc}. Falling back to deterministic heuristic extraction."
            )
            return self._heuristic_extract(prompt)
