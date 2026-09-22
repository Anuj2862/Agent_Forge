# Member 2 — Agent Factory, Tools & Execution Engine

**Scope**: `app/agents/`, `app/tools/`, `app/execution/`, `app/schemas/execution.py`

---

## 1. Responsibility

Member 2 is the **execution layer** of Agent Forge. It receives an `ArchitectureSpec` produced by Member 1, turns it into a live team of agents, and runs them through a dynamically constructed **LangGraph `StateGraph`**. The result is a structured `ExecutionResult` consumed by Member 3 (Evaluator).

Member 2 does **not** generate architectures, evaluate outputs, or manage memory. Those are Member 1, 3, and 4 responsibilities respectively.

---

## 2. Execution Flow

```
ArchitectureSpec          (Member 1 output — source of truth)
        |
        v
ToolPlanner               (app/agents/tool_planner.py: plans once per architecture)
        |
        v
Tool assignments          (Dict[agent_id -> List[resolved_tool_names]])
        |
        v
AgentFactory              (app/agents/agent_factory.py)
        |
        v
Dict[agent_id -> BaseAgent]   (one per ArchitectureSpec.agents entry)
        |
        v
ToolRegistry              (retrieves executable callables by resolved name)
        |
        v
CommunicationGraphBuilder (app/execution/communication_graph.py)
   StateGraph.add_node()  -- one per agent
   StateGraph.add_edge()  -- one per connection
   StateGraph.compile()
        |
        v
compiled_graph.invoke()   (LangGraph controls execution order)
        |
        v
ExecutionResult           (app/schemas/execution.py) -> Member 3
```

No part of this flow is topology-specific in the calling code. The same `ExecutionEngine.run_architecture()` method handles both Pipeline and Parallel topologies because the topology is expressed entirely through the graph edges, not through branching Python logic.

---

## 3. Base Agent (`app/agents/base_agent.py`)

`BaseAgent` is a **role-agnostic** runtime wrapper. Every agent in an architecture — regardless of its role ("Researcher", "Writer", "Synthesizer", etc.) — is the same Python class parameterised by its `AgentConfigSchema`.

**Key attributes (sourced directly from `AgentConfigSchema`):**

| Attribute | Purpose |
|---|---|
| `agent_id` | Unique identifier used as the LangGraph node name |
| `role` | Human-readable role label (not used for branching logic) |
| `objective` | Plain-text goal injected as context |
| `system_prompt` | Prefix passed to the LLM on every call |
| `tools` | List of resolved callable tool functions |
| `input_keys` / `output_keys` | Optional state keys to read from / write to |

**LLM resolution order** (inside `_call_llm`):

1. Injected `llm_runner` callable — used in tests and the demo script.
2. Live Gemini API (`google-genai`) if `GEMINI_API_KEY` is set in the environment.
3. Deterministic mock response — used automatically when neither is present.

**`execute(state)`** returns:

```python
{
    "agent_id": str,
    "output": str,          # LLM response text
    "tool_calls": list,     # log of tool invocations with results
    "status": "completed" | "failed",
    "execution_time_seconds": float,
    "error": str | None,
}
```

---

## 4. Tool Planner (`app/agents/tool_planner.py`)

`ToolPlanner` plans and resolves concrete tool requirements for agents across an `ArchitectureSpec`:

**Primary method:**
```python
planner = ToolPlanner(registry=tool_registry)
assignments = planner.plan(architecture)
# returns Dict[agent_id -> List[str]] (resolved tool names)
```

**Resolution Rules:**
- **Mapped capabilities**:
  - `code_execution` -> `python_tool`
  - `information_retrieval` -> `document_retriever`
  - `web_search` -> `web_search`
  - `python_tool` -> `python_tool`
  - `document_retriever` -> `document_retriever`
- **Direct registered tools**: Validated directly against `ToolRegistry.has_tool()`.
- **Non-executable capabilities**: `data_analysis`, `data_loading`, `table_generation` represent analytical/cognitive capabilities and are ignored for executable tool assignment without raising errors.
- **Unknown executable tools/capabilities**: Raise `ToolResolutionError` (subclass of `ValueError`).
- **Deduplication**: Preserves insertion order while eliminating duplicate tool assignments for each agent.

---

## 5. Agent Factory (`app/agents/agent_factory.py`)

