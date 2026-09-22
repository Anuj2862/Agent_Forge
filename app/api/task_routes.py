"""
FastAPI Task Routes (Member 4) — Task submission and retrieval.
Endpoint: POST /tasks/submit  — Analyze prompt → TaskSpec + ArchitectureSpec
Endpoint: GET  /tasks/{task_id} — Retrieve stored task state
Endpoint: GET  /tasks/ — List recent tasks
"""

import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec
from app.controller.meta_controller import MetaController
from app.api.simulate import SimulatedMetaController
from app.memory.database import get_db_session
from app.memory.memory_store import MemoryStore
from app.core.config import settings

router = APIRouter(prefix="/tasks", tags=["Task Analysis"])

# In-memory task store (keyed by task_id) for fast retrieval within session
# In production, this should be stored in Redis or the DB
_task_store: dict[str, dict] = {}

_real_meta_controller = MetaController()
_simulated_meta_controller = SimulatedMetaController()


class TaskSubmitRequest(BaseModel):
    user_prompt: str
    run_number: Optional[int] = 1


class TaskSubmitResponse(BaseModel):
    task_id: str
    task_spec: TaskSpec
    architecture_spec: ArchitectureSpec
    message: str


@router.post("/submit", response_model=TaskSubmitResponse, summary="Submit a task for architecture synthesis")
async def submit_task(request: TaskSubmitRequest):
    """
    Submit a user prompt for task analysis and dynamic architecture synthesis.
    
    Returns the analyzed TaskSpec and generated ArchitectureSpec using Member 1's real
    MetaController, TaskAnalyzer, TaskDecomposer, CapabilityExtractor,
    ComplexityAnalyzer, and ArchitectureGenerator.
    """
    if not request.user_prompt.strip():
        raise HTTPException(status_code=400, detail="user_prompt cannot be empty.")

    mode = getattr(settings, "AGENT_FORGE_MODE", "real").lower()
    if mode == "simulation":
        task_spec, architecture_spec = await _simulated_meta_controller.process_task(request.user_prompt)
    else:
        task_spec, architecture_spec = await _real_meta_controller.process_task_with_spec(request.user_prompt)

    # Cache task state for downstream use
    _task_store[task_spec.task_id] = {
        "task_spec": task_spec.model_dump(),
        "architecture_spec": architecture_spec.model_dump(),
        "run_number": request.run_number or 1,
        "status": "architecture_ready",
    }

    return TaskSubmitResponse(
        task_id=task_spec.task_id,
        task_spec=task_spec,
        architecture_spec=architecture_spec,
        message=f"Task analyzed and architecture synthesized: {len(architecture_spec.agents)}-agent {architecture_spec.topology.value} pipeline.",
    )


@router.get("/{task_id}", summary="Retrieve task state by ID")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db_session)):
    """Fetch the stored state of a task by its ID, with fallback to persistent memory store."""
    task = _task_store.get(task_id)
    if task:
        return task

    # Fallback to persistent memory if available
    try:
        store = MemoryStore(db)
        records = await store.get_records_for_task(task_id)
        if records:
            latest = records[-1]
            restored_task = {
                "task_spec": latest.task_spec.model_dump() if hasattr(latest.task_spec, "model_dump") else latest.task_spec,
                "architecture_spec": latest.architecture_spec.model_dump() if hasattr(latest.architecture_spec, "model_dump") else latest.architecture_spec,
                "run_number": latest.run_number,
                "status": "memory_restored",
            }
            _task_store[task_id] = restored_task
            return restored_task
    except Exception:
        pass

    raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")


@router.get("/", summary="List recent tasks")
async def list_tasks():
    """Return a summary list of all recently submitted tasks."""
    return {
        "tasks": [
            {
                "task_id": tid,
                "status": data.get("status"),
                "task_type": data.get("task_spec", {}).get("task_type"),
                "complexity": data.get("task_spec", {}).get("complexity"),
                "run_number": data.get("run_number", 1),
            }
            for tid, data in _task_store.items()
        ],
        "total": len(_task_store),
    }
