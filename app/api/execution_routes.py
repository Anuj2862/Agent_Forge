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
    architecture_id: Optional[str] = None
    use_real_engine: Optional[bool] = False


@router.post("/run", summary="Execute agent architecture for a task")
async def run_execution(request: ExecutionRunRequest):
    """
    Execute the synthesized architecture for a given task_id.
    
    Runs the multi-agent pipeline and returns agent logs, timing, and final output.
    Supports executing evolved v2 architectures on subsequent runs.
    """
    task_data = _task_store.get(request.task_id)
    if not task_data:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{request.task_id}' not found. Submit the task first via POST /tasks/submit.",
        )

    task_spec = TaskSpec.model_validate(task_data["task_spec"])
    target_run = request.run_number or task_data.get("run_number", 1)

    # Resolve architecture spec (v2 if run_number == 2, or by architecture_id)
    arch_dict = None
    if request.architecture_id:
        if task_data.get("architecture_spec", {}).get("architecture_id") == request.architecture_id:
            arch_dict = task_data["architecture_spec"]
        elif task_data.get("architecture_versions", {}).get("v2", {}).get("architecture_id") == request.architecture_id:
            arch_dict = task_data["architecture_versions"]["v2"]
        elif task_data.get("architecture_versions", {}).get("v1", {}).get("architecture_id") == request.architecture_id:
            arch_dict = task_data["architecture_versions"]["v1"]
    if not arch_dict:
        if target_run >= 2 and task_data.get("architecture_versions", {}).get("v2"):
            arch_dict = task_data["architecture_versions"]["v2"]
        else:
            arch_dict = task_data.get("architecture_spec")

    if not arch_dict:
        raise HTTPException(status_code=404, detail="No valid architecture found to execute.")

    architecture_spec = ArchitectureSpec.model_validate(arch_dict)

    engine = SimulatedExecutionEngine()
    execution_result = await engine.execute_architecture(
        architecture=architecture_spec,
        task_spec=task_spec,
        run_number=target_run,
    )

    # Ensure run_number and architecture_id are explicitly recorded
    execution_result["run_number"] = target_run
    execution_result["architecture_id"] = architecture_spec.architecture_id

    # Cache result for polling
    _execution_store[execution_result["execution_id"]] = execution_result

    # Update task state
    task_data["status"] = "execution_completed"
    task_data["latest_execution_id"] = execution_result["execution_id"]
    task_data["run_number"] = target_run
    if "executions" not in task_data:
        task_data["executions"] = {}
    task_data["executions"][f"run_{target_run}"] = execution_result

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
