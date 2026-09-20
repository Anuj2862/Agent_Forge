"""
Evolution Memory Store — Full PostgreSQL/SQLite Implementation (Member 4).
Persists TaskSpec → Architecture → Evaluation → Reflection → Recommendation records.
"""

import json
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.database import Base
from app.memory.memory_schema import EvolutionMemoryRecord
from app.schemas.task import TaskType, ComplexityLevel


# ---------------------------------------------------------------------------
# ORM Model
# ---------------------------------------------------------------------------

class EvolutionMemoryORM(Base):
    """SQLAlchemy ORM table for evolution memory records."""

    __tablename__ = "evolution_memory"

    record_id = Column(String(64), primary_key=True, index=True)
    task_id = Column(String(64), index=True, nullable=False)
    architecture_id = Column(String(64), index=True, nullable=False)
    task_type = Column(String(32), index=True, nullable=False, default="general")
    complexity = Column(String(16), index=True, nullable=False, default="medium")
    topology = Column(String(32), nullable=False, default="pipeline")
    run_number = Column(Integer, nullable=False, default=1)
    agent_count = Column(Integer, nullable=False, default=1)
    success_rating = Column(Float, nullable=False, default=0.0)
    execution_duration_seconds = Column(Float, nullable=False, default=0.0)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    recommendation_summary = Column(Text, nullable=True)

    # Full JSON blobs for all nested schemas
    task_spec_json = Column(Text, nullable=False)
    architecture_spec_json = Column(Text, nullable=False)
    evaluation_result_json = Column(Text, nullable=False)
    reflection_result_json = Column(Text, nullable=False)


# ---------------------------------------------------------------------------
# Memory Store
# ---------------------------------------------------------------------------

class MemoryStore:
    """
    Persists architectural evolution experience to allow future synthesis improvement.
    Uses async SQLAlchemy with PostgreSQL (production) or SQLite (local dev).
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def save_record(self, record: EvolutionMemoryRecord) -> str:
        """
        Persist an EvolutionMemoryRecord to the database.

        Args:
            record: Complete evolution memory record.

        Returns:
            record_id: The persisted record's unique identifier.
        """
        if not record.record_id:
            record_id = f"mem_{uuid.uuid4().hex[:12]}"
        else:
            record_id = record.record_id

        orm_record = EvolutionMemoryORM(
            record_id=record_id,
            task_id=record.task_spec.task_id,
            architecture_id=record.architecture_spec.architecture_id,
            task_type=record.task_type.value if hasattr(record.task_type, "value") else str(record.task_type),
            complexity=record.complexity.value if hasattr(record.complexity, "value") else str(record.complexity),
            topology=record.architecture_spec.topology.value
            if hasattr(record.architecture_spec.topology, "value")
            else str(record.architecture_spec.topology),
            run_number=record.run_number,
            agent_count=record.agent_count,
            success_rating=record.success_rating,
            execution_duration_seconds=record.execution_duration_seconds,
            timestamp=record.timestamp if record.timestamp else datetime.utcnow(),
            recommendation_summary=record.recommendation_summary,
            task_spec_json=record.task_spec.model_dump_json(),
            architecture_spec_json=record.architecture_spec.model_dump_json(),
            evaluation_result_json=record.evaluation_result.model_dump_json(),
            reflection_result_json=record.reflection_result.model_dump_json(),
        )

        self._db.add(orm_record)
        await self._db.flush()
        return record_id

    async def get_record(self, record_id: str) -> Optional[EvolutionMemoryRecord]:
        """
        Fetch a single evolution memory record by ID.

        Args:
            record_id: The unique record identifier.

        Returns:
            EvolutionMemoryRecord or None if not found.
        """
        result = await self._db.execute(
            select(EvolutionMemoryORM).where(EvolutionMemoryORM.record_id == record_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._orm_to_schema(row)

    async def list_records(
        self,
        limit: int = 20,
        offset: int = 0,
        task_type: Optional[str] = None,
        min_success_rating: Optional[float] = None,
    ) -> List[EvolutionMemoryRecord]:
        """
        List persisted records with optional filtering.

        Args:
            limit: Maximum records to return.
            offset: Pagination offset.
            task_type: Filter by task type string.
            min_success_rating: Filter to records with rating >= threshold.

        Returns:
            List of EvolutionMemoryRecord ordered by timestamp descending.
        """
        query = select(EvolutionMemoryORM).order_by(EvolutionMemoryORM.timestamp.desc())

        if task_type:
            query = query.where(EvolutionMemoryORM.task_type == task_type)
        if min_success_rating is not None:
            query = query.where(EvolutionMemoryORM.success_rating >= min_success_rating)

        query = query.offset(offset).limit(limit)
        result = await self._db.execute(query)
        rows = result.scalars().all()
        return [self._orm_to_schema(row) for row in rows]

    async def count_records(self, task_type: Optional[str] = None) -> int:
        """Return total count of stored records."""
        from sqlalchemy import func
        query = select(func.count()).select_from(EvolutionMemoryORM)
        if task_type:
            query = query.where(EvolutionMemoryORM.task_type == task_type)
        result = await self._db.execute(query)
        return result.scalar_one()

    async def get_records_for_task(self, task_id: str) -> List[EvolutionMemoryRecord]:
        """Retrieve all run history records for a specific task_id."""
        result = await self._db.execute(
            select(EvolutionMemoryORM)
            .where(EvolutionMemoryORM.task_id == task_id)
            .order_by(EvolutionMemoryORM.run_number.asc())
        )
        rows = result.scalars().all()
        return [self._orm_to_schema(row) for row in rows]

    async def delete_record(self, record_id: str) -> bool:
        """
        Delete a record by ID.

        Returns:
            True if deleted, False if not found.
        """
        result = await self._db.execute(
            delete(EvolutionMemoryORM).where(EvolutionMemoryORM.record_id == record_id)
        )
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _orm_to_schema(row: EvolutionMemoryORM) -> EvolutionMemoryRecord:
        """Deserialize an ORM row back to a Pydantic EvolutionMemoryRecord."""
        from app.schemas.task import TaskSpec
        from app.schemas.architecture import ArchitectureSpec
        from app.schemas.evaluation import EvaluationResult
        from app.schemas.reflection import ReflectionResult

        return EvolutionMemoryRecord(
            record_id=row.record_id,
            task_spec=TaskSpec.model_validate_json(row.task_spec_json),
            architecture_spec=ArchitectureSpec.model_validate_json(row.architecture_spec_json),
            evaluation_result=EvaluationResult.model_validate_json(row.evaluation_result_json),
            reflection_result=ReflectionResult.model_validate_json(row.reflection_result_json),
            success_rating=row.success_rating,
            run_number=row.run_number,
            task_type=TaskType(row.task_type),
            complexity=ComplexityLevel(row.complexity),
            timestamp=row.timestamp,
            execution_duration_seconds=row.execution_duration_seconds,
            agent_count=row.agent_count,
            topology=row.topology,
            recommendation_summary=row.recommendation_summary,
        )
