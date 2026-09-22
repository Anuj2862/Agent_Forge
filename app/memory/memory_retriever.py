"""
Evolution Memory Retriever — Similarity-Based Retrieval (Member 4).
Retrieves relevant prior architectural experience to guide Meta Controller synthesis.
Exposed as a clean interface callable by Member 1's MetaController.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.task import TaskSpec, TaskType, ComplexityLevel
from app.memory.memory_schema import EvolutionMemoryRecord
from app.memory.memory_store import MemoryStore, EvolutionMemoryORM


class MemoryRetriever:
    """
    Retrieves relevant prior architectural experience based on task similarity.
    
    Similarity is determined by:
    1. Exact match on task_type (highest weight)
    2. Exact match on complexity (secondary weight)
    3. Sorted by success_rating DESC to surface best experiences first
    
    Clean interface for Member 1's MetaController to call before architecture synthesis.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._store = MemoryStore(db)

    async def retrieve_similar_experiences(
        self, task_spec: TaskSpec, limit: int = 3
    ) -> List[EvolutionMemoryRecord]:
        """
        Retrieve the most relevant prior experiences for a given task.

        Strategy:
        - Primary filter: same task_type
        - Secondary filter: same complexity
        - Sort: success_rating DESC
        - Fallback: if no same-type records, return top-rated records overall

        Args:
            task_spec: The TaskSpec to find similar experiences for.
            limit: Maximum number of records to return.

        Returns:
            List of EvolutionMemoryRecord sorted by relevance and success rating.
        """
        task_type_val = (
            task_spec.task_type.value
            if hasattr(task_spec.task_type, "value")
            else str(task_spec.task_type)
        )
        complexity_val = (
            task_spec.complexity.value
            if hasattr(task_spec.complexity, "value")
            else str(task_spec.complexity)
        )

        # --- Tier 1: same task_type + same complexity ---
        tier1_rows = await self._query_records(
            task_type=task_type_val,
            complexity=complexity_val,
            limit=limit,
        )
        if len(tier1_rows) >= limit:
            return tier1_rows[:limit]

        # --- Tier 2: same task_type, any complexity ---
        tier2_rows = await self._query_records(
            task_type=task_type_val,
            complexity=None,
            limit=limit,
        )
        # Merge deduped
        seen_ids = {r.record_id for r in tier1_rows}
        combined = list(tier1_rows)
        for r in tier2_rows:
            if r.record_id not in seen_ids:
                combined.append(r)
                seen_ids.add(r.record_id)
        if len(combined) >= limit:
            return combined[:limit]

        # --- Tier 3: any record, best rated ---
        fallback_rows = await self._query_records(task_type=None, complexity=None, limit=limit)
        for r in fallback_rows:
            if r.record_id not in seen_ids:
                combined.append(r)
                seen_ids.add(r.record_id)

        return combined[:limit]

    async def get_best_architecture_for_task(
        self, task_type: TaskType, complexity: ComplexityLevel
    ) -> Optional[EvolutionMemoryRecord]:
        """
        Return the single highest-rated architectural experience for a task profile.
        Convenience method for Member 1's MetaController.

        Args:
            task_type: Task type enum value.
            complexity: Complexity level enum value.

        Returns:
            Best matching EvolutionMemoryRecord or None if no prior experience exists.
        """
        task_type_val = task_type.value if hasattr(task_type, "value") else str(task_type)
        complexity_val = complexity.value if hasattr(complexity, "value") else str(complexity)

        rows = await self._query_records(
            task_type=task_type_val, complexity=complexity_val, limit=1
        )
        return rows[0] if rows else None

    async def get_evolution_history_for_task(self, task_id: str) -> List[EvolutionMemoryRecord]:
        """
        Return all run iterations for a specific task, ordered by run_number.
        Used for the evolution comparison view in the frontend.
        """
        return await self._store.get_records_for_task(task_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _query_records(
        self,
        task_type: Optional[str],
        complexity: Optional[str],
        limit: int,
    ) -> List[EvolutionMemoryRecord]:
        """Build and execute a filtered + sorted query against the memory table."""
        query = (
            select(EvolutionMemoryORM)
            .order_by(EvolutionMemoryORM.success_rating.desc())
            .limit(limit)
        )
        if task_type:
            query = query.where(EvolutionMemoryORM.task_type == task_type)
        if complexity:
            query = query.where(EvolutionMemoryORM.complexity == complexity)

        result = await self._db.execute(query)
        rows = result.scalars().all()
        return [MemoryStore._orm_to_schema(row) for row in rows]
