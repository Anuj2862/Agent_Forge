import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec
from app.schemas.execution import ExecutionResult, ExecutionStatus
from app.agents.agent_factory import AgentFactory
from app.execution.execution_engine import ExecutionEngine
from app.tools.tool_registry import tool_registry
from app.api.simulate import SimulatedExecutionEngine
from app.api.task_routes import _task_store
from app.core.config import settings

router = APIRouter(prefix="/execution", tags=["Execution Engine"])

# In-memory execution result store
_execution_store: dict[str, dict] = {}

_agent_factory = AgentFactory(registry=tool_registry)
_real_execution_engine = ExecutionEngine(factory=_agent_factory)
_simulated_execution_engine = SimulatedExecutionEngine()


class ExecutionRunRequest(BaseModel):
    task_id: str
    run_number: Optional[int] = 1
    architecture_id: Optional[str] = None
    use_real_engine: Optional[bool] = True


@router.post("/run", summary="Execute agent architecture for a task")
async def run_execution(request: ExecutionRunRequest):
    """
    Execute the synthesized architecture for a given task_id.
    
    Runs the multi-agent pipeline using Member 2's real LangGraph ExecutionEngine
    and dynamic AgentFactory with registered tools, returning real step history,
    agent execution traces, and generated output.
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

    mode = getattr(settings, "AGENT_FORGE_MODE", "real").lower()
    if mode == "simulation" or not request.use_real_engine:
        execution_result = await _simulated_execution_engine.execute_architecture(
            architecture=architecture_spec,
            task_spec=task_spec,
            run_number=target_run,
        )
    else:
        exec_id = f"exec_{uuid.uuid4().hex[:8]}"
        real_res = await _real_execution_engine.execute_architecture(
            architecture=architecture_spec,
            input_data={
                "user_prompt": task_spec.user_prompt,
                "task_id": task_spec.task_id,
                "execution_id": exec_id,
            },
        )

        agent_logs: List[Dict[str, Any]] = []
        for step in real_res.step_history:
            agent_logs.append({
                "agent_id": step.agent_id,
                "agent_name": step.agent_role or step.agent_id,
                "role": step.agent_role or "Agent",
                "status": step.status,
                "execution_time_seconds": step.execution_time_seconds,
                "output_preview": str(step.output_state.get("output", real_res.final_output or ""))[:300],
                "tool_calls": [
                    {
                        "tool": tc.get("tool", "tool"),
                        "query": tc.get("input", ""),
                        "output": str(tc.get("result", ""))[:200],
                        "duration": 0.05,
                    }
                    for tc in step.tool_calls
                ],
            })

        execution_result = {
            "execution_id": real_res.execution_id,
            "task_id": real_res.task_id,
            "architecture_id": real_res.architecture_id,
            "status": "completed" if real_res.status == ExecutionStatus.SUCCESS else real_res.status.value,
            "run_number": target_run,
            "total_steps": real_res.total_steps,
            "execution_time": real_res.execution_time_seconds,
            "duration_seconds": real_res.execution_time_seconds,
            "agent_count": real_res.agent_count,
            "tool_call_count": real_res.tool_call_count,
            "final_output": real_res.final_output,
            "overall_success_rate": 1.0 if real_res.status == ExecutionStatus.SUCCESS else 0.5,
            "step_history": [s.model_dump() for s in real_res.step_history],
            "agent_traces": [t.model_dump() for t in real_res.agent_traces],
            "agent_logs": agent_logs,
            "error": real_res.error,
        }

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
