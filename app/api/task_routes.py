"""
FastAPI Task Routes (Member 4) — Task submission and retrieval.
Endpoint: POST /tasks/submit  — Analyze prompt → TaskSpec + ArchitectureSpec
Endpoint: GET  /tasks/{task_id} — Retrieve stored task state
Endpoint: GET  /tasks/ — List recent tasks
"""

import uuid
from typing import Optional, Union, Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.task import TaskSpec, TaskConstraints
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


from app.memory.repository import DatabaseRepository


class TaskSubmitRequest(BaseModel):
    user_prompt: str
    run_number: Optional[int] = 1
    max_agents: Optional[int] = None
    max_execution_time_seconds: Optional[float] = None
    allowed_tools: Optional[list[str]] = None
    forbidden_tools: Optional[list[str]] = None
    require_verification: Optional[bool] = None
    constraints: Optional[Union[TaskConstraints, Dict[str, Any], List[str]]] = None
    auto_pipeline: Optional[bool] = False
    use_real_engine: Optional[bool] = True


class TaskSubmitResponse(BaseModel):
    task_id: str
    task_spec: TaskSpec
    architecture_spec: ArchitectureSpec
    message: str
    execution_id: Optional[str] = None
    stream_url: Optional[str] = None


@router.post("/submit", response_model=TaskSubmitResponse, summary="Submit a task for architecture synthesis")
async def submit_task(
    request: TaskSubmitRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Submit a user prompt for task analysis and dynamic architecture synthesis.
    Enforces typed operational constraints (max_agents, forbidden_tools, etc.)
    and persists the synthesized state in the authoritative database.
    Optionally launches the full autonomous self-evolution pipeline asynchronously.
    """
    if not request.user_prompt.strip():
        raise HTTPException(status_code=400, detail="user_prompt cannot be empty.")

    c_dict: Dict[str, Any] = {}
    c_list: List[str] = []
    if isinstance(request.constraints, TaskConstraints):
        c_dict = request.constraints.model_dump()
    elif isinstance(request.constraints, dict):
        c_dict = request.constraints
    elif isinstance(request.constraints, list):
        c_list = request.constraints

    structured_constraints = {
        "max_agents": request.max_agents if request.max_agents is not None else c_dict.get("max_agents"),
        "max_execution_time_seconds": request.max_execution_time_seconds if request.max_execution_time_seconds is not None else c_dict.get("max_execution_time_seconds"),
        "allowed_tools": request.allowed_tools or c_dict.get("allowed_tools") or [],
        "forbidden_tools": request.forbidden_tools or c_dict.get("forbidden_tools") or [],
        "require_verification": request.require_verification if request.require_verification is not None else c_dict.get("require_verification", False),
        "constraints": c_list or c_dict.get("constraints") or [],
    }

    mode = getattr(settings, "AGENT_FORGE_MODE", "real").lower()
    if mode == "simulation":
        task_spec, architecture_spec = await _simulated_meta_controller.process_task(
            request.user_prompt, structured_constraints=structured_constraints
        )
    else:
        task_spec, architecture_spec = await _real_meta_controller.process_task_with_spec(
            user_prompt=request.user_prompt,
            structured_constraints=structured_constraints,
            db=db,
        )

    # Persist authoritatively to database
    repo = DatabaseRepository(db)
    await repo.save_task(
        task_spec=task_spec,
        architecture_spec=architecture_spec,
        run_number=request.run_number or 1,
        status="architecture_ready",
    )

    # Cache task state for fast retrieval within session
    _task_store[task_spec.task_id] = {
        "task_spec": task_spec.model_dump(),
        "architecture_spec": architecture_spec.model_dump(),
        "run_number": request.run_number or 1,
        "status": "architecture_ready",
    }

    exec_id: Optional[str] = None
    stream_url: Optional[str] = None

    # Autonomous pipeline execution if requested
    if request.auto_pipeline:
        import asyncio
        from app.api.execution_routes import _execution_store
        from app.execution.pipeline_orchestrator import AutonomousPipelineOrchestrator

        exec_id = f"exec_{uuid.uuid4().hex[:8]}"
        stream_url = f"/execution/{exec_id}/events"

        _execution_store[exec_id] = {
            "execution_id": exec_id,
            "task_id": task_spec.task_id,
            "architecture_id": architecture_spec.architecture_id,
            "run_number": 1,
            "status": "running",
            "duration_seconds": 0.0,
            "step_history": [],
            "agent_logs": [],
        }

        orchestrator = AutonomousPipelineOrchestrator(
            task_id=task_spec.task_id,
            task_spec=task_spec,
            architecture_spec=architecture_spec,
            execution_id=exec_id,
            use_real_engine=bool(request.use_real_engine),
        )
        asyncio.create_task(orchestrator.execute_full_pipeline())

    return TaskSubmitResponse(
        task_id=task_spec.task_id,
        task_spec=task_spec,
        architecture_spec=architecture_spec,
        execution_id=exec_id,
        stream_url=stream_url,
        message=f"Task analyzed and architecture synthesized: {len(architecture_spec.agents)}-agent {architecture_spec.topology.value} pipeline.",
    )


@router.get("/{task_id}", summary="Retrieve task state by ID")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db_session)):
    """Fetch the stored state of a task by its ID with full database persistence."""
    repo = DatabaseRepository(db)
    task_composite = await repo.get_task_composite(task_id)
    if task_composite:
        # Keep cache updated
        _task_store[task_id] = task_composite
        return task_composite

    # Fallback to in-memory store
    task = _task_store.get(task_id)
    if task:
        return task

    # Fallback to persistent evolution memory if available
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
async def list_tasks(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """Return a summary list of all tasks from persistent database with pagination."""
    repo = DatabaseRepository(db)
    db_tasks = await repo.list_tasks(limit=limit, offset=offset)
    if db_tasks:
        return {
            "tasks": db_tasks,
            "total": len(db_tasks),
        }

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
