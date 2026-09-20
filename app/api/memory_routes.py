"""
FastAPI Evolution Memory Routes (Member 4).
Endpoint: GET    /memory/history         — Paginated evolution history
Endpoint: GET    /memory/retrieve        — Similar experience retrieval
Endpoint: GET    /memory/{record_id}     — Single record fetch
Endpoint: DELETE /memory/{record_id}     — Delete a record
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.task import TaskType, ComplexityLevel, TaskSpec
from app.memory.database import get_db_session
from app.memory.memory_store import MemoryStore
from app.memory.memory_retriever import MemoryRetriever
from app.memory.memory_schema import MemoryQueryResult

router = APIRouter(prefix="/memory", tags=["Evolution Memory"])


@router.get("/history", summary="List evolution memory history (paginated)")
async def list_memory_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    task_type: Optional[str] = Query(default=None, description="Filter by task type"),
    min_success_rating: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Return paginated list of all stored evolution memory records.
    Supports filtering by task_type and minimum success rating.
    """
    store = MemoryStore(db)
    offset = (page - 1) * page_size

    records = await store.list_records(
        limit=page_size,
        offset=offset,
        task_type=task_type,
        min_success_rating=min_success_rating,
    )
    total = await store.count_records(task_type=task_type)

    return MemoryQueryResult(
        records=records,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/retrieve", summary="Retrieve similar past experiences for a task type")
async def retrieve_similar_experiences(
    task_type: str = Query(..., description="Task type to match"),
    complexity: str = Query(default="medium", description="Complexity level"),
    limit: int = Query(default=3, ge=1, le=10),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve the most relevant prior evolution experiences for given task characteristics.
    Used by Member 1's MetaController before architecture synthesis.
    """
    try:
        task_type_enum = TaskType(task_type)
        complexity_enum = ComplexityLevel(complexity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Build a minimal TaskSpec for retrieval
    dummy_spec = TaskSpec(
        task_id="retrieval_query",
        user_prompt="",
        task_type=task_type_enum,
        complexity=complexity_enum,
    )

    retriever = MemoryRetriever(db)
    experiences = await retriever.retrieve_similar_experiences(dummy_spec, limit=limit)

    return {
        "query": {"task_type": task_type, "complexity": complexity},
        "count": len(experiences),
        "experiences": [
            {
                "record_id": exp.record_id,
                "run_number": exp.run_number,
                "success_rating": exp.success_rating,
                "topology": exp.topology,
                "agent_count": exp.agent_count,
                "recommendation_summary": exp.recommendation_summary,
                "timestamp": exp.timestamp.isoformat() if exp.timestamp else None,
            }
            for exp in experiences
        ],
    }


@router.get("/task/{task_id}/history", summary="Get full evolution history for a task")
async def get_task_evolution_history(task_id: str, db: AsyncSession = Depends(get_db_session)):
    """Return all run iterations for a specific task, showing the evolution progression."""
    retriever = MemoryRetriever(db)
    records = await retriever.get_evolution_history_for_task(task_id)
    return {
        "task_id": task_id,
        "run_count": len(records),
        "runs": [
            {
                "record_id": r.record_id,
                "run_number": r.run_number,
                "success_rating": r.success_rating,
                "agent_count": r.agent_count,
                "topology": r.topology,
                "execution_duration_seconds": r.execution_duration_seconds,
                "recommendation_summary": r.recommendation_summary,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in records
        ],
    }


@router.get("/{record_id}", summary="Get a single memory record by ID")
async def get_memory_record(record_id: str, db: AsyncSession = Depends(get_db_session)):
    """Retrieve a single full EvolutionMemoryRecord by its record_id."""
    store = MemoryStore(db)
    record = await store.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Memory record '{record_id}' not found.")
    return record


@router.delete("/{record_id}", summary="Delete a memory record")
async def delete_memory_record(record_id: str, db: AsyncSession = Depends(get_db_session)):
    """Delete an evolution memory record by ID."""
    store = MemoryStore(db)
    deleted = await store.delete_record(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory record '{record_id}' not found.")
    return {"deleted": True, "record_id": record_id}


@router.get("/", summary="Memory module status")
async def get_memory_status(db: AsyncSession = Depends(get_db_session)):
    """Return memory module status and record count."""
    store = MemoryStore(db)
    total = await store.count_records()
    return {"status": "operational", "module": "evolution_memory", "total_records": total}
