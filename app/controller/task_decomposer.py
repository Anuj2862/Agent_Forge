"""
Task Decomposer Subsystem (Owned by Member 1).

Decomposes a natural-language task into structured subtasks.
"""

import json

from google import genai

from app.core.config import settings
from app.schemas.task import Subtask
from app.core.logging import logger


class TaskDecomposer:
    """Decomposes a complex task into structured subtasks."""

    def __init__(self):
        if settings.GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self.model = settings.GEMINI_MODEL
            except Exception as e:
                logger.warning(f"[TaskDecomposer] Failed to initialize Gemini client: {e}. Using heuristic decomposer.")
                self.client = None
                self.model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro")
        else:
            self.client = None
            self.model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro")

    def _heuristic_decompose(self, prompt: str) -> list[Subtask]:
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["research", "investigate", "survey", "ev", "electric vehicle"]):
            return [
                Subtask(
                    id="subtask_1",
                    title="Information Retrieval",
                    description=f"Conduct search and collect verified data for: {prompt[:80]}",
                    required_capabilities=["web_search", "information_retrieval"],
                ),
                Subtask(
                    id="subtask_2",
                    title="Analysis & Report Drafting",
                    description="Analyze collected evidence, verify factual consistency, and draft structured summary.",
                    required_capabilities=["content_synthesis"],
                ),
            ]
        elif any(w in prompt_lower for w in ["data", "trend", "sales", "quarterly"]):
            return [
                Subtask(
                    id="subtask_1",
                    title="Data Ingestion & Cleaning",
                    description="Extract and structure numeric data records for analysis.",
                    required_capabilities=["python_tool", "data_analysis"],
                ),
                Subtask(
                    id="subtask_2",
                    title="Trend Analysis & Modeling",
                    description="Execute mathematical analysis and compute projections.",
                    required_capabilities=["python_tool", "data_analysis"],
                ),
                Subtask(
                    id="subtask_3",
                    title="Executive Summary Generation",
                    description="Formulate structured business report from analytical findings.",
                    required_capabilities=["content_synthesis"],
                ),
            ]
        elif any(w in prompt_lower for w in ["code", "script", "python", "function", "program", "sort"]):
            return [
                Subtask(
                    id="subtask_1",
                    title="Code Generation",
                    description=f"Implement robust code meeting requirements for: {prompt[:80]}",
                    required_capabilities=["python_tool"],
                ),
                Subtask(
                    id="subtask_2",
                    title="Validation & Test Execution",
                    description="Execute and test generated code to verify correctness.",
                    required_capabilities=["python_tool"],
                ),
            ]
        else:
            return [
                Subtask(
                    id="subtask_1",
                    title="Task Analysis & Preparation",
                    description=f"Gather context and establish requirements for: {prompt[:80]}",
                    required_capabilities=["information_retrieval"],
                ),
                Subtask(
                    id="subtask_2",
                    title="Execution & Output Generation",
                    description="Execute primary operations and synthesize final response.",
                    required_capabilities=["content_synthesis"],
                ),
            ]

    def decompose(self, prompt: str) -> list[Subtask]:
        """
        Decompose a natural-language task into structured subtasks.
        Falls back to transparent heuristic decomposition if offline or API key absent.
        """
        if not prompt or not prompt.strip():
            raise ValueError("prompt cannot be empty.")

        if not self.client:
            return self._heuristic_decompose(prompt)

        decomposition_prompt = f"""
You are the Task Decomposer component of an AI agent orchestration system.

Break the following user task into meaningful, executable subtasks.

USER TASK:
{prompt}

Return ONLY valid JSON.

The JSON must contain exactly this structure:

{{
    "subtasks": [
        {{
            "id": "subtask_1",
            "title": "Short title",
            "description": "Detailed description",
            "required_capabilities": [
                "capability_1",
                "capability_2"
            ]
        }}
    ]
}}

Instructions:

1. Break the task into logical subtasks.
2. Each subtask must represent a meaningful unit of work.
3. Order the subtasks in a logical execution order.
4. Give every subtask a unique ID such as subtask_1, subtask_2, etc.
5. Clearly describe what each subtask must accomplish.
6. Identify the capabilities required for each subtask.
7. Do not create unnecessary subtasks.
8. Do not invent requirements that are not supported by the user task.
9. Return only JSON. Do not include Markdown or explanations.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=decomposition_prompt,
                config={
                    "response_mime_type": "application/json",
                },
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            result = json.loads(response.text)
            raw_subtasks = result.get("subtasks")
            if not isinstance(raw_subtasks, list):
                raise ValueError("Gemini response must contain a 'subtasks' list.")

            return [
                Subtask.model_validate(subtask)
                for subtask in raw_subtasks
            ]
        except Exception as exc:
            logger.warning(
                f"[TaskDecomposer] Gemini decomposition failed: {exc}. Falling back to deterministic heuristic decomposition."
            )
            return self._heuristic_decompose(prompt)
