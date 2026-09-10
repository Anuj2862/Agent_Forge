"""
LLM-Assisted Qualitative Evaluator with Graceful Deterministic Fallback.
Isolates Google Gemini API interactions cleanly behind an explainable interface.
"""

import os
import json
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger


class LLMEvaluator:
    """Provides qualitative text evaluation via Gemini when available, with automatic offline fallback."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name or settings.GEMINI_MODEL or "gemini-1.5-pro"
        self._client = None
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"[LLM_EVALUATOR] Failed to initialize Google GenAI client: {e}. Running in deterministic mode.")

    @property
    def is_available(self) -> bool:
        """Returns True only if LLM client is initialized and configured."""
        return self._client is not None

    def evaluate_quality(
        self, prompt: str, text: str, context: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Requests qualitative evaluation of text from LLM.
        Returns a dict with 'relevance', 'clarity', 'depth', 'feedback' if successful, or None on failure/fallback.
        """
        if not self.is_available:
            return None

        eval_prompt = f"""
You are an expert multi-agent architecture evaluator. Evaluate the following generated output against the user prompt.

USER PROMPT:
{prompt}

CONTEXT/CONSTRAINTS:
{context or "None provided"}

GENERATED OUTPUT:
{text}

Provide your evaluation strictly as a valid JSON object with the following fields:
{{
    "relevance": <float between 0.0 and 1.0>,
    "clarity": <float between 0.0 and 1.0>,
    "depth": <float between 0.0 and 1.0>,
    "feedback": "<concise summary of quality, strengths, and deficiencies>"
}}
Do NOT include markdown formatting or backticks around the JSON.
"""
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=eval_prompt,
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()

            parsed = json.loads(raw_text)
            return {
                "relevance": float(parsed.get("relevance", 0.7)),
                "clarity": float(parsed.get("clarity", 0.7)),
                "depth": float(parsed.get("depth", 0.7)),
                "feedback": str(parsed.get("feedback", "LLM qualitative evaluation completed.")),
            }
        except Exception as e:
            logger.info(f"[LLM_EVALUATOR] LLM evaluation unavailable or failed: {e}. Falling back to deterministic heuristics.")
            return None
