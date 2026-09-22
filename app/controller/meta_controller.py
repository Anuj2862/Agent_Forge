"""
Meta Controller Subsystem (Owned by Member 1).
Responsible for coordinating task understanding, decomposition,
capability extraction, complexity analysis, and architecture synthesis.
"""

from app.controller.architecture_generator import ArchitectureGenerator
from app.controller.capability_extractor import CapabilityExtractor
from app.controller.complexity_analyzer import ComplexityAnalyzer
from app.controller.task_analyzer import TaskAnalyzer
from app.controller.task_decomposer import TaskDecomposer
from app.schemas.architecture import ArchitectureSpec


class MetaController:
    """
    High-level orchestrator for task understanding and
    dynamic architecture synthesis.
    """

    def __init__(self):
        self.task_analyzer = TaskAnalyzer()
        self.task_decomposer = TaskDecomposer()
        self.capability_extractor = CapabilityExtractor()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.architecture_generator = ArchitectureGenerator()

    async def process_task(self, user_prompt: str) -> ArchitectureSpec:
        """
        Process a natural-language task and generate an ArchitectureSpec.

        Pipeline:
        1. Analyze the task.
        2. Decompose the task into subtasks.
        3. Extract required capabilities.
        4. Assess task complexity.
        5. Generate the final architecture.
        """

        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty.")

        # Step 1: Analyze the complete task.
        task_spec = self.task_analyzer.analyze(user_prompt)

        # Step 2: Generate structured subtasks.
        task_spec.subtasks = self.task_decomposer.decompose(user_prompt)

        # Step 3: Extract capabilities for the complete task.
        task_spec.required_capabilities = (
            self.capability_extractor.extract_capabilities(user_prompt)
        )

        # Step 4: Assess complexity using the transparent heuristic analyzer.
        task_spec.complexity = self.complexity_analyzer.assess_complexity(
            user_prompt
        )

        # Step 5: Synthesize the final agent architecture.
        architecture = self.architecture_generator.generate_architecture(
            task_spec
        )

        return architecture
