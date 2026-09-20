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
from app.api.simulate import SimulatedMetaController
from app.memory.database import get_db_session

router = APIRouter(prefix="/tasks", tags=["Task Analysis"])

# In-memory task store (keyed by task_id) for fast retrieval within session
# In production, this should be stored in Redis or the DB
_task_store: dict[str, dict] = {}


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
    
    Returns the analyzed TaskSpec and generated ArchitectureSpec.
    This is the entry point for the Agent Forge E2E pipeline.
    """
    if not request.user_prompt.strip():
        raise HTTPException(status_code=400, detail="user_prompt cannot be empty.")

    controller = SimulatedMetaController()
    task_spec, architecture_spec = await controller.process_task(request.user_prompt)

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
async def get_task(task_id: str):
    """Fetch the stored state of a task by its ID."""
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task


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
