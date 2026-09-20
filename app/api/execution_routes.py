"""
FastAPI Execution Routes (Member 4) — Agent team execution.
Endpoint: POST /execution/run   — Execute an architecture for a task
Endpoint: GET  /execution/{execution_id} — Poll execution status/results
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec
from app.api.simulate import SimulatedExecutionEngine
from app.api.task_routes import _task_store

router = APIRouter(prefix="/execution", tags=["Execution Engine"])

# In-memory execution result store
_execution_store: dict[str, dict] = {}


class ExecutionRunRequest(BaseModel):
    task_id: str
    run_number: Optional[int] = 1


@router.post("/run", summary="Execute agent architecture for a task")
async def run_execution(request: ExecutionRunRequest):
    """
    Execute the synthesized architecture for a given task_id.
    
    Runs the multi-agent pipeline and returns agent logs, timing, and final output.
    """
    task_data = _task_store.get(request.task_id)
    if not task_data:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{request.task_id}' not found. Submit the task first via POST /tasks/submit.",
        )

    task_spec = TaskSpec.model_validate(task_data["task_spec"])
    architecture_spec = ArchitectureSpec.model_validate(task_data["architecture_spec"])

    engine = SimulatedExecutionEngine()
    execution_result = await engine.execute_architecture(
        architecture=architecture_spec,
        task_spec=task_spec,
        run_number=request.run_number or task_data.get("run_number", 1),
    )

    # Cache result for polling
    _execution_store[execution_result["execution_id"]] = execution_result

    # Update task state
    _task_store[request.task_id]["status"] = "execution_completed"
    _task_store[request.task_id]["latest_execution_id"] = execution_result["execution_id"]

    return execution_result


@router.get("/{execution_id}", summary="Get execution result by ID")
async def get_execution(execution_id: str):
    """Retrieve execution results and agent logs by execution_id."""
    result = _execution_store.get(execution_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found.")
    return result


@router.get("/", summary="List all execution results")
async def list_executions():
    """List all execution results."""
    return {
        "executions": [
            {
                "execution_id": eid,
                "task_id": data.get("task_id"),
                "run_number": data.get("run_number"),
                "status": data.get("status"),
                "duration_seconds": data.get("duration_seconds"),
                "overall_success_rate": data.get("overall_success_rate"),
            }
            for eid, data in _execution_store.items()
        ],
        "total": len(_execution_store),
    }
