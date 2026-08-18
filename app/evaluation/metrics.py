"""
Metrics Calculator (Owned by Member 3).
"""

from app.schemas.evaluation import EvaluationMetrics


class MetricsCalculator:
    def compute(self, raw_output: str, time_taken: float, agent_count: int) -> EvaluationMetrics:
        raise NotImplementedError("MetricsCalculator belongs to Member 3 feature branch.")
