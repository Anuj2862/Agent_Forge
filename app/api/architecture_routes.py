"""
FastAPI Architecture Routes (Member 4) — Architecture retrieval and listing.
Endpoint: GET /architectures/{architecture_id}
Endpoint: GET /architectures/task/{task_id}
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.architecture import ArchitectureSpec
from app.schemas.reflection import ReflectionResult
from app.reflection.architecture_modifier import ArchitectureModifier
from app.api.task_routes import _task_store
from app.api.evaluation_routes import _evaluation_store

router = APIRouter(prefix="/architectures", tags=["Architecture Synthesis"])


class EvolveArchitectureRequest(BaseModel):
    task_id: str
    architecture_id: Optional[str] = None
    reflection_id: Optional[str] = None


class EvolveArchitectureResponse(BaseModel):
    task_id: str
    base_architecture_id: str
    evolved_architecture_id: str
    evolved_architecture: ArchitectureSpec
    run_number: int
    modifications_applied: List[str]
    message: str


@router.post("/evolve", response_model=EvolveArchitectureResponse, summary="Mutate architecture using reflection recommendations")
async def evolve_architecture(request: EvolveArchitectureRequest):
    """
    Applies recommendations from ReflectionResult to the base ArchitectureSpec,
    producing and persisting an improved ArchitectureSpec v2.
    """
    task = _task_store.get(request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{request.task_id}' not found.")

    # Locate base architecture
    base_arch_dict = None
    if request.architecture_id:
        if task.get("architecture_spec", {}).get("architecture_id") == request.architecture_id:
            base_arch_dict = task["architecture_spec"]
        elif task.get("architecture_versions", {}).get("v1", {}).get("architecture_id") == request.architecture_id:
            base_arch_dict = task["architecture_versions"]["v1"]
    if not base_arch_dict:
        base_arch_dict = task.get("architecture_versions", {}).get("v1") or task.get("architecture_spec")

    if not base_arch_dict:
        raise HTTPException(status_code=404, detail="No base architecture found to evolve.")

    base_architecture = ArchitectureSpec.model_validate(base_arch_dict)

    # Locate reflection result
    eval_id = request.reflection_id or task.get("latest_evaluation_id")
    eval_entry = _evaluation_store.get(eval_id)
    if not eval_entry:
        # Search all evaluations for this task_id
        for eid, entry in _evaluation_store.items():
            if entry.get("evaluation_result", {}).get("task_id") == request.task_id:
                eval_entry = entry
                break

    if not eval_entry or not eval_entry.get("reflection_result"):
        raise HTTPException(
            status_code=400,
            detail="No reflection analysis found for this task. Run evaluation first.",
        )

    reflection_result = ReflectionResult.model_validate(eval_entry["reflection_result"])

    # Check if recommendations were generated
    if not reflection_result.recommendations:
        return EvolveArchitectureResponse(
            task_id=request.task_id,
            base_architecture_id=base_architecture.architecture_id,
            evolved_architecture_id=base_architecture.architecture_id,
            evolved_architecture=base_architecture,
            run_number=task.get("run_number", 1),
            modifications_applied=[],
            message="No architectural mutation recommended for this run.",
        )

    # Invoke Member 3 ArchitectureModifier
    modifier = ArchitectureModifier()
    evolved_architecture = modifier.mutate_architecture(base_architecture, reflection_result)

    # Preserve multi-version history in task store
    if "architecture_versions" not in task:
        task["architecture_versions"] = {
            "v1": base_arch_dict,
        }
    task["architecture_versions"]["v2"] = evolved_architecture.model_dump()
    task["architecture_spec"] = evolved_architecture.model_dump()
    task["run_number"] = 2
    task["status"] = "architecture_evolved"

    modifications = [
        f"{r.action}: {r.reason or r.details.get('role', '')}"
        for r in reflection_result.recommendations
    ]

    return EvolveArchitectureResponse(
        task_id=request.task_id,
        base_architecture_id=base_architecture.architecture_id,
        evolved_architecture_id=evolved_architecture.architecture_id,
        evolved_architecture=evolved_architecture,
        run_number=2,
        modifications_applied=modifications,
        message=f"Architecture successfully evolved from {base_architecture.architecture_id} to {evolved_architecture.architecture_id}.",
    )


@router.get("/task/{task_id}/versions", summary="Get all architecture versions for a task")
async def get_architecture_versions(task_id: str):
    """Retrieve both v1 and v2 architecture specs for comparative inspection."""
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return {
        "task_id": task_id,
        "current_version": "v2" if task.get("run_number", 1) >= 2 else "v1",
        "versions": task.get("architecture_versions", {
            "v1": task.get("architecture_spec")
        }),
    }


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
        # Also check versions
        for v_arch in task_data.get("architecture_versions", {}).values():
            if v_arch.get("architecture_id") == architecture_id:
                return v_arch
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
                "version": "v2" if data.get("run_number", 1) >= 2 else "v1",
            }
            for data in _task_store.values()
            if data.get("architecture_spec")
        ],
    }
