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
    Retrieves relevant prior architectural experience based on task similarity and semantic embeddings.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._store = MemoryStore(db)

    @staticmethod
    def _extract_feature_vector(text: str) -> dict[str, float]:
        """Convert a text string into a normalized term-frequency feature vector."""
        import re
        import math
        from collections import Counter

        stopwords = {
            "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
            "is", "was", "are", "were", "of", "by", "that", "this", "it", "as",
            "from", "into", "task", "agent", "run", "produce", "generate",
        }
        tokens = [
            w.lower()
            for w in re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text)
            if w.lower() not in stopwords
        ]
        if not tokens:
            return {}

        counts = Counter(tokens)
        norm = math.sqrt(sum(c * c for c in counts.values()))
        if norm == 0:
            return {}
        return {term: count / norm for term, count in counts.items()}

    @classmethod
    def compute_semantic_similarity(
        cls,
        task_spec: TaskSpec,
        record: EvolutionMemoryRecord,
    ) -> float:
        """
        Compute cosine similarity between incoming TaskSpec and a historical memory record.
        Incorporates user prompt, subtask objectives, and required capabilities.
        """
        # Build query text
        query_parts = [task_spec.user_prompt or ""]
        if task_spec.subtasks:
            query_parts.extend(f"{st.title} {st.description}" for st in task_spec.subtasks)
        if task_spec.required_capabilities:
            query_parts.extend(task_spec.required_capabilities)
        query_text = " ".join(query_parts)

        # Build candidate record text
        record_parts = []
        if record.task_spec:
            record_parts.append(record.task_spec.user_prompt or "")
            if record.task_spec.subtasks:
                record_parts.extend(f"{st.title} {st.description}" for st in record.task_spec.subtasks)
            if record.task_spec.required_capabilities:
                record_parts.extend(record.task_spec.required_capabilities)
        if record.recommendation_summary:
            record_parts.append(record.recommendation_summary)

        record_text = " ".join(record_parts)

        v1 = cls._extract_feature_vector(query_text)
        v2 = cls._extract_feature_vector(record_text)

        if not v1 or not v2:
            return 0.1  # baseline neutral similarity

        # Cosine dot product of normalized vectors
        shared_terms = set(v1.keys()) & set(v2.keys())
        cosine_sim = sum(v1[term] * v2[term] for term in shared_terms)
        return max(0.0, min(1.0, float(cosine_sim)))

    async def retrieve_similar_experiences(
        self, task_spec: TaskSpec, limit: int = 3
    ) -> List[EvolutionMemoryRecord]:
        """
        Retrieve the most relevant prior experiences for a given task.

        Strategy:
        - Primary filter: same task_type
        - Secondary filter: same complexity
        - Sort: composite score combining success_rating and semantic similarity
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
            limit=limit * 2,
        )

        seen_ids = {r.record_id for r in tier1_rows}
        combined = list(tier1_rows)

        if len(combined) < limit:
            # --- Tier 2: same task_type, any complexity ---
            tier2_rows = await self._query_records(
                task_type=task_type_val,
                complexity=None,
                limit=limit * 2,
            )
            for r in tier2_rows:
                if r.record_id not in seen_ids:
                    combined.append(r)
                    seen_ids.add(r.record_id)

        if len(combined) < limit:
            # --- Tier 3: any record, best rated ---
            fallback_rows = await self._query_records(task_type=None, complexity=None, limit=limit * 2)
            for r in fallback_rows:
                if r.record_id not in seen_ids:
                    combined.append(r)
                    seen_ids.add(r.record_id)

        # Annotate records with semantic similarity score for transparency
        for r in combined:
            sim = self.compute_semantic_similarity(task_spec, r)
            if hasattr(r, "task_spec") and r.task_spec and hasattr(r.task_spec, "metadata"):
                r.task_spec.metadata["semantic_similarity"] = round(sim, 3)

        # Sort primarily by success_rating descending (preserving established unit tests contract)
        # while using semantic similarity as tie-breaker/ranking boost
        combined.sort(key=lambda r: (r.success_rating, self.compute_semantic_similarity(task_spec, r)), reverse=True)
        return combined[:limit]

    async def retrieve_semantic_experiences(
        self, task_spec: TaskSpec, min_similarity: float = 0.1, limit: int = 3
    ) -> List[EvolutionMemoryRecord]:
        """
        Retrieve prior experiences purely by semantic vector similarity,
        transcending rigid enum categories.
        """
        all_records = await self._query_records(task_type=None, complexity=None, limit=50)
        scored: list[tuple[float, EvolutionMemoryRecord]] = []

        for rec in all_records:
            sim = self.compute_semantic_similarity(task_spec, rec)
            if sim >= min_similarity:
                composite = (0.6 * sim) + (0.4 * (rec.success_rating or 0.0))
                scored.append((composite, rec))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]


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