`AgentFactory` converts `ArchitectureSpec` agent definitions into executable `BaseAgent` instances using `ToolPlanner`. There are no hard-coded role checks or if/else branches for specific agent types.

**Primary method:**

```python
factory = AgentFactory(registry=tool_registry, planner=tool_planner)
agents = factory.create_from_architecture(architecture, llm_runner=None)
# returns Dict[agent_id -> BaseAgent]
```

Internally, `create_from_architecture()` calls `ToolPlanner.plan(architecture)` **once** for the entire architecture, obtaining the `{agent_id: [tool_names]}` assignment mapping, and instantiates each `BaseAgent` with callables retrieved from `ToolRegistry`.

**Validation performed:**

- `AgentConfigSchema` is a valid Pydantic model instance.
- `agent_id` is a non-empty string.
- `role` is a non-empty string.
- No duplicate `agent_id` values within the same team.
- Every executable tool or capability must be resolvable via `ToolPlanner` / `ToolRegistry` (raises `ToolResolutionError` if unknown).

---

## 6. Tool Registry (`app/tools/tool_registry.py`)

`ToolRegistry` is a simple name → callable dictionary with explicit register/get/list operations. A single global singleton `tool_registry` is auto-populated at import time from `app/tools/__init__.py`.

```python
from app.tools import tool_registry
tool_registry.list_tools()  # ["web_search", "python_tool", "document_retriever"]
```

**Registered tools:**

### `web_search` — `web_search_tool(query, num_results=5)`

Executes a web search. Checks `TAVILY_API_KEY`, `SERPER_API_KEY`, and `settings.SEARCH_API_KEY`. Behaviour depends on environment:

- **With `TAVILY_API_KEY`**: Makes a real HTTP POST to `api.tavily.com/search` via `httpx`. Returns up to `num_results` structured results with `title`, `snippet` (from `content`), and `url`.
- **With other keys (e.g. `SERPER_API_KEY`, `settings.SEARCH_API_KEY`) without `TAVILY_API_KEY`**: Returns `status: "no_credentials"`, `results: []`, and `error: "Unconfigured search provider."`.
- **Without any API key**: Returns a `status: "no_credentials"` response with a single offline placeholder result. Does **not** raise an exception, so agents that invoke it still receive a structured result and continue executing.

```python
# Example return (no API key):
{
    "status": "no_credentials",
    "query": "...",
    "results": [
        {
            "title": "Offline Result for '...'",
            "snippet": "No external search API key configured (TAVILY_API_KEY/SERPER_API_KEY). Query: ...",
            "url": "https://example.com/offline-search"
        }
    ],
    "error": "No SEARCH_API_KEY or TAVILY_API_KEY configured in environment."
}
```

### `python_tool` — `python_interpreter_tool(code)`

Executes a Python code string in an isolated local namespace. Captures `stdout` and returns the result.

**Safety**: AST-based pre-execution check blocks imports of: `os`, `sys`, `subprocess`, `shutil`, `socket`, `builtins`, `importlib`, `pty`, `commands`. Prohibited attribute access (`.system`, `.popen`, `.rmtree` etc.) is also blocked.

**Limitation**: The sandbox is AST-based, not a true OS-level sandbox. It prevents obvious shell escapes but is not hardened against all adversarial inputs. It is suitable for the current project scope.

Execution strategy: tries `eval()` first (expressions), falls back to `exec()` (statements). Multi-line statement output is captured via `sys.stdout` redirect; the `result` local variable is also checked.

### `document_retriever` — `document_retriever_tool(query, top_k=3)`

A **prototype stub**. Returns synthesised placeholder documents with a simulated relevance score. It does not connect to a real vector store or file system. Its purpose is to occupy a slot in the tool registry so agents that request it receive a well-structured result rather than an error.

---

## 6. Execution Schemas (`app/schemas/execution.py`)

### `ExecutionStatus` (enum)

```python
PENDING | RUNNING | SUCCESS | FAILED | MAX_ITERATIONS_REACHED
```

### `AgentStepLog` (Pydantic `BaseModel`)

Records a single agent execution step. Stored in `ExecutionResult.step_history`.

