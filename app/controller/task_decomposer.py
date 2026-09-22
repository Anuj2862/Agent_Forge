"""
Task Decomposer Subsystem (Owned by Member 1).

Decomposes a natural-language task into structured subtasks.
"""

import json

from google import genai

from app.core.config import settings
from app.schemas.task import Subtask


class TaskDecomposer:
    """Decomposes a complex task into structured subtasks."""

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    def decompose(self, prompt: str) -> list[Subtask]:
        """
        Decompose a natural-language task into structured subtasks.
        """

        if not prompt or not prompt.strip():
            raise ValueError("prompt cannot be empty.")

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

        response = self.client.models.generate_content(
            model=self.model,
            contents=decomposition_prompt,
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

        raw_subtasks = result.get("subtasks")

        if not isinstance(raw_subtasks, list):
            raise ValueError(
                "Gemini response must contain a 'subtasks' list."
            )

        try:
            return [
                Subtask.model_validate(subtask)
                for subtask in raw_subtasks
            ]
        except Exception as exc:
            raise ValueError(
                "Gemini returned invalid subtask data."
            ) from exc
