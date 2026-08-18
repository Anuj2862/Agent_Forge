"""
Task Decomposer Subsystem (Owned by Member 1).
"""

from typing import List
from app.schemas.task import Subtask


class TaskDecomposer:
    """Decomposes a complex task objective into structured subtasks."""

    def decompose(self, prompt: str) -> List[Subtask]:
        raise NotImplementedError("TaskDecomposer implementation belongs to Member 1 feature branch.")