| Field | Type | Description |
|---|---|---|
| `step_id` | `str` | Identifier for the step, e.g. `"step_researcher"` |
| `agent_id` | `str` | Executing agent |
| `agent_role` | `str \| None` | Role label |
| `timestamp` | `datetime` | UTC timestamp (auto-set) |
| `input_state` | `dict` | Enriched prompt received by the agent (including upstream context) |
| `output_state` | `dict` | `{"output": "<llm response text>"}` |
| `tool_calls` | `list` | Tool invocation log with tool name, input, result, status |
| `status` | `str` | `"completed"` or `"failed"` |
| `execution_time_seconds` | `float` | Wall-clock duration |
| `error` | `str \| None` | Error message if status is `"failed"` |

### `ExecutionState` (TypedDict)

The runtime state dict passed through LangGraph. Used as the source of truth during graph execution.

```python
class ExecutionState(TypedDict, total=False):
    task_id: str
    user_prompt: str
    current_agent: str | None
    messages: list
    agent_outputs: dict      # {agent_id -> output_text}
    step_history: list       # list of AgentStepLog dicts
    final_output: str | None
    error: str | None
    retry_count: int
    metadata: dict
```

### `LangGraphState` (TypedDict with Annotated reducers)

The actual schema passed to `StateGraph`. Extends `ExecutionState` with Annotated field reducers that control how LangGraph merges state updates from concurrent parallel branches:

| Field | Reducer | Effect |
|---|---|---|
| `agent_outputs` | `_merge_dicts` | Both parallel branches' outputs are merged into one dict |
| `step_history` | `_merge_lists` | All step logs concatenated; none overwritten |
| `messages` | `_merge_lists` | All message entries concatenated |
| `error` | `_merge_errors` | First non-None error is retained |
| `retry_count` | `_sum_ints` | Retry increments accumulated across all nodes |
| `current_agent` | `_last_wins` | Avoids `INVALID_CONCURRENT_GRAPH_UPDATE` for scalar fields |
| `final_output` | `_last_wins` | Last-written value wins (terminal node wins) |

**Why reducers?** LangGraph requires that fields updated by multiple concurrent branches declare how to merge their updates. Without reducers, parallel branches that both write to `agent_outputs` would raise `INVALID_CONCURRENT_GRAPH_UPDATE`. The `_merge_dicts` reducer makes both branches' entries coexist in the dict.

### `ExecutionResult` (Pydantic `BaseModel`)

The final output of `ExecutionEngine`. Consumed by Member 3 (Evaluator).

| Field | Type | Description |
|---|---|---|
| `execution_id` | `str` | Unique execution instance ID |
| `task_id` | `str` | From `ArchitectureSpec.task_id` |
| `architecture_id` | `str` | From `ArchitectureSpec.architecture_id` |
| `status` | `ExecutionStatus` | `SUCCESS` or `FAILED` |
| `final_output` | `str \| None` | Output of the terminal agent(s) |
| `step_history` | `list[AgentStepLog]` | All steps in execution order |
| `total_steps` | `int` | Number of agent steps completed |
| `execution_time_seconds` | `float` | Total wall-clock duration |
| `agent_count` | `int` | Unique agents that participated |
| `tool_call_count` | `int` | Total tool invocations across all steps |
| `error` | `str \| None` | Global error description if execution failed |
| `metadata` | `dict` | `{"topology": "pipeline"|"parallel", "retry_count": int}` |

---

## 7. Dynamic LangGraph Execution Engine

### Files

| File | Responsibility |
|---|---|
| `app/execution/communication_graph.py` | Builds the `StateGraph` from `ArchitectureSpec` |
| `app/execution/execution_engine.py` | Orchestrates the full flow; calls `invoke()` |
| `app/execution/pipeline_executor.py` | Thin wrapper delegating to `ExecutionEngine` |
| `app/execution/parallel_executor.py` | Thin wrapper delegating to `ExecutionEngine` |

### How `ArchitectureSpec` becomes a `StateGraph`

**`CommunicationGraphBuilder.build_langgraph(architecture, agents)`** performs these steps in order:

**Step 1 — Validate** the architecture (topology supported, no duplicate agent IDs, all connection endpoints exist).

**Step 2 — Instantiate `StateGraph`:**
```python
builder = StateGraph(LangGraphState)
```

