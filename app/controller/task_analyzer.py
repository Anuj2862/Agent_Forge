"""
Task Analyzer Subsystem (Owned by Member 1).

Analyzes a natural-language task and converts it into a validated TaskSpec.
"""

import json
from uuid import uuid4

from google import genai

from app.core.config import settings
from app.schemas.task import TaskSpec, Subtask
from app.core.logging import logger


class TaskAnalyzer:
    """Analyzes natural language prompts and produces TaskSpec objects."""

    def __init__(self):
        if settings.GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self.model = settings.GEMINI_MODEL
            except Exception as e:
                logger.warning(f"[TaskAnalyzer] Failed to initialize Gemini client: {e}. Using heuristic analyzer.")
                self.client = None
                self.model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro")
        else:
            self.client = None
            self.model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro")

    def _heuristic_analyze(self, user_prompt: str) -> TaskSpec:
        prompt_lower = user_prompt.lower()
        if any(w in prompt_lower for w in ["research", "investigate", "survey", "find", "ev", "electric vehicle"]):
            task_type = "research"
        elif any(w in prompt_lower for w in ["data", "trend", "sales", "quarterly", "metric"]):
            task_type = "data_analysis"
        elif any(w in prompt_lower for w in ["code", "script", "python", "function", "program", "sort"]):
            task_type = "code_generation"
        elif any(w in prompt_lower for w in ["content", "article", "write", "post"]):
            task_type = "content_creation"
        elif any(w in prompt_lower for w in ["problem", "solve", "debug"]):
            task_type = "problem_solving"
        else:
            task_type = "general"

        word_count = len(user_prompt.split())
        complexity = "high" if word_count > 40 else ("medium" if word_count > 15 else "low")

        subtasks = [
            Subtask(
                id="subtask_1",
                title="Data & Context Retrieval",
                description=f"Gather foundational evidence for: {user_prompt[:80]}",
                required_capabilities=["web_search", "information_retrieval"],
            ),
            Subtask(
                id="subtask_2",
                title="Synthesis & Analysis",
                description="Synthesize findings, verify assertions, and formulate final structured response.",
                required_capabilities=["content_synthesis"],
            ),
        ]

        return TaskSpec(
            task_id=f"task_{uuid4().hex[:10]}",
            user_prompt=user_prompt,
            task_type=task_type,
            complexity=complexity,
            subtasks=subtasks,
            required_capabilities=["web_search", "information_retrieval", "content_synthesis"],
            constraints=[],
            expected_output_format="report",
        )

    def analyze(self, user_prompt: str) -> TaskSpec:
        """
        Analyze a user task using Gemini and return a validated TaskSpec.
        Falls back to transparent heuristic analysis if offline or API key is absent.
        """
        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty.")

        if not self.client:
            return self._heuristic_analyze(user_prompt)

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

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                },
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            result = json.loads(response.text)

            task_spec_data = {
                "task_id": str(uuid4()),
                "user_prompt": user_prompt,
                **result,
            }

            return TaskSpec.model_validate(task_spec_data)
        except Exception as exc:
            logger.warning(
                f"[TaskAnalyzer] Gemini generation failed: {exc}. Falling back to deterministic heuristic analysis."
            )
            return self._heuristic_analyze(user_prompt)
