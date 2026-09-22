"""
Task Analyzer Subsystem (Owned by Member 1).

Analyzes a natural-language task and converts it into a validated TaskSpec.
"""

import json
from uuid import uuid4

from google import genai

from app.core.config import settings
from app.schemas.task import TaskSpec


class TaskAnalyzer:
    """Analyzes natural language prompts and produces TaskSpec objects."""

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    def analyze(self, user_prompt: str) -> TaskSpec:
        """
        Analyze a user task using Gemini and return a validated TaskSpec.
        """

        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty.")

        prompt = f"""
You are the Task Analyzer component of an AI agent orchestration system.

Analyze the following user task and convert it into structured task information.

USER TASK:
{user_prompt}

Return ONLY valid JSON.

The JSON must contain these fields:

{{
    "task_type": "research | data_analysis | code_generation | content_creation | problem_solving | general",
    "complexity": "low | medium | high | very_high",
    "subtasks": [
        {{
            "id": "string",
            "title": "string",
            "description": "string",
            "required_capabilities": ["string"]
        }}
    ],
    "required_capabilities": ["string"],
    "constraints": ["string"],
    "expected_output_format": "string or null"
}}

Instructions:

1. Identify the main type of task.
2. Estimate complexity based on the number of steps,
   dependencies, reasoning requirements, and technical difficulty.
3. Break the task into meaningful subtasks.
4. Identify capabilities required to complete the task.
5. Extract explicit constraints from the user request.
6. Identify the expected output format.
7. Do not invent constraints that are not implied by the task.
8. Keep the output concise and structured.
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
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

        task_spec_data = {
            "task_id": str(uuid4()),
            "user_prompt": user_prompt,
            **result,
        }

        return TaskSpec.model_validate(task_spec_data)