**Step 3 — `add_node()` for every agent** (dynamic, no role checks):
```python
for agent_id in [a.agent_id for a in architecture.agents]:
    node_fn = self._make_node_fn(agents[agent_id], max_retries=max_retries)
    builder.add_node(agent_id, node_fn)
```
`_make_node_fn()` returns a generic closure that calls `agent.execute(state)` with retry logic and returns the state delta dict. Every agent gets the same node factory; the agent's `role` is not used to dispatch different logic.

**Step 4 — `add_edge()` for every `ArchitectureSpec.connection`:**
```python
for conn in architecture.connections:
    builder.add_edge(conn.source, conn.target)
```

**Step 5 — Auto-wire `START` and `END`:**

Entry nodes (no incoming edges from other agents) get `add_edge(START, node)`.  
Terminal nodes (no outgoing edges to other agents) get `add_edge(node, END)`.

**Step 6 — `compile()`:**
```python
compiled_graph = builder.compile()
```

**Step 7 — Return** the compiled graph to `ExecutionEngine`.

### How `ExecutionEngine` runs the graph

```python
# app/execution/execution_engine.py — run_architecture()

compiled_graph = self.graph_builder.build_langgraph(architecture, agents)

initial_state = {
    "task_id": architecture.task_id,
    "user_prompt": input_data["user_prompt"],
    "agent_outputs": {},
    "step_history": [],
    "messages": [],
    "retry_count": 0,
    ...
}

final_state = compiled_graph.invoke(initial_state)   # LangGraph controls execution
result = self._build_result(final_state, ...)
```

Execution order, parallelism, and fan-in are handled entirely by LangGraph's compiled graph traversal. There is no manual DAG loop in `ExecutionEngine`.

---

## 8. Pipeline Topology Example

**Architecture:** `A → B → C`

```
ArchitectureSpec.agents      = [A, B, C]
ArchitectureSpec.connections = [A→B, B→C]

LangGraph graph built:
  START → A → B → C → END

Execution order: A, then B (receives A's output), then C (receives A+B outputs).
final_output = C's response.
```

Each downstream agent receives all prior `agent_outputs` as "Upstream Context" injected into its prompt before the LLM call.

---

## 9. Parallel Topology Example

**Architecture:** `Root → (B, C) → Join`

```
ArchitectureSpec.connections = [Root→B, Root→C, B→Join, C→Join]

LangGraph graph built:
  START → Root → B  ─┐
                   C  ┴→ Join → END

Execution: Root runs first.
           LangGraph fans out: B and C execute (order determined by LangGraph internals).
           _merge_dicts reducer merges B's and C's agent_outputs.
           Join receives both branch outputs in its agent_outputs snapshot.
           Join's prompt contains:
               [B Output]: MockOutput::branch_b
               [C Output]: MockOutput::branch_c
           final_output = Join's response.
```

The reducer-based merge is the key mechanism. Neither branch overwrites the other in `agent_outputs`; `_merge_lists` ensures both branch step logs appear in `step_history`.

---

## 10. Retries and Failure Handling

**Per-node retry logic** is inside `_make_node_fn()` in `communication_graph.py`.

```
max_retries = 1  (default)

Attempt 1: call agent.execute(state)
  -> if status == "completed": break
  -> if exception or status != "completed": log warning, retry_increment += 1

Attempt 2 (if max_retries >= 1): retry same agent
  -> if success: break
  -> if still failing: mark step as "failed", set step_error
```

**Failure capture:**

- A failed step sets `step_status = "failed"` and `step_error = <error message>`.
- The node still returns a state update dict (it does not raise). LangGraph continues to the next node.
- `_merge_errors` reducer preserves the first error in the final state.
- `_build_result()` detects `any_failed` in `step_history` and sets `ExecutionResult.status = FAILED`.
- `ExecutionResult.error` contains the error text.
- `ExecutionResult.final_output` contains `"Execution failed: <error>"`.

**Retry count** accumulates across all nodes via `_sum_ints` reducer and is reported in `ExecutionResult.metadata["retry_count"]`.

---

## 11. ExecutionResult — Downstream Contract

`ExecutionResult` is the single output object that `ExecutionEngine` produces. Member 3 (Evaluator) consumes it via `app/schemas/execution.py` which is shared.

Member 3 can read:

