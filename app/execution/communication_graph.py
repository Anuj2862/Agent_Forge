"""
Communication Graph Representation (Owned by Member 2).

Constructs actual LangGraph StateGraph objects dynamically from ArchitectureSpec.
ArchitectureSpec.connections become real LangGraph edges; agents become real LangGraph nodes.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# LangGraph imports – fail explicitly if not installed (no silent fallback).
try:
    from langgraph.graph import StateGraph, START, END
    from typing import Annotated
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "LangGraph is required for Agent Forge execution. "
        "Install it with: pip install langgraph>=0.2.0"
    ) from exc

from app.agents.base_agent import BaseAgent
from app.schemas.architecture import ArchitectureSpec, TopologyType

logger = logging.getLogger("agent_forge.execution")

SUPPORTED_TOPOLOGIES = {TopologyType.PIPELINE, TopologyType.PARALLEL, TopologyType.HYBRID}

# ---------------------------------------------------------------------------
# LangGraph-compatible state type
# ---------------------------------------------------------------------------
# We use Annotated reducers so that parallel branches that each return
# updates to agent_outputs / step_history / messages are MERGED rather than
# overwriting each other.  This is the standard LangGraph pattern for fan-in.

def _merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer: merge two dicts, later values win (used for agent_outputs)."""
    result = dict(a or {})
    result.update(b or {})
    return result

def _merge_lists(a: List[Any], b: List[Any]) -> List[Any]:
    """Reducer: concatenate two lists (used for step_history / messages)."""
    return (a or []) + (b or [])

def _sum_ints(a: int, b: int) -> int:
    """Reducer: accumulate retry counts across nodes."""
    return (a or 0) + (b or 0)

def _merge_errors(a: Optional[str], b: Optional[str]) -> Optional[str]:
    """Reducer: keep the first non-None error encountered."""
    return a if a is not None else b

def _last_wins(a: Any, b: Any) -> Any:
    """Reducer: last writer wins (used for scalar fields written by every node)."""
    return b if b is not None else a

# The LangGraph state schema.
# TypedDict + Annotated reducers is the canonical LangGraph pattern.
# Reducers on agent_outputs / step_history / messages enable parallel
# branch fan-in without overwriting each other.
# retry_count uses _sum_ints so every node's retry increment accumulates.
# error uses _merge_errors so the first failure is preserved.
# Scalar fields written by every node (current_agent, final_output) use
# _last_wins to avoid INVALID_CONCURRENT_GRAPH_UPDATE errors in parallel.
from typing import TypedDict

class LangGraphState(TypedDict, total=False):
    """
    Typed state passed through LangGraph nodes.
    Annotated reducers control how parallel branch updates are merged.
    """
    task_id: str
    user_prompt: str
    current_agent: Annotated[Optional[str], _last_wins]
    messages: Annotated[List[Any], _merge_lists]
    agent_outputs: Annotated[Dict[str, Any], _merge_dicts]
    step_history: Annotated[List[Any], _merge_lists]
    final_output: Annotated[Optional[str], _last_wins]
    error: Annotated[Optional[str], _merge_errors]
    retry_count: Annotated[int, _sum_ints]
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

