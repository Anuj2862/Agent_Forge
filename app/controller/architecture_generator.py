"""
Architecture Generator Subsystem (Owned by Member 1).
"""

from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec


class ArchitectureGenerator:
    """Synthesizes an ArchitectureSpec dynamically from a TaskSpec."""

    def generate_architecture(self, task_spec: TaskSpec) -> ArchitectureSpec:
        raise NotImplementedError("ArchitectureGenerator implementation belongs to Member 1 feature branch.")
