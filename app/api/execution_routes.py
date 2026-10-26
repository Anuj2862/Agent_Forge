import asyncio
import json
import logging
import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Query, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.task import TaskSpec
from app.schemas.architecture import ArchitectureSpec
from app.schemas.execution import ExecutionResult, ExecutionStatus
from app.schemas.execution_event import (
    ExecutionEvent,
    ExecutionEventType,
    ExecutionStage,
    sanitize_payload,
)
from app.agents.agent_factory import AgentFactory
from app.execution.execution_engine import ExecutionEngine
from app.execution.event_broadcaster import broadcaster
from app.execution.event_emitter import ExecutionEventEmitter
from app.tools.tool_registry import tool_registry
from app.api.simulate import SimulatedExecutionEngine
from app.api.task_routes import _task_store
from app.memory.database import get_db_session, AsyncSessionFactory
from app.memory.repository import DatabaseRepository
from app.memory.models import ExecutionRecordORM
from app.core.config import settings

logger = logging.getLogger("agent_forge.execution_routes")

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


async def _execute_pipeline_core(
    exec_id: str,
    task_id: str,
    task_spec: TaskSpec,
    architecture_spec: ArchitectureSpec,
    target_run: int,
    use_real_engine: bool,
    db: Optional[AsyncSession] = None,
    emitter: Optional[ExecutionEventEmitter] = None,
    is_pipeline_stage: bool = False,
) -> Dict[str, Any]:
    """
    Core multi-agent execution pipeline orchestrating real-time event emissions,
    LangGraph execution, and state persistence.
    """
    if emitter is None:
        emitter = ExecutionEventEmitter(execution_id=exec_id, task_id=task_id, db=db)
        await emitter.init_sequence_from_db()

    # Capture frozen configuration snapshot at execution start
    from app.core.settings_manager import settings_manager
    config_snapshot = settings_manager.get_execution_snapshot()

    # 1. Emit Queued & Started Events
    await emitter.emit(
        event_type=ExecutionEventType.EXECUTION_QUEUED,
        message=f"Execution '{exec_id}' queued for task '{task_id}' (Run #{target_run})",
        stage=ExecutionStage.SYNTHESIS.value,
        data={
            "run_number": target_run,
            "architecture_id": architecture_spec.architecture_id,
            "topology": architecture_spec.topology.value,
            "agent_count": len(architecture_spec.agents),
            "config_version": config_snapshot.get("config_version", 1),
        },
    )

    await emitter.emit(
        event_type=ExecutionEventType.EXECUTION_STARTED,
        message=f"Execution pipeline active for '{architecture_spec.architecture_id}'",
        stage=ExecutionStage.SYNTHESIS.value,
        data={
            "run_number": target_run,
            "agent_count": len(architecture_spec.agents),
            "config_snapshot_id": config_snapshot.get("snapshot_id"),
        },
    )

    # 2. Stage: Graph Compilation
    await emitter.emit(
        event_type=ExecutionEventType.EXECUTION_STAGE_STARTED,

        message=f"Compiling LangGraph StateGraph ({len(architecture_spec.agents)} agents, {len(architecture_spec.connections)} edges)",
        stage=ExecutionStage.GRAPH_COMPILATION.value,
        data={"stage_name": ExecutionStage.GRAPH_COMPILATION.value},
    )

    await emitter.emit(
        event_type=ExecutionEventType.EXECUTION_STAGE_COMPLETED,
        message="LangGraph StateGraph compiled and verified successfully",
        stage=ExecutionStage.GRAPH_COMPILATION.value,
        data={"stage_name": ExecutionStage.GRAPH_COMPILATION.value},
    )

    # 3. Stage: Agent Execution
    await emitter.emit(
        event_type=ExecutionEventType.EXECUTION_STAGE_STARTED,
        message="Dispatching agents into StateGraph execution pipeline",
        stage=ExecutionStage.AGENT_EXECUTION.value,
        data={"stage_name": ExecutionStage.AGENT_EXECUTION.value},
    )

    mode = getattr(settings, "AGENT_FORGE_MODE", "real").lower()
    if mode == "simulation" or not use_real_engine:
        # Simulated run with step-by-step event emission
        execution_res = await _simulated_execution_engine.execute_architecture(
            architecture=architecture_spec,
            task_spec=task_spec,
            run_number=target_run,
        )
        # Emit simulated agent and tool events
        agent_logs = execution_res.get("agent_logs", [])
        for log in agent_logs:
            agent_id = log.get("agent_id", "agent_sim")
            await emitter.emit(
                event_type=ExecutionEventType.AGENT_STARTED,
                message=f"Agent '{log.get('agent_name', agent_id)}' started",
                stage=ExecutionStage.AGENT_EXECUTION.value,
                agent_id=agent_id,
                data={"role": log.get("role", "Agent"), "tools": [t.get("tool") for t in log.get("tool_calls", [])]},
            )
            for tc in log.get("tool_calls", []):
                tool_name = tc.get("tool", "tool")
                await emitter.emit(
                    event_type=ExecutionEventType.TOOL_STARTED,
                    message=f"Tool '{tool_name}' invoked",
                    stage=ExecutionStage.AGENT_EXECUTION.value,
                    agent_id=agent_id,
                    data={"tool": tool_name, "input_preview": tc.get("query", "")},
                )
                await emitter.emit(
                    event_type=ExecutionEventType.TOOL_COMPLETED,
                    message=f"Tool '{tool_name}' completed",
                    stage=ExecutionStage.AGENT_EXECUTION.value,
                    agent_id=agent_id,
                    data={"tool": tool_name, "duration_seconds": tc.get("duration", 0.05), "output_preview": tc.get("output", "")},
                )
            await emitter.emit(
                event_type=ExecutionEventType.AGENT_COMPLETED,
                message=f"Agent '{log.get('agent_name', agent_id)}' completed",
                stage=ExecutionStage.AGENT_EXECUTION.value,
                agent_id=agent_id,
                data={"status": "completed", "output_preview": log.get("output_preview", "")[:200]},
            )
        execution_result = execution_res
        execution_result["execution_id"] = exec_id
    else:
        # Real LangGraph execution engine
        real_res = await _real_execution_engine.execute_architecture(
            architecture=architecture_spec,
            input_data={
                "user_prompt": task_spec.user_prompt,
                "task_id": task_spec.task_id,
                "execution_id": exec_id,
                "emitter": emitter,
            },
        )

        agent_logs = []
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
                        "duration": tc.get("duration_seconds", 0.05),
                    }
                    for tc in step.tool_calls
                ],
            })

        execution_result = {
            "execution_id": exec_id,
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

    execution_result["run_number"] = target_run
    execution_result["architecture_id"] = architecture_spec.architecture_id
    execution_result["config_snapshot"] = config_snapshot

    # 4. End Stage & Terminal Event
    await emitter.emit(
        event_type=ExecutionEventType.EXECUTION_STAGE_COMPLETED,
        message=f"Agent execution stage finished in {execution_result.get('duration_seconds', 0.0)}s",
        stage=ExecutionStage.AGENT_EXECUTION.value,
        data={
            "stage_name": ExecutionStage.AGENT_EXECUTION.value,
            "duration_seconds": execution_result.get("duration_seconds", 0.0),
        },
    )

    if is_pipeline_stage:
        await emitter.emit(
            event_type=ExecutionEventType.EXECUTION_STAGE_COMPLETED,
            message=f"Run #{target_run} execution completed ({execution_result.get('total_steps', 0)} steps)",
            stage=ExecutionStage.AGENT_EXECUTION.value,
            status="running",
            data={
                "run_number": target_run,
                "duration_seconds": execution_result.get("duration_seconds", 0.0),
                "total_steps": execution_result.get("total_steps", 0),
                "tool_call_count": execution_result.get("tool_call_count", 0),
                "final_output": str(execution_result.get("final_output", ""))[:300],
            },
        )
    elif execution_result.get("status") in ("completed", "success"):
        await emitter.emit(
            event_type=ExecutionEventType.EXECUTION_COMPLETED,
            message=f"Execution '{exec_id}' completed successfully ({execution_result.get('total_steps', 0)} steps)",
            stage=ExecutionStage.AGENT_EXECUTION.value,
            status="completed",
            data={
                "duration_seconds": execution_result.get("duration_seconds", 0.0),
                "total_steps": execution_result.get("total_steps", 0),
                "tool_call_count": execution_result.get("tool_call_count", 0),
                "final_output": str(execution_result.get("final_output", ""))[:300],
            },
        )
    else:
        await emitter.emit(
            event_type=ExecutionEventType.EXECUTION_FAILED,
            message=f"Execution '{exec_id}' failed: {execution_result.get('error', 'Unknown failure')}",
            stage=ExecutionStage.AGENT_EXECUTION.value,
            status="failed",
            error=str(execution_result.get("error", "execution failed")),
        )

    # 5. Persist to DB and update memory cache
    _execution_store[exec_id] = execution_result

    if db:
        try:
            repo = DatabaseRepository(db)
            rec = ExecutionRecordORM(
                execution_id=exec_id,
                task_id=task_id,
                architecture_id=architecture_spec.architecture_id,
                run_number=target_run,
                status=execution_result.get("status", "completed"),
                duration_seconds=float(execution_result.get("duration_seconds", 0.0)),
                execution_result_json=json.dumps(execution_result, default=str),
            )
            db.add(rec)
            await db.flush()
            await repo.update_task_status(
                task_id=task_id,
                status="execution_completed",
                run_number=target_run,
                latest_execution_id=exec_id,
            )
        except Exception as db_err:
            logger.warning(f"Failed to persist execution {exec_id} to DB: {db_err}")

    # Update in-memory task store
    task_data = _task_store.get(task_id)
    if task_data:
        task_data["status"] = "execution_completed"
        task_data["latest_execution_id"] = exec_id
        if "executions" not in task_data or task_data["executions"] is None:
            task_data["executions"] = [execution_result]
        elif isinstance(task_data["executions"], list):
            task_data["executions"].append(execution_result)
        elif isinstance(task_data["executions"], dict):
            task_data["executions"][f"run_{target_run}"] = execution_result

    return execution_result


@router.post("/run", summary="Execute agent architecture synchronously for a task")
async def run_execution(
    request: ExecutionRunRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Execute the synthesized architecture for a given task_id synchronously.
    Streams and persists real-time events, and returns the final execution result.
    """
    repo = DatabaseRepository(db)
    task_data = _task_store.get(request.task_id)
    if not task_data:
        task_data = await repo.get_task_composite(request.task_id)
        if task_data:
            _task_store[request.task_id] = task_data

    if not task_data:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{request.task_id}' not found. Submit the task first via POST /tasks/submit.",
        )

    task_spec = TaskSpec.model_validate(task_data["task_spec"])
    target_run = request.run_number or task_data.get("run_number", 1)

    # Resolve architecture spec
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
    exec_id = f"exec_{uuid.uuid4().hex[:8]}"

    return await _execute_pipeline_core(
        exec_id=exec_id,
        task_id=request.task_id,
        task_spec=task_spec,
        architecture_spec=architecture_spec,
        target_run=target_run,
        use_real_engine=bool(request.use_real_engine),
        db=db,
    )


@router.post("/start", summary="Start agent architecture execution asynchronously")
async def start_execution(
    request: ExecutionRunRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Start an asynchronous multi-agent execution pipeline.
    Returns immediately with execution_id and status='running'.
    Clients subscribe to GET /execution/{execution_id}/events to follow real-time progress.
    """
    repo = DatabaseRepository(db)
    task_data = _task_store.get(request.task_id)
    if not task_data:
        task_data = await repo.get_task_composite(request.task_id)
        if task_data:
            _task_store[request.task_id] = task_data

    if not task_data:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{request.task_id}' not found. Submit the task first via POST /tasks/submit.",
        )

    task_spec = TaskSpec.model_validate(task_data["task_spec"])
    target_run = request.run_number or task_data.get("run_number", 1)

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
    exec_id = f"exec_{uuid.uuid4().hex[:8]}"

    # Initialize in-memory cache as running
    _execution_store[exec_id] = {
        "execution_id": exec_id,
        "task_id": request.task_id,
        "architecture_id": architecture_spec.architecture_id,
        "run_number": target_run,
        "status": "running",
        "duration_seconds": 0.0,
        "step_history": [],
        "agent_logs": [],
    }

    # Spawn background execution runner
    async def _bg_runner():
        async with AsyncSessionFactory() as bg_db:
            try:
                await _execute_pipeline_core(
                    exec_id=exec_id,
                    task_id=request.task_id,
                    task_spec=task_spec,
                    architecture_spec=architecture_spec,
                    target_run=target_run,
                    use_real_engine=bool(request.use_real_engine),
                    db=bg_db,
                )
                await bg_db.commit()
            except Exception as e:
                logger.error(f"Background execution failed for {exec_id}: {e}", exc_info=True)
                await bg_db.rollback()

    asyncio.create_task(_bg_runner())

    return {
        "execution_id": exec_id,
        "task_id": request.task_id,
        "architecture_id": architecture_spec.architecture_id,
        "run_number": target_run,
        "status": "running",
        "stream_url": f"/execution/{exec_id}/events",
    }


@router.post("/pipeline", summary="Start full autonomous self-evolution pipeline asynchronously")
async def start_autonomous_pipeline(
    request: ExecutionRunRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Launch the complete autonomous research pipeline end-to-end:
    Run 1 execution -> evaluation -> reflection -> architecture mutation (V2) ->
    constraint validation -> Run 2 execution -> evaluation -> evolution decision -> memory.
    Returns immediately with execution_id and status='running'.
    Stream events live via GET /execution/{execution_id}/events.
    """
    from app.execution.pipeline_orchestrator import AutonomousPipelineOrchestrator
    repo = DatabaseRepository(db)
    task_data = _task_store.get(request.task_id)
    if not task_data:
        task_data = await repo.get_task_composite(request.task_id)
        if task_data:
            _task_store[request.task_id] = task_data

    if not task_data:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{request.task_id}' not found. Please submit task first.",
        )

    task_spec = TaskSpec.model_validate(task_data["task_spec"])
    arch_dict = task_data.get("architecture_spec") or task_data.get("architecture_versions", {}).get("v1")
    if not arch_dict:
        raise HTTPException(status_code=404, detail="No valid base architecture found for task.")

    architecture_spec = ArchitectureSpec.model_validate(arch_dict)
    exec_id = f"exec_{uuid.uuid4().hex[:8]}"

    _execution_store[exec_id] = {
        "execution_id": exec_id,
        "task_id": request.task_id,
        "architecture_id": architecture_spec.architecture_id,
        "run_number": 1,
        "status": "running",
        "duration_seconds": 0.0,
        "step_history": [],
        "agent_logs": [],
    }

    orchestrator = AutonomousPipelineOrchestrator(
        task_id=request.task_id,
        task_spec=task_spec,
        architecture_spec=architecture_spec,
        execution_id=exec_id,
        use_real_engine=bool(request.use_real_engine),
    )
    asyncio.create_task(orchestrator.execute_full_pipeline())

    return {
        "execution_id": exec_id,
        "task_id": request.task_id,
        "architecture_id": architecture_spec.architecture_id,
        "run_number": 1,
        "status": "running",
        "pipeline_mode": "autonomous",
        "stream_url": f"/execution/{exec_id}/events",
    }


@router.get("/{execution_id}/events", summary="Stream real-time execution events via SSE")
async def stream_execution_events(
    execution_id: str,
    after_seq: Optional[int] = Query(0, description="Resume stream after sequence number"),
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Server-Sent Events (SSE) streaming endpoint for an execution.
    Supports reconnection and resume via Last-Event-ID or ?after_seq=N.
    Emits keepalive comments to prevent intermediate proxy timeouts.
    """
    repo = DatabaseRepository(db)

    # Validate execution existence
    exec_rec = _execution_store.get(execution_id)
    if not exec_rec:
        exec_rec = await repo.get_execution(execution_id)

    if not exec_rec:
        events_check = await repo.list_execution_events(execution_id, after_seq=0, limit=1)
        if not events_check:
            raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found.")

    start_seq = after_seq or 0
    if last_event_id:
        try:
            start_seq = max(start_seq, int(last_event_id))
        except (ValueError, TypeError):
            pass

    async def sse_event_stream():
        current_seq = start_seq

        # 1. Replay historical events from database
        historical_events = await repo.list_execution_events(execution_id, after_seq=current_seq)
        for ev in historical_events:
            current_seq = max(current_seq, ev.sequence_number)
            yield ev.to_sse_message()

        # Check if execution has reached terminal state
        is_terminal = False
        if exec_rec and exec_rec.get("status") in ("completed", "failed", "cancelled", "success"):
            is_terminal = True
        elif historical_events and historical_events[-1].event_type.value in (
            "execution.completed", "execution.failed", "execution.cancelled"
        ):
            is_terminal = True

        if is_terminal:
            return

        # 2. Subscribe to live events with keepalive loop
        queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        async with broadcaster._lock:
            if execution_id not in broadcaster._subscribers:
                broadcaster._subscribers[execution_id] = set()
            broadcaster._subscribers[execution_id].add(queue)

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    if event.sequence_number > current_seq:
                        current_seq = event.sequence_number
                        yield event.to_sse_message()
                    if event.event_type.value in ("execution.completed", "execution.failed", "execution.cancelled"):
                        break
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            async with broadcaster._lock:
                if execution_id in broadcaster._subscribers:
                    broadcaster._subscribers[execution_id].discard(queue)
                    if not broadcaster._subscribers[execution_id]:
                        del broadcaster._subscribers[execution_id]

    return StreamingResponse(
        sse_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{execution_id}/events/history", summary="List persisted execution events as JSON")
async def get_execution_event_history(
    execution_id: str,
    after_seq: int = Query(0, description="Fetch events with sequence number greater than this"),
    limit: int = Query(500, description="Maximum number of events to return"),
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve historical execution events as structured JSON."""
    repo = DatabaseRepository(db)
    events = await repo.list_execution_events(execution_id, after_seq=after_seq, limit=limit)
    return {
        "execution_id": execution_id,
        "count": len(events),
        "events": [e.model_dump(mode="json") for e in events],
    }


@router.get("/{execution_id}", summary="Get execution result by ID")
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve execution results and agent logs by execution_id."""
    result = _execution_store.get(execution_id)
    if result:
        return result

    repo = DatabaseRepository(db)
    db_res = await repo.get_execution(execution_id)
    if db_res:
        _execution_store[execution_id] = db_res
        return db_res

    raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found.")


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
