"""
Quality Scorer and Composite Overall Score Calculator for Agent Forge.
Evaluates textual quality (relevance, clarity, consistency, structure, usefulness)
using deterministic heuristics and optional LLM review, and calculates weighted overall scores.
"""

import re
from typing import Dict, Any, Optional, Tuple
from app.evaluation.llm_evaluator import LLMEvaluator
from app.schemas.evaluation import EvaluationMetrics
from app.core.logging import logger


class QualityScorer:
    """Evaluates output quality and computes documented overall scores."""

    # Documented default scoring weights
    DEFAULT_WEIGHTS = {
        "task_success": 0.30,
        "quality": 0.25,
        "accuracy": 0.25,
        "completeness": 0.20,
    }

    def __init__(self, llm_evaluator: Optional[LLMEvaluator] = None, custom_weights: Optional[Dict[str, float]] = None):
        self.llm_evaluator = llm_evaluator or LLMEvaluator()
        self.weights = custom_weights or self.DEFAULT_WEIGHTS.copy()
        self._normalize_weights()

    def _normalize_weights(self) -> None:
        """Ensures the core scoring weights sum precisely to 1.0."""
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def score_output(
        self,
        text: str,
        user_prompt: Optional[str] = None,
        context: Optional[str] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculates output quality score using deterministic heuristics and optional LLM review.
        Returns: (quality_score in [0.0, 1.0], breakdown dictionary)
        """
        if not text or not text.strip():
            return 0.0, {"heuristic_score": 0.0, "reason": "Empty output"}

        clean_text = text.strip()

        # 1. Relevance Score
        relevance_score = self._compute_relevance(clean_text, user_prompt)

        # 2. Structural Completeness & Formatting
        structure_score = self._compute_structure(clean_text)

        # 3. Clarity & Readability
        clarity_score = self._compute_clarity(clean_text)

        # 4. Usefulness & Substance
        usefulness_score = self._compute_usefulness(clean_text)

        # 5. Consistency & Error Absence
        consistency_score = self._compute_consistency(clean_text)

        # Composite deterministic score
        # Relevance: 30%, Substance/Usefulness: 25%, Structure: 20%, Clarity: 15%, Consistency: 10%
        deterministic_score = (
            (0.30 * relevance_score)
            + (0.25 * usefulness_score)
            + (0.20 * structure_score)
            + (0.15 * clarity_score)
            + (0.10 * consistency_score)
        )
        deterministic_score = max(0.0, min(1.0, deterministic_score))

        breakdown = {
            "relevance": round(relevance_score, 4),
            "usefulness": round(usefulness_score, 4),
            "structure": round(structure_score, 4),
            "clarity": round(clarity_score, 4),
            "consistency": round(consistency_score, 4),
            "deterministic_score": round(deterministic_score, 4),
            "llm_evaluated": False,
        }

        # Optional LLM blending if available
        if self.llm_evaluator and self.llm_evaluator.is_available and user_prompt:
            llm_result = self.llm_evaluator.evaluate_quality(user_prompt, clean_text, context)
            if llm_result:
                llm_score = (
                    (0.40 * llm_result["relevance"])
                    + (0.35 * llm_result["depth"])
                    + (0.25 * llm_result["clarity"])
                )
                final_score = (0.50 * deterministic_score) + (0.50 * llm_score)
                breakdown["llm_score"] = round(llm_score, 4)
                breakdown["llm_feedback"] = llm_result["feedback"]
                breakdown["llm_evaluated"] = True
                return round(final_score, 4), breakdown

        return round(deterministic_score, 4), breakdown

    def _compute_relevance(self, text: str, user_prompt: Optional[str]) -> float:
        """Measures keyword overlap and prompt alignment."""
        if not user_prompt:
            return 0.80

        # Extract informative prompt tokens (>3 chars, ignore common stopwords)
        stopwords = {"what", "when", "where", "which", "with", "from", "that", "this", "these", "those", "about", "produce", "report"}
        tokens = [w.lower() for w in re.findall(r"\b\w+\b", user_prompt) if len(w) > 3 and w.lower() not in stopwords]
        if not tokens:
            return 0.80

        text_lower = text.lower()
        matched = sum(1 for token in set(tokens) if token in text_lower)
        coverage = matched / len(set(tokens))
        return min(1.0, 0.4 + (0.6 * coverage))

    def _compute_structure(self, text: str) -> float:
        """Evaluates presence of structured formatting: headings, bullet points, sections."""
        score = 0.4
        # Check for headings (# Heading or bold headers)
        if re.search(r"^#{1,4}\s+\w+", text, re.MULTILINE) or re.search(r"\*\*[A-Z][\w\s]+\*\*:", text):
            score += 0.3
        # Check for lists / bullets
        if re.search(r"^\s*[-*•]\s+", text, re.MULTILINE) or re.search(r"^\s*\d+\.\s+", text, re.MULTILINE):
            score += 0.2
        # Check for conclusion / summary
        if any(term in text.lower() for term in ["summary", "conclusion", "key findings", "recommendations"]):
            score += 0.1
        return min(1.0, score)

    def _compute_clarity(self, text: str) -> float:
        """Evaluates readability, sentence lengths, and flow."""
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 0]
        if not sentences:
            return 0.2

        # Average words per sentence
        avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
        # Optimal sentence length is 10 - 25 words
        if 8 <= avg_words <= 30:
            clarity = 0.95
        elif 5 <= avg_words < 8 or 30 < avg_words <= 45:
            clarity = 0.75
        else:
            clarity = 0.50

        # Check for repetitive loops (same line printed > 3 times)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) > len(set(lines)) + 4:
            clarity -= 0.30

        return max(0.1, min(1.0, clarity))

    def _compute_usefulness(self, text: str) -> float:
        """Evaluates substance, length, and absence of placeholder text."""
        length = len(text.strip())
        if length > 800:
            substance = 1.0
        elif length > 400:
            substance = 0.85
        elif length > 150:
            substance = 0.65
        elif length > 50:
            substance = 0.40
        else:
            substance = 0.15

        # Penalize placeholder tokens
        placeholder_tokens = ["todo", "lorem ipsum", "[insert", "<insert", "placeholder", "tbd"]
        for p in placeholder_tokens:
            if p in text.lower():
                substance -= 0.25

        return max(0.0, min(1.0, substance))

    def _compute_consistency(self, text: str) -> float:
        """Checks for direct self-contradictions and obvious hallucination indicators."""
        score = 1.0
        text_lower = text.lower()
        # Direct conflicting declarations
        if "is completely safe" in text_lower and "is extremely dangerous" in text_lower:
            score -= 0.40
        if "no evidence exists" in text_lower and "numerous studies have proven" in text_lower:
            score -= 0.40
        return max(0.2, score)

    def compute_overall_score(
        self,
        metrics: EvaluationMetrics,
        cost_efficiency_weight: float = 0.05,
    ) -> float:
        """
        Calculates documented composite overall score:
        Overall = w_success * TaskSuccess
                + w_quality * Quality
                + w_accuracy * Accuracy
                + w_completeness * Completeness
                + cost_efficiency_adjustment

        Weights:
        - Task Success: 30%
        - Quality: 25%
        - Accuracy: 25%
        - Completeness: 20%
        - Cost Efficiency Modulation: up to +/- 5%
        """
        acc = metrics.accuracy if metrics.accuracy is not None else 0.50
        base_score = (
            (self.weights["task_success"] * metrics.task_success)
            + (self.weights["quality"] * metrics.quality)
            + (self.weights["accuracy"] * acc)
            + (self.weights["completeness"] * metrics.completeness)
        )

        # Modulate by cost efficiency
        if metrics.cost_efficiency is not None:
            # Shift from centered 0.70 baseline: (cost_efficiency - 0.70) * weight
            adjustment = (metrics.cost_efficiency - 0.70) * cost_efficiency_weight
            overall = base_score + adjustment
        else:
            overall = base_score

        overall = max(0.0, min(1.0, overall))
        return round(overall, 4)
