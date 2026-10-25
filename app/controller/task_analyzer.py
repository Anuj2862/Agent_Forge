"""
Task Analyzer Subsystem (Owned by Member 1).
Analyzes natural-language tasks, extracts explicit operational constraints,
and converts them into validated TaskSpec objects.
"""

import json
import re
from uuid import uuid4
from typing import Optional, Dict, Any, List

from google import genai

from app.core.config import settings
from app.schemas.task import TaskSpec, Subtask, TaskConstraints
from app.core.logging import logger


class TaskAnalyzer:
    """Analyzes natural language prompts, extracts constraints, and produces TaskSpec objects."""

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

    @staticmethod
    def extract_nl_constraints(user_prompt: str) -> Dict[str, Any]:
        """Extracts deterministic operational constraints from prompt text."""
        prompt_lower = user_prompt.lower()
        extracted: Dict[str, Any] = {}

        # 1. max_agents
        m = re.search(
            r"(?:max_agents\s*[:=]\s*|maximum\s+|max\s+|no\s+more\s+than\s+|at\s+most\s+)(\d+)\s*agents?",
            prompt_lower,
        )
        if m:
            extracted["max_agents"] = int(m.group(1))

        # 2. forbidden_tools
        forbidden = []
        if any(t in prompt_lower for t in ["no web search", "without web search", "do not use web search", "disallow web search"]):
            forbidden.append("web_search")
            forbidden.append("web_search_tool")
        if any(t in prompt_lower for t in ["no code execution", "no python", "do not run code", "prohibit code execution", "disallow python"]):
            forbidden.append("python_tool")
            forbidden.append("python_interpreter")
        if forbidden:
            extracted["forbidden_tools"] = list(set(forbidden))

        # 3. require_verification
        if any(t in prompt_lower for t in ["require fact verification", "require verification", "must be verified", "independent verification", "verified report"]):
            extracted["require_verification"] = True

        return extracted

    def _heuristic_analyze(
        self,
        user_prompt: str,
        structured_constraints: Optional[Dict[str, Any]] = None,
    ) -> TaskSpec:
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

        # Merge natural language and structured constraints
        nl_constraints = self.extract_nl_constraints(user_prompt)
        merged_constraints_dict = {**nl_constraints, **(structured_constraints or {})}

        constraints_list: List[str] = []
        max_agents = merged_constraints_dict.get("max_agents")
        if max_agents is not None:
            constraints_list.append(f"max_agents={max_agents}")

        forbidden_tools = merged_constraints_dict.get("forbidden_tools") or []
        for ft in forbidden_tools:
            constraints_list.append(f"forbidden_tool:{ft}")

        require_verification = bool(merged_constraints_dict.get("require_verification", False))
        if require_verification:
            constraints_list.append("require_verification=True")

        raw_constraints = merged_constraints_dict.get("constraints") or []
        if isinstance(raw_constraints, list):
            constraints_list.extend(raw_constraints)

        task_constraints = TaskConstraints(
            max_agents=max_agents,
            forbidden_tools=forbidden_tools,
            allowed_tools=merged_constraints_dict.get("allowed_tools") or [],
            require_verification=require_verification,
            max_execution_time_seconds=merged_constraints_dict.get("max_execution_time_seconds"),
            constraints=list(set(constraints_list)),
        )

        return TaskSpec(
            task_id=f"task_{uuid4().hex[:10]}",
            user_prompt=user_prompt,
            task_type=task_type,
            complexity=complexity,
            subtasks=subtasks,
            required_capabilities=["web_search", "information_retrieval", "content_synthesis"],
            constraints=task_constraints,
            expected_output_format="report",
            max_agents=max_agents,
            forbidden_tools=forbidden_tools,
            allowed_tools=merged_constraints_dict.get("allowed_tools") or [],
            require_verification=require_verification,
            max_execution_time_seconds=merged_constraints_dict.get("max_execution_time_seconds"),
        )

    def analyze(
        self,
        user_prompt: str,
        structured_constraints: Optional[Dict[str, Any]] = None,
    ) -> TaskSpec:
        """
        Analyze a user task using Gemini and return a validated TaskSpec.
        Falls back to transparent heuristic analysis if offline or API key is absent.
        """
        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty.")

        if not self.client:
            return self._heuristic_analyze(user_prompt, structured_constraints)

        prompt = f"""
You are the Task Analyzer component of an AI agent orchestration system.

Analyze the following user task and convert it into structured task information.

USER TASK:
{user_prompt}

Return ONLY valid JSON with fields:
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
    "expected_output_format": "string or null",
    "max_agents": "integer or null",
    "forbidden_tools": ["string"],
    "require_verification": false
}}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            result = json.loads(response.text)

            # Overlay structured constraints
            nl_constraints = self.extract_nl_constraints(user_prompt)
            combined_constraints = {**nl_constraints, **(structured_constraints or {})}

            task_spec_data = {
                "task_id": f"task_{uuid4().hex[:10]}",
                "user_prompt": user_prompt,
                **result,
            }

            for k, v in combined_constraints.items():
                if v is not None:
                    task_spec_data[k] = v

            return TaskSpec.model_validate(task_spec_data)
        except Exception as exc:
            logger.warning(
                f"[TaskAnalyzer] Gemini generation failed: {exc}. Falling back to deterministic heuristic analysis."
            )
            return self._heuristic_analyze(user_prompt, structured_constraints)
