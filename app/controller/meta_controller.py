from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.controller.architecture_generator import ArchitectureGenerator
from app.controller.capability_extractor import CapabilityExtractor
from app.controller.complexity_analyzer import ComplexityAnalyzer
from app.controller.task_analyzer import TaskAnalyzer
from app.controller.task_decomposer import TaskDecomposer
from app.schemas.architecture import ArchitectureSpec
from app.schemas.task import TaskSpec, TaskConstraints
from app.core.logging import logger


class MetaController:
    """
    High-level orchestrator for task understanding, memory-informed reasoning,
    and dynamic architecture synthesis.
    """

    def __init__(self):
        self.task_analyzer = TaskAnalyzer()
        self.task_decomposer = TaskDecomposer()
        self.capability_extractor = CapabilityExtractor()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.architecture_generator = ArchitectureGenerator()

    async def process_task_with_spec(
        self,
        user_prompt: str,
        structured_constraints: Optional[Any] = None,
        db: Optional[AsyncSession] = None,
    ) -> tuple[TaskSpec, ArchitectureSpec]:
        """
        Process a natural-language task and return both TaskSpec and synthesized ArchitectureSpec.

        Pipeline:
        1. Analyze the task -> TaskSpec (incorporating natural language and structured constraints).
        2. Decompose the task into structured subtasks.
        3. Extract required capabilities.
        4. Assess task complexity.
        5. Retrieve relevant historical evolution memory if DB session available.
        6. Generate the final ArchitectureSpec.
        """
        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty.")

        # Step 1: Analyze the complete task with constraints
        if structured_constraints is not None:
            task_spec = self.task_analyzer.analyze(
                user_prompt,
                structured_constraints=structured_constraints,
            )
        else:
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

        # Step 5: Active evolutionary memory retrieval if database is connected
        if db is not None:
            try:
                from app.memory.memory_retriever import MemoryRetriever
                retriever = MemoryRetriever(db)
                memories = await retriever.retrieve_similar_experiences(task_spec, limit=2)
                if memories:
                    task_spec.metadata["retrieved_memories"] = [
                        {
                            "record_id": m.record_id,
                            "run_number": m.run_number,
                            "success_rating": m.success_rating,
                            "topology": m.topology,
                            "recommendation_summary": m.recommendation_summary,
                        }
                        for m in memories
                    ]
                    logger.info(
                        f"[META_CONTROLLER] Retrieved {len(memories)} prior experience(s) to guide architecture synthesis."
                    )
            except Exception as ex:
                logger.warning(f"[META_CONTROLLER] Memory retrieval skipped due to exception: {ex}")

        # Step 6: Synthesize the final agent architecture.
        architecture = self.architecture_generator.generate_architecture(
            task_spec
        )

        return task_spec, architecture

    async def process_task(self, user_prompt: str) -> ArchitectureSpec:
        """
        Process a natural-language task and generate an ArchitectureSpec.
        Maintains backward compatibility with callers expecting only ArchitectureSpec.
        """
        _, architecture = await self.process_task_with_spec(user_prompt)
        return architecture
