"""
Execution Engine Subsystem (Owned by Member 2).

Primary execution flow:
    ArchitectureSpec
        ↓  AgentFactory.create_from_architecture()
    Dict[agent_id → BaseAgent]
        ↓  CommunicationGraphBuilder.build_langgraph()
    Compiled LangGraph StateGraph
        ↓  compiled_graph.invoke(initial_state)
    Final LangGraph state dict
        ↓  _build_result()
    ExecutionResult  →  consumed by Member 3 (Evaluator)
"""

import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from app.agents.agent_factory import AgentFactory, tool_registry
from app.agents.base_agent import BaseAgent
from app.execution.communication_graph import CommunicationGraphBuilder
from app.schemas.architecture import ArchitectureSpec
from app.schemas.execution import AgentStepLog, ExecutionResult, ExecutionStatus

logger = logging.getLogger("agent_forge.execution")


class ExecutionEngine:
    """
    Orchestrates dynamic multi-agent execution via LangGraph StateGraph.

    Responsibilities:
    - Accept any ArchitectureSpec (no hardcoded roles / IDs).
    - Delegate agent instantiation to AgentFactory.
    - Delegate graph construction to CommunicationGraphBuilder
      (which issues the real StateGraph / add_node / add_edge / compile calls).
    - Invoke the compiled graph and convert the resulting state into ExecutionResult.
    """

    def __init__(
        self,
        factory: Optional[AgentFactory] = None,
        graph_builder: Optional[CommunicationGraphBuilder] = None,
    ):
        self.factory = factory or AgentFactory(registry=tool_registry)
        self.graph_builder = graph_builder or CommunicationGraphBuilder()

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def execute_architecture(
        self,
        architecture: ArchitectureSpec,
        input_data: Dict[str, Any],
        agents: Optional[Dict[str, BaseAgent]] = None,
        llm_runner: Optional[Callable] = None,
        max_retries: int = 1,
    ) -> ExecutionResult:
        """
        Execute an ArchitectureSpec through the compiled LangGraph.

        Args:
            architecture:  Member 1 ArchitectureSpec (source of truth for topology).
            input_data:    Initial state / user prompt dict.
            agents:        Optional pre-built agent dict (used in tests for mock injection).
            llm_runner:    Optional LLM callable for offline testing.
            max_retries:   Per-agent retry limit.

        Returns:
            ExecutionResult compatible with Member 3 EvaluationMetrics.
        """
        return self.run_architecture(architecture, input_data, agents, llm_runner, max_retries)

    # ------------------------------------------------------------------
    # Public synchronous API  (primary entry point)
    # ------------------------------------------------------------------

    def run_architecture(
        self,
        architecture: ArchitectureSpec,
        input_data: Dict[str, Any],
        agents: Optional[Dict[str, BaseAgent]] = None,
        llm_runner: Optional[Callable] = None,
        max_retries: int = 1,
    ) -> ExecutionResult:
        """
        Synchronous execution path.  All LangGraph graph construction and
        invocation happens inside this method.

        Execution steps (easily verifiable in code review):
          1. Instantiate / receive agents via AgentFactory.
          2. Build LangGraph StateGraph via CommunicationGraphBuilder.build_langgraph()
             (StateGraph, add_node, add_edge, START, END, compile are all called there).
          3. Prepare initial LangGraph state dict.
          4. Call compiled_graph.invoke(initial_state)  ← LangGraph controls execution.
          5. Convert final LangGraph state → ExecutionResult.
        """
        wall_start = time.time()
        exec_id = input_data.get("execution_id") or f"exec_{uuid.uuid4().hex[:8]}"
        user_prompt = input_data.get("user_prompt") or input_data.get("task_prompt") or ""

        logger.info(
            f"[ExecutionEngine] Starting execution: architecture='{architecture.architecture_id}' "
            f"topology='{architecture.topology.value}' exec_id='{exec_id}'"
        )

        # ---- Step 1: Instantiate agents ----------------------------------------
        if agents is None:
            agents = self.factory.create_from_architecture(architecture, llm_runner=llm_runner)
        else:
            # Inject llm_runner into pre-built agents if provided (test convenience)
            if llm_runner is not None:
                for agent in agents.values():
                    agent._llm_runner = llm_runner

        # ---- Step 2: Build compiled LangGraph ----------------------------------
        # CommunicationGraphBuilder issues:
        #   StateGraph(LangGraphState)
        #   builder.add_node(agent_id, node_fn)   for every agent
        #   builder.add_edge(src, tgt)             for every connection
        #   builder.add_edge(START, entry_node)    for entry nodes
        #   builder.add_edge(terminal_node, END)   for terminal nodes
        #   builder.compile()
        compiled_graph = self.graph_builder.build_langgraph(
            architecture=architecture,
            agents=agents,
            max_retries=max_retries,
        )

        # ---- Step 3: Prepare initial state dict --------------------------------
        initial_state: Dict[str, Any] = {
            "task_id": architecture.task_id,
            "user_prompt": user_prompt,
            "current_agent": None,
            "messages": list(input_data.get("messages", [])),
            "agent_outputs": dict(input_data.get("agent_outputs", {})),
            "step_history": list(input_data.get("step_history", [])),
            "final_output": None,
            "error": None,
            "retry_count": int(input_data.get("retry_count", 0)),
            "metadata": dict(input_data.get("metadata", {})),
        }

        # ---- Step 4: invoke() – LangGraph controls execution order/branching ----
        logger.info(f"[LangGraph] compiled_graph.invoke() -> architecture '{architecture.architecture_id}'")
        try:
            final_state: Dict[str, Any] = compiled_graph.invoke(initial_state)
        except Exception as exc:
            logger.error(f"[LangGraph] Graph invocation failed: {exc}")
            return ExecutionResult(
                execution_id=exec_id,
                task_id=architecture.task_id,
                architecture_id=architecture.architecture_id,
                status=ExecutionStatus.FAILED,
                final_output=f"Graph execution failed: {exc}",
                step_history=[],
                total_steps=0,
                execution_time_seconds=round(time.time() - wall_start, 4),
                agent_count=len(agents),
                tool_call_count=0,
                error=str(exc),
                metadata={"topology": architecture.topology.value},
            )

        # ---- Step 5: Convert final LangGraph state → ExecutionResult -----------
        result = self._build_result(
            exec_id=exec_id,
            architecture=architecture,
            final_state=final_state,
            agents=agents,
            wall_start=wall_start,
        )

        logger.info(
            f"[ExecutionEngine] Completed: architecture='{architecture.architecture_id}' "
            f"status='{result.status.value}' steps={result.total_steps} "
            f"elapsed={result.execution_time_seconds}s"
        )
        return result

    # ------------------------------------------------------------------
    # Result construction
    # ------------------------------------------------------------------

    def _build_result(
        self,
        exec_id: str,
        architecture: ArchitectureSpec,
        final_state: Dict[str, Any],
        agents: Dict[str, BaseAgent],
        wall_start: float,
    ) -> ExecutionResult:
        """Convert the final LangGraph state dict into a structured ExecutionResult."""

        # Determine terminal nodes for final_output derivation (no role assumptions)
        try:
            _, _, _, _, terminal_nodes = self.graph_builder.get_topology_nodes_and_edges(architecture)
        except Exception:
            terminal_nodes = list(agents.keys())[-1:]

        agent_outputs: Dict[str, Any] = final_state.get("agent_outputs", {})
        step_history_dicts: List[Dict] = final_state.get("step_history", [])
        global_error: Optional[str] = final_state.get("error")

        # Determine status from step logs
        any_failed = any(s.get("status") == "failed" for s in step_history_dicts)
        status = ExecutionStatus.FAILED if any_failed else ExecutionStatus.SUCCESS

        # Derive final_output generically from terminal node(s)
        terminal_outputs = [agent_outputs[t] for t in terminal_nodes if t in agent_outputs]
        if len(terminal_outputs) == 1:
            final_output = terminal_outputs[0]
        elif len(terminal_outputs) > 1:
            final_output = "\n\n".join(
                f"[{t} Output]: {agent_outputs[t]}"
                for t in terminal_nodes
                if t in agent_outputs
            )
        else:
            final_output = final_state.get("final_output") or "Execution completed."

        # Convert raw step dicts to AgentStepLog models
        step_logs: List[AgentStepLog] = []
        for idx, s in enumerate(step_history_dicts):
            try:
                step_logs.append(
                    AgentStepLog(
                        step_id=s.get("step_id", f"step_{idx+1}"),
                        agent_id=s.get("agent_id", "unknown"),
                        agent_role=s.get("agent_role"),
                        input_state=s.get("input_state", {}),
                        output_state=s.get("output_state", {}),
                        tool_calls=s.get("tool_calls", []),
                        status=s.get("status", "completed"),
                        execution_time_seconds=s.get("execution_time_seconds", 0.0),
                        error=s.get("error"),
                    )
                )
            except Exception:
                pass  # Never let serialisation prevent a result

        tool_call_count = sum(len(log.tool_calls) for log in step_logs)
        unique_agents = len({log.agent_id for log in step_logs})

        return ExecutionResult(
            execution_id=exec_id,
            task_id=architecture.task_id,
            architecture_id=architecture.architecture_id,
            status=status,
            final_output=final_output,
            step_history=step_logs,
            total_steps=len(step_logs),
            execution_time_seconds=round(time.time() - wall_start, 4),
            agent_count=unique_agents,
            tool_call_count=tool_call_count,
            error=global_error,
            metadata={
                "topology": architecture.topology.value,
                "retry_count": final_state.get("retry_count", 0),
            },
        )
