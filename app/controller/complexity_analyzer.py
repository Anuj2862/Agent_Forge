"""
Complexity Analyzer Subsystem (Owned by Member 1).

Estimates task complexity using transparent heuristics.
"""

import re

from app.schemas.task import ComplexityLevel


class ComplexityAnalyzer:
    """Evaluates task prompts and assigns a ComplexityLevel."""

    def assess_complexity(self, prompt: str) -> ComplexityLevel:
        """
        Estimate task complexity using transparent heuristic signals.
        """

        if not prompt or not prompt.strip():
            raise ValueError("prompt cannot be empty.")

        text = prompt.lower().strip()
        score = 0

        # ---------------------------------------------------------
        # 1. Task length
        # ---------------------------------------------------------
        word_count = len(text.split())

        if word_count > 150:
            score += 4
        elif word_count > 80:
            score += 3
        elif word_count > 40:
            score += 2
        elif word_count > 20:
            score += 1

        # ---------------------------------------------------------
        # 2. Multi-step indicators
        # ---------------------------------------------------------
        step_indicators = [
            "first",
            "then",
            "next",
            "finally",
            "after that",
            "step",
            "pipeline",
            "workflow",
        ]

        step_matches = sum(
            1 for indicator in step_indicators
            if indicator in text
        )

        score += min(step_matches * 2, 6)

        # ---------------------------------------------------------
        # 3. Technical / computational indicators
        # ---------------------------------------------------------
        technical_terms = [
            "code",
            "algorithm",
            "api",
            "database",
            "machine learning",
            "deep learning",
            "model",
            "train",
            "deploy",
            "docker",
            "cloud",
            "architecture",
            "system",
            "integration",
        ]

        technical_matches = sum(
            1 for term in technical_terms
            if term in text
        )

        score += min(technical_matches * 2, 8)

        # ---------------------------------------------------------
        # 4. Reasoning / analysis indicators
        # ---------------------------------------------------------
        reasoning_terms = [
            "research",
            "analyze",
            "compare",
            "evaluate",
            "investigate",
            "optimize",
            "validate",
            "verify",
            "predict",
        ]

        reasoning_matches = sum(
            1 for term in reasoning_terms
            if term in text
        )

        score += min(reasoning_matches * 2, 8)

        # ---------------------------------------------------------
        # 5. Data-processing indicators
        # ---------------------------------------------------------
        data_terms = [
            "csv",
            "dataset",
            "data",
            "revenue",
            "sort",
            "filter",
            "aggregate",
            "calculate",
            "statistics",
        ]

        data_matches = sum(
            1 for term in data_terms
            if term in text
        )

        score += min(data_matches, 5)

        # ---------------------------------------------------------
        # 6. Output requirements
        # ---------------------------------------------------------
        output_indicators = [
            "report",
            "table",
            "chart",
            "summary",
            "recommendations",
            "documentation",
            "dashboard",
        ]

        output_matches = sum(
            1 for term in output_indicators
            if term in text
        )

        if output_matches >= 3:
            score += 4
        elif output_matches >= 2:
            score += 3
        elif output_matches >= 1:
            score += 1

        # ---------------------------------------------------------
        # 7. Explicit numbered steps
        # ---------------------------------------------------------
        numbered_steps = re.findall(
            r"(?:^|\s)(?:\d+[\.\)]|step\s+\d+)",
            text,
        )

        if len(numbered_steps) >= 4:
            score += 5
        elif len(numbered_steps) >= 2:
            score += 3

        # ---------------------------------------------------------
        # 8. Multiple requested actions
        # ---------------------------------------------------------
        action_terms = [
            "and",
            "also",
            "then",
            "after",
            "before",
        ]

        action_count = sum(
            text.count(term)
            for term in action_terms
        )

        if action_count >= 6:
            score += 3
        elif action_count >= 3:
            score += 2

        # ---------------------------------------------------------
        # Final classification
        # ---------------------------------------------------------
        if score <= 4:
            return ComplexityLevel.LOW

        if score <= 9:
            return ComplexityLevel.MEDIUM

        if score <= 14:
            return ComplexityLevel.HIGH

        return ComplexityLevel.VERY_HIGH
