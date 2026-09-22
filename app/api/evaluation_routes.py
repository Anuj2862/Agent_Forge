"""
FastAPI Evaluation & Reflection Routes (Member 4).
Endpoint: POST /evaluation/evaluate — Run evaluation + reflection + store memory
Endpoint: GET  /evaluation/{evaluation_id} — Fetch evaluation + reflection result
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime, timezone

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

    # --- Evaluate & Reflect ---
    try:
        from app.evaluation.evaluator import Evaluator
        from app.evaluation.failure_analyzer import FailureAnalyzer
        from app.reflection.reflection_engine import ReflectionEngine

        real_evaluator = Evaluator()
        evaluation_result = real_evaluator.evaluate(
            task=task_spec,
            architecture=architecture_spec,
            execution=execution_data,
        )

        real_reflection_engine = ReflectionEngine(failure_analyzer=FailureAnalyzer())
        reflection_result = real_reflection_engine.reflect(
            evaluation_result=evaluation_result,
            architecture=architecture_spec,
            task=task_spec,
            execution=execution_data,
        )
    except Exception as e:
        evaluator = SimulatedEvaluator()
        evaluation_result = evaluator.evaluate(
            task_id=request.task_id,
            architecture=architecture_spec,
            execution_output=execution_data,
        )
        reflector = SimulatedReflectionEngine()
        reflection_result = reflector.reflect(evaluation_result)

    # --- Compose success rating ---
    m = evaluation_result.metrics
    accuracy_term = getattr(m, "accuracy", m.task_success) or m.task_success
    success_rating = round(
        0.4 * m.task_success + 0.3 * m.quality + 0.2 * m.completeness + 0.1 * accuracy_term, 4
    )

    # --- Recommendation summary for quick display ---
    rec_summary = None
    if reflection_result.recommendations:
        top = reflection_result.recommendations[0]
        rec_summary = f"{top.action}: {top.reason or top.details.get('role', '')}"

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
        timestamp=datetime.now(timezone.utc),
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

    # Update task state and multi-run evaluation history
    task_data["status"] = "evaluated"
    task_data["latest_evaluation_id"] = evaluation_result.evaluation_id
    task_data["success_rating"] = success_rating
    if "evaluations" not in task_data:
        task_data["evaluations"] = {}
    task_data["evaluations"][f"run_{run_number}"] = eval_record

    return {
        **eval_record,
        "message": f"Evaluation complete for Run #{run_number}. Memory record '{saved_record_id}' stored. Success rating: {success_rating:.2%}",
    }


def _compute_metric_deltas(run1_record: dict, run2_record: dict) -> dict:
    m1 = run1_record.get("evaluation_result", {}).get("metrics", {})
    m2 = run2_record.get("evaluation_result", {}).get("metrics", {})
    return {
        "task_success": round((m2.get("task_success", 0) or 0) - (m1.get("task_success", 0) or 0), 3),
        "quality": round((m2.get("quality", 0) or 0) - (m1.get("quality", 0) or 0), 3),
        "accuracy": round((m2.get("accuracy", 0) or 0) - (m1.get("accuracy", 0) or 0), 3),
        "completeness": round((m2.get("completeness", 0) or 0) - (m1.get("completeness", 0) or 0), 3),
        "duration_seconds": round((m2.get("execution_time_seconds", 0) or 0) - (m1.get("execution_time_seconds", 0) or 0), 2),
        "agent_count": (m2.get("agent_count", 0) or 0) - (m1.get("agent_count", 0) or 0),
        "overall_score": round(
            (run2_record.get("success_rating", 0) or 0) - (run1_record.get("success_rating", 0) or 0), 3
        ),
    }


def _compute_architecture_diff(arch1: dict, arch2: dict) -> dict:
    agents1 = {a["agent_id"]: a for a in arch1.get("agents", [])}
    agents2 = {a["agent_id"]: a for a in arch2.get("agents", [])}
    added = [a for aid, a in agents2.items() if aid not in agents1]
    removed = [a for aid, a in agents1.items() if aid not in agents2]

    conns1 = {(c.get("source"), c.get("target")) for c in arch1.get("connections", [])}
    conns2 = {(c.get("source"), c.get("target")) for c in arch2.get("connections", [])}
    added_conns = list(conns2 - conns1)
    removed_conns = list(conns1 - conns2)

    return {
        "added_agents": added,
        "removed_agents": removed,
        "added_connections": [{"source": s, "target": t} for s, t in added_conns if s and t],
        "removed_connections": [{"source": s, "target": t} for s, t in removed_conns if s and t],
        "topology_changed": arch1.get("topology") != arch2.get("topology"),
        "initial_topology": arch1.get("topology"),
        "evolved_topology": arch2.get("topology"),
    }


@router.get("/compare/{task_id}", summary="Compare Run 1 vs Run 2 evaluations and architecture evolution")
async def compare_task_runs(task_id: str):
    """
    Returns comparative evaluation metrics and architecture diff across runs for a given task.
    """
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    evals = task.get("evaluations", {})
    run_1_eval = evals.get("run_1")
    run_2_eval = evals.get("run_2")

    if not run_1_eval or not run_2_eval:
        task_evals = [
            e for e in _evaluation_store.values()
            if e.get("evaluation_result", {}).get("task_id") == task_id
        ]
        task_evals.sort(key=lambda x: x.get("run_number", 1))
        if len(task_evals) >= 1 and not run_1_eval:
            run_1_eval = task_evals[0]
        if len(task_evals) >= 2 and not run_2_eval:
            run_2_eval = task_evals[1]

    versions = task.get("architecture_versions", {})
    arch_v1 = versions.get("v1") or task.get("architecture_spec")
    arch_v2 = versions.get("v2")

    has_comparison = run_1_eval is not None and run_2_eval is not None
    deltas = _compute_metric_deltas(run_1_eval, run_2_eval) if has_comparison else None
    arch_diff = _compute_architecture_diff(arch_v1, arch_v2) if (arch_v1 and arch_v2) else None

    return {
        "task_id": task_id,
        "has_comparison": has_comparison,
        "run_1": {
            "evaluation": run_1_eval,
            "architecture": arch_v1,
        } if run_1_eval else None,
        "run_2": {
            "evaluation": run_2_eval,
            "architecture": arch_v2,
        } if run_2_eval else None,
        "deltas": deltas,
        "architecture_diff": arch_diff,
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