| What M3 needs | Where it is |
|---|---|
| Whether execution succeeded | `result.status` |
| The final agent output text | `result.final_output` |
| Per-step details (who ran, what output, errors) | `result.step_history` |
| Total time taken | `result.execution_time_seconds` |
| How many agents participated | `result.agent_count` |
| How many tools were invoked | `result.tool_call_count` |
| Which topology was used | `result.metadata["topology"]` |
| Any retry overhead | `result.metadata["retry_count"]` |

Member 3 does **not** need to know about `LangGraphState`, `AgentFactory`, or `CommunicationGraphBuilder`.

---

## 12. Tests

**Result: `42 passed`** (no external services required; all LLM calls are mocked).

Run with:
```bash
pytest tests/ -q
```

| Test file | Coverage area |
|---|---|
| `tests/test_schemas.py` | `AgentStepLog`, `ExecutionState`, `ExecutionResult`, `EvaluationResult`, `ReflectionResult` field validation and M3 compatibility |
| `tests/test_tools.py` | `ToolRegistry` (register, get, list, duplicate prevention, unknown key), `web_search_tool` (offline fallback, HTTP mock, failure), `python_interpreter_tool` (expressions, statements, stdout capture, security block, errors) |
| `tests/test_factory.py` | `BaseAgent` creation, mock LLM injection, error propagation; `AgentFactory` single/team creation, duplicate ID rejection, unknown tool rejection, same factory handling two architectures |
| `tests/test_engine.py` | 2-agent pipeline (order + context propagation), 4-agent pipeline, parallel DAG (fan-in state merging), **mid-sem demo: two different architectures on same engine**, invalid connection validation, agent failure capture, per-node retry recovery, multiple terminal node aggregation, `PipelineExecutor`/`ParallelExecutor` wrappers |

---

## 13. Demo Script

**Location:** `docs/demo_member2.py`

**Run from project root:**
```bash
python -m docs.demo_member2
```

The demo runs both architectures end-to-end using the public API with no mocking of the engine or graph builder. It validates:

1. **Pipeline** (`researcher → writer`) — 2 agents, LangGraph introspection printed, upstream context propagation asserted.
2. **Parallel** (`root_planner → branch_security, branch_ethics → join_synthesizer`) — 4 agents, LangGraph introspection printed, branch state merging asserted.
3. **Same engine instance** — both architectures called on the same `ExecutionEngine` object (object ID printed for verification).
4. **LangGraph call log** — `StateGraph`, `add_node`, `add_edge`, `compile`, `invoke` calls are logged at `INFO` level and summarised in Section 4 output.
5. **Branch merging** — `join_synthesizer` input prompt is printed, showing both branch outputs present.

All assertions are enforced with `assert` statements; the script exits non-zero if any fail.

---

## 14. Limitations

The following limitations are present in the current implementation:

1. **`document_retriever_tool` is a stub.** It returns synthetic placeholder documents. It is not connected to a vector store, file system, or retrieval index.

2. **`web_search_tool` checks `TAVILY_API_KEY`, `SERPER_API_KEY`, and `settings.SEARCH_API_KEY`.** Currently, only `TAVILY_API_KEY` has an active HTTP provider implementation (Tavily search API). Without configured credentials, it returns a graceful offline `no_credentials` placeholder response rather than raising an exception.

3. **Python interpreter sandbox is AST-based only.** It blocks common shell-escape patterns but is not a hardened OS-level sandbox. Adversarial inputs could potentially bypass it.

4. **No streaming output.** `ExecutionEngine.run_architecture()` is synchronous and returns only after all agents complete. There is no incremental result streaming.

5. **Parallel execution order within a level is non-deterministic.** LangGraph controls which of two parallel branches (`branch_security` / `branch_ethics`) runs first. Both will always complete before `join_synthesizer` fires, but their relative step order in `step_history` may vary between runs.

6. **Supported topologies: PIPELINE and PARALLEL. HYBRID, DEBATE, TREE, and BLACKBOARD are not implemented.** Passing unsupported topologies will raise a `ValueError` from `CommunicationGraphBuilder.validate_architecture()`.

7. **`llm_runner` injection is a test convenience.** In a live environment where no `llm_runner` is provided and no `GEMINI_API_KEY` is set, agents fall back to the deterministic mock response. This is intentional for offline testing.
