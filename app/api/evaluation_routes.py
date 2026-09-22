"""
FastAPI Evaluation & Reflection Routes (Member 4).
Endpoint: POST /evaluation/evaluate — Run evaluation + reflection + store memory
Endpoint: GET  /evaluation/{evaluation_id} — Fetch evaluation + reflection result
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec
from app.schemas.evaluation import EvaluationResult
from app.schemas.reflection import ReflectionResult
from app.api.simulate import SimulatedEvaluator, SimulatedReflectionEngine
from app.api.task_routes import _task_store
from app.api.execution_routes import _execution_store
from app.memory.database import get_db_session
from app.memory.memory_store import MemoryStore
from app.memory.memory_schema import EvolutionMemoryRecord

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Reflection"])

# In-memory evaluation store
_evaluation_store: dict[str, dict] = {}


class EvaluateRequest(BaseModel):
    execution_id: str
    task_id: str


@router.post("/evaluate", summary="Evaluate execution, run reflection, store memory")
async def evaluate_execution(
    request: EvaluateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Evaluate execution results, run reflection analysis, and persist the full
    evolution memory record to the database.
    
    This is the step that closes the E2E loop:
    Execution → Evaluation → Reflection → Memory Store
    """
    execution_data = _execution_store.get(request.execution_id)
    if not execution_data:
        raise HTTPException(
            status_code=404,
            detail=f"Execution '{request.execution_id}' not found. Run execution first.",
        )

    task_data = _task_store.get(request.task_id)
    if not task_data:
        raise HTTPException(status_code=404, detail=f"Task '{request.task_id}' not found.")

    task_spec = TaskSpec.model_validate(task_data["task_spec"])
    architecture_spec = ArchitectureSpec.model_validate(task_data["architecture_spec"])
    run_number = execution_data.get("run_number", 1)

    # --- Evaluate ---
    evaluator = SimulatedEvaluator()
    evaluation_result = evaluator.evaluate(
        task_id=request.task_id,
        architecture=architecture_spec,
        execution_output=execution_data,
    )

    # --- Reflect ---
    reflector = SimulatedReflectionEngine()
    reflection_result = reflector.reflect(evaluation_result)

    # --- Compose success rating ---
    m = evaluation_result.metrics
    success_rating = round(
        0.5 * m.task_success + 0.3 * m.quality + 0.2 * m.completeness, 4
    )

    # --- Recommendation summary for quick display ---
    rec_summary = None
    if reflection_result.recommendations:
        top = reflection_result.recommendations[0]
        rec_summary = f"{top.action}: {top.details.get('rationale', top.details.get('role', ''))}"

    # --- Persist to memory store ---
    memory_record = EvolutionMemoryRecord(
        record_id=f"mem_{uuid.uuid4().hex[:12]}",
        task_spec=task_spec,
        architecture_spec=architecture_spec,
        evaluation_result=evaluation_result,
        reflection_result=reflection_result,
        success_rating=success_rating,
        run_number=run_number,
        task_type=task_spec.task_type,
        complexity=task_spec.complexity,
        timestamp=datetime.utcnow(),
        execution_duration_seconds=execution_data.get("duration_seconds", 0.0),
        agent_count=len(architecture_spec.agents),
        topology=architecture_spec.topology.value
        if hasattr(architecture_spec.topology, "value")
        else str(architecture_spec.topology),
        recommendation_summary=rec_summary,
    )

    store = MemoryStore(db)
    saved_record_id = await store.save_record(memory_record)

    # Cache for GET
    eval_record = {
        "evaluation_result": evaluation_result.model_dump(),
        "reflection_result": reflection_result.model_dump(),
        "memory_record_id": saved_record_id,
        "success_rating": success_rating,
        "run_number": run_number,
        "recommendation_summary": rec_summary,
    }
    _evaluation_store[evaluation_result.evaluation_id] = eval_record

    # Update task state
    _task_store[request.task_id]["status"] = "evaluated"
    _task_store[request.task_id]["latest_evaluation_id"] = evaluation_result.evaluation_id
    _task_store[request.task_id]["success_rating"] = success_rating

    return {
        **eval_record,
        "message": f"Evaluation complete. Memory record '{saved_record_id}' stored. Success rating: {success_rating:.2%}",
    }


@router.get("/{evaluation_id}", summary="Get evaluation and reflection results")
async def get_evaluation(evaluation_id: str):
    """Fetch stored evaluation + reflection results by evaluation_id."""
    record = _evaluation_store.get(evaluation_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evaluation '{evaluation_id}' not found.")
    return record


@router.get("/", summary="List all evaluation results")
async def list_evaluations():
    """List all evaluation records."""
    return {
        "evaluations": [
            {
                "evaluation_id": eid,
                "task_id": data.get("evaluation_result", {}).get("task_id"),
                "success_rating": data.get("success_rating"),
                "run_number": data.get("run_number"),
                "memory_record_id": data.get("memory_record_id"),
            }
            for eid, data in _evaluation_store.items()
        ],
        "total": len(_evaluation_store),
    }
