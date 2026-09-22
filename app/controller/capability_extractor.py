"""
Capability Extractor Subsystem (Owned by Member 1).

Extracts the capabilities/tools required to complete a task.
"""

import json
from typing import List

from google import genai

from app.core.config import settings


class CapabilityExtractor:
    """Extracts required agent capabilities from a natural-language task."""

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    def extract_capabilities(self, prompt: str) -> List[str]:
        """
        Extract the capabilities/tools required to complete a task.
        """

        if not prompt or not prompt.strip():
            raise ValueError("prompt cannot be empty.")

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

        response = self.client.models.generate_content(
            model=self.model,
            contents=extraction_prompt,
            config={
                "response_mime_type": "application/json",
            },
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        try:
            result = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned invalid JSON."
            ) from exc

        capabilities = result.get("capabilities")

        if not isinstance(capabilities, list):
            raise ValueError(
                "Gemini response must contain a 'capabilities' list."
            )

        cleaned_capabilities = []

        for capability in capabilities:
            if not isinstance(capability, str):
                raise ValueError(
                    "Each capability must be a string."
                )

            capability = capability.strip().lower()

            if capability and capability not in cleaned_capabilities:
                cleaned_capabilities.append(capability)

        return cleaned_capabilities
