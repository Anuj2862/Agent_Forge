"""
FastAPI Architecture Routes (Member 4) — Architecture retrieval and listing.
Endpoint: GET /architectures/{architecture_id}
Endpoint: GET /architectures/task/{task_id}
"""

from fastapi import APIRouter, HTTPException
from app.api.task_routes import _task_store

router = APIRouter(prefix="/architectures", tags=["Architecture Synthesis"])


@router.get("/task/{task_id}", summary="Get architecture for a task")
async def get_architecture_for_task(task_id: str):
    """Return the ArchitectureSpec generated for a specific task_id."""
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"No architecture found for task '{task_id}'.")
    return task.get("architecture_spec")


@router.get("/{architecture_id}", summary="Get architecture by ID")
async def get_architecture(architecture_id: str):
    """Retrieve an ArchitectureSpec by its architecture_id."""
    for task_data in _task_store.values():
        arch = task_data.get("architecture_spec", {})
        if arch.get("architecture_id") == architecture_id:
            return arch
    raise HTTPException(status_code=404, detail=f"Architecture '{architecture_id}' not found.")


@router.get("/", summary="List all architectures")
async def list_architectures():
    """List all architectures that have been synthesized."""
    return {
        "architectures": [
            {
                "architecture_id": data.get("architecture_spec", {}).get("architecture_id"),
                "task_id": data.get("task_spec", {}).get("task_id"),
                "topology": data.get("architecture_spec", {}).get("topology"),
                "agent_count": len(data.get("architecture_spec", {}).get("agents", [])),
            }
            for data in _task_store.values()
            if data.get("architecture_spec")
        ],
    }