class CommunicationGraphBuilder:
    """
    Dynamically builds and validates an actual LangGraph StateGraph from
    an ArchitectureSpec.  Every ArchitectureSpec.agents entry becomes an
    add_node() call; every ArchitectureSpec.connections entry becomes an
    add_edge() call.
    """

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_architecture(self, architecture: ArchitectureSpec) -> None:
        """Validate topology, agent list, and connections before graph construction."""
        if not isinstance(architecture, ArchitectureSpec):
            raise ValueError("CommunicationGraphBuilder requires a valid ArchitectureSpec instance.")

        if architecture.topology not in SUPPORTED_TOPOLOGIES:
            raise ValueError(
                f"Topology '{architecture.topology.value}' is not supported. "
                f"Supported: {[t.value for t in SUPPORTED_TOPOLOGIES]}"
            )

        if not architecture.agents:
            raise ValueError(
                f"ArchitectureSpec '{architecture.architecture_id}' contains no agents."
            )

        agent_ids: Set[str] = set()
        for agent in architecture.agents:
            if agent.agent_id in agent_ids:
                raise ValueError(
                    f"Duplicate agent_id '{agent.agent_id}' in architecture "
                    f"'{architecture.architecture_id}'."
                )
            agent_ids.add(agent.agent_id)

        for conn in architecture.connections:
            if conn.source not in ("START", "__start__") and conn.source not in agent_ids:
                raise ValueError(
                    f"Connection source '{conn.source}' is not a known agent in "
                    f"architecture '{architecture.architecture_id}'."
                )
            if conn.target not in ("END", "__end__") and conn.target not in agent_ids:
                raise ValueError(
                    f"Connection target '{conn.target}' is not a known agent in "
                    f"architecture '{architecture.architecture_id}'."
                )

    # ------------------------------------------------------------------
    # Topology helpers (used for START/END wiring)
    # ------------------------------------------------------------------

    def _compute_entry_and_terminal_nodes(
        self,
        agent_ids: List[str],
        connections: list,
        topology: Optional[TopologyType] = None,
    ) -> Tuple[List[str], List[str]]:
        """
        Determine entry nodes (no incoming edges) and terminal nodes (no outgoing
        edges) from the provided connections list.  Falls back to all nodes as
        independent branches for parallel topology with empty connections, or a
        linear sequence for pipelines.
        """
        if topology == TopologyType.PARALLEL and not connections:
            # Parallel topology with no explicit connections: every agent is an
            # independent branch running in parallel (START -> each agent -> END).
            return list(agent_ids), list(agent_ids)

        targets: Set[str] = set()
        sources: Set[str] = set()

        for conn in connections:
            if conn.source not in ("START", "__start__") and conn.target not in ("END", "__end__"):
                targets.add(conn.target)
                sources.add(conn.source)

        entry_nodes = [aid for aid in agent_ids if aid not in targets]
        terminal_nodes = [aid for aid in agent_ids if aid not in sources]

        # Implicit linear pipeline: if no connections defined, treat as A->B->C...
        if not connections and len(agent_ids) > 1:
            entry_nodes = [agent_ids[0]]
            terminal_nodes = [agent_ids[-1]]

        if not entry_nodes:
            raise ValueError("No valid entry node found in graph (all nodes have incoming edges).")
        if not terminal_nodes:
            raise ValueError("No valid terminal node found in graph (all nodes have outgoing edges).")

        return entry_nodes, terminal_nodes

    # ------------------------------------------------------------------
    # Generic LangGraph node factory
    # ------------------------------------------------------------------

    def _make_node_fn(
        self,
        agent: BaseAgent,
        max_retries: int = 1,
    ) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """
        Returns a *generic* LangGraph node function for the given BaseAgent.

        The returned function is role-agnostic: the same factory pattern
        produces node functions for any agent regardless of its role.  It:

        1. Extracts the user_prompt and upstream agent_outputs from state.
        2. Builds the enriched input state for this node (injects upstream context).
        3. Calls agent.run(state) with retry logic.
        4. Returns a state *update dict* that LangGraph merges into the graph state
           (Annotated reducers handle parallel-branch merging automatically).
        """
        agent_id = agent.agent_id

        def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
            user_prompt = state.get("user_prompt", "")
            existing_agent_outputs: Dict[str, Any] = state.get("agent_outputs", {})

            # Build enriched prompt for this node if upstream outputs exist
            if existing_agent_outputs:
                context_lines = [
                    f"[{pid} Output]: {out}"
                    for pid, out in existing_agent_outputs.items()
                ]
                enriched_prompt = f"{user_prompt}\n\nUpstream Context:\n" + "\n".join(context_lines)
            else:
                enriched_prompt = user_prompt

            # State snapshot passed into the agent
            node_input_state = {
                **state,
                "current_agent": agent_id,
                "user_prompt": enriched_prompt,
            }

            # --- Execute with per-node retries ---
            attempts = 0
            last_err: Optional[str] = None
            res: Optional[Dict[str, Any]] = None
            retry_increment = 0

            while attempts <= max_retries:
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                                future = ex.submit(asyncio.run, agent.execute(node_input_state))
                                res = future.result()
                        else:
                            res = loop.run_until_complete(agent.execute(node_input_state))
                    except RuntimeError:
                        res = asyncio.run(agent.execute(node_input_state))

                    if res and res.get("status") == "completed":
                        break
                    last_err = res.get("error") if res else "Unknown error"
                except Exception as exc:
                    last_err = str(exc)
                    res = None

                attempts += 1
                retry_increment += 1
                logger.warning(
                    f"Agent '{agent_id}' attempt {attempts}/{max_retries + 1} failed: {last_err}"
                )

            # --- Build state update dict (LangGraph merges this into graph state) ---
            # NOTE: With Annotated reducers:
            #   - retry_count: return only the *increment*; _sum_ints accumulates it.
            #   - error: return step_error (may be None); _merge_errors keeps the first error.

            if res and res.get("status") == "completed":
                output_text = res.get("output", "")
                tool_calls = res.get("tool_calls", [])
                exec_time = res.get("execution_time_seconds", 0.0)
                step_status = "completed"
                step_error = None
            else:
                output_text = f"Execution failed: {last_err}"
                tool_calls = []
                exec_time = 0.0
                step_status = "failed"
                step_error = last_err

            # Build AgentStepLog as a plain dict (so it is JSON-serialisable in state)
            step_log_dict = {
                "step_id": f"step_{agent_id}",
                "agent_id": agent_id,
                "agent_role": agent.role,
                "input_state": {"user_prompt": enriched_prompt},
                "output_state": {"output": output_text},
                "tool_calls": tool_calls,
                "status": step_status,
                "execution_time_seconds": exec_time,
                "error": step_error,
            }

            # Return only the *delta* for each field; Annotated reducers merge
            # agent_outputs, step_history, messages, error, and retry_count.
            return {
                "current_agent": agent_id,
                "agent_outputs": {agent_id: output_text},   # merged by _merge_dicts
                "step_history": [step_log_dict],             # merged by _merge_lists
                "messages": [{"role": agent.role, "content": output_text}],  # merged
                "final_output": output_text,
                "error": step_error,                         # merged by _merge_errors (keeps first)
                "retry_count": retry_increment,              # merged by _sum_ints (accumulates)
            }

        # Give the inner function a meaningful __name__ for debugging
        node_fn.__name__ = f"node_{agent_id}"
        return node_fn

    # ------------------------------------------------------------------
    # Main graph builder
    # ------------------------------------------------------------------

    def build_langgraph(
        self,
        architecture: ArchitectureSpec,
        agents: Dict[str, BaseAgent],
        max_retries: int = 1,
    ):
        """
        Constructs and compiles an actual LangGraph StateGraph from an ArchitectureSpec.

        Steps (all visible for code-review / demo purposes):
          1. Validate architecture.
          2. Instantiate StateGraph.
          3. add_node() for every agent dynamically.
          4. add_edge() for every ArchitectureSpec.connection dynamically.
          5. Wire START → entry nodes and terminal nodes → END.
          6. compile() the graph.
          7. Return the compiled graph ready for invoke().

        Args:
            architecture:  Member 1 ArchitectureSpec.
            agents:        Dict[agent_id → BaseAgent] from AgentFactory.
            max_retries:   Per-node retry limit.

        Returns:
            compiled LangGraph CompiledStateGraph.
        """
        self.validate_architecture(architecture)

        agent_ids = [a.agent_id for a in architecture.agents]

        # ---- Step 1: Instantiate StateGraph with Annotated state schema ----
        # LangGraph reads Annotated[..., reducer] annotations to merge parallel
        # branch updates.  We pass our LangGraphState class which carries those
        # annotations for agent_outputs, step_history, and messages.
        logger.info(
            f"[LangGraph] Instantiating StateGraph for architecture "
            f"'{architecture.architecture_id}' ({architecture.topology.value})"
        )
        builder = StateGraph(LangGraphState)

        # ---- Step 2: add_node() for every agent (dynamically, no role checks) ----
        for agent_id in agent_ids:
            agent_obj = agents[agent_id]
            node_fn = self._make_node_fn(agent_obj, max_retries=max_retries)
            builder.add_node(agent_id, node_fn)
            logger.info(f"[LangGraph] add_node('{agent_id}')")

        # ---- Step 3: add_edge() for every ArchitectureSpec connection ----
        # Filter out any explicit START/END markers in connections.
        for conn in architecture.connections:
            src = conn.source
            tgt = conn.target
            if src in ("START", "__start__"):
                builder.add_edge(START, tgt)
                logger.info(f"[LangGraph] add_edge(START, '{tgt}')")
            elif tgt in ("END", "__end__"):
                builder.add_edge(src, END)
                logger.info(f"[LangGraph] add_edge('{src}', END)")
            else:
                builder.add_edge(src, tgt)
                logger.info(f"[LangGraph] add_edge('{src}', '{tgt}')")

        # Implicit linear pipeline when no connections provided for PIPELINE topology
        if architecture.topology == TopologyType.PIPELINE and not architecture.connections and len(agent_ids) > 1:
            for src, tgt in zip(agent_ids, agent_ids[1:]):
                builder.add_edge(src, tgt)
                logger.info(f"[LangGraph] add_edge('{src}', '{tgt}')  [auto pipeline]")

        # ---- Step 4: Wire START and END for auto-detected entry/terminal nodes ----
        entry_nodes, terminal_nodes = self._compute_entry_and_terminal_nodes(
            agent_ids, architecture.connections, topology=architecture.topology
        )

        # For nodes already connected to START/END in the loop above, skip to avoid duplicates
        already_from_start = {
            conn.target for conn in architecture.connections
            if conn.source in ("START", "__start__")
        }
        already_to_end = {
            conn.source for conn in architecture.connections
            if conn.target in ("END", "__end__")
        }

        for entry in entry_nodes:
            if entry not in already_from_start:
                builder.add_edge(START, entry)
                logger.info(f"[LangGraph] add_edge(START, '{entry}')  [auto entry]")

        for terminal in terminal_nodes:
            if terminal not in already_to_end:
                builder.add_edge(terminal, END)
                logger.info(f"[LangGraph] add_edge('{terminal}', END)  [auto terminal]")

        # ---- Step 5: compile() ----
        compiled_graph = builder.compile()
        logger.info(
            f"[LangGraph] compile() complete for architecture '{architecture.architecture_id}'"
        )

        return compiled_graph

    # ------------------------------------------------------------------
    # Legacy helper kept for backward compatibility with any external callers
    # ------------------------------------------------------------------

    def get_topology_nodes_and_edges(
        self, architecture: ArchitectureSpec
    ) -> Tuple[List[str], Dict[str, List[str]], Dict[str, int], List[str], List[str]]:
        """
        Legacy topology parsing helper (now used only for validation reporting;
        graph execution happens through build_langgraph -> compiled_graph.invoke()).
        """
        self.validate_architecture(architecture)
        agent_ids = [a.agent_id for a in architecture.agents]
        adj: Dict[str, List[str]] = {aid: [] for aid in agent_ids}
        in_degree: Dict[str, int] = {aid: 0 for aid in agent_ids}

        for conn in architecture.connections:
            if conn.source in ("START", "__start__") or conn.target in ("END", "__end__"):
                continue
            adj[conn.source].append(conn.target)
            in_degree[conn.target] += 1

        if not any(architecture.connections):
            if architecture.topology == TopologyType.PARALLEL:
                # All agents execute in parallel as independent branches (no internal edges)
                pass
            else:
                # Implicit linear pipeline
                for i in range(len(agent_ids) - 1):
                    adj[agent_ids[i]].append(agent_ids[i + 1])
                    in_degree[agent_ids[i + 1]] += 1

        entry_nodes = [aid for aid in agent_ids if in_degree[aid] == 0]
        terminal_nodes = [aid for aid in agent_ids if len(adj[aid]) == 0]
        return agent_ids, adj, in_degree, entry_nodes, terminal_nodes
