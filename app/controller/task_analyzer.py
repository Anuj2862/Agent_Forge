"""
Task Analyzer Subsystem (Owned by Member 1).
"""

from app.schemas.task import TaskSpec


class TaskAnalyzer:
    """Analyzes natural language prompt to populate TaskSpec."""

    def analyze(self, user_prompt: str) -> TaskSpec:
        raise NotImplementedError("TaskAnalyzer implementation belongs to Member 1 feature branch.")
