# REAL-TIME EXPERIMENT STREAMING & LIVE EXECUTION IMPLEMENTATION PLAN

**Research Thesis**: *Failure-Driven, Constraint-Aware Self-Evolution of Multi-Agent Architectures*  
**Date**: 2026-10-24  
**Author**: Antigravity (Agent Forge Core)  
**Target Repository**: `https://github.com/Anuj2862/Agent_Forge` (`/Users/anuj/Desktop/EDI-5`)

---

## 1. Executive Summary & Objective

Agent Forge requires a production-quality, real-time experiment execution experience. While the platform previously established SQLAlchemy persistence, centralized architecture validation, deterministic evolution decision policies, and a research-lab UI, executions were executed as blocking requests where intermediate agent thought steps, tool calls, and state transitions were only visible post-hoc.

This implementation introduces:
1. A **durable execution event model** (`ExecutionEventORM` and Pydantic `ExecutionEvent`) with monotonic sequence numbers, distinct event types, and structured payloads.
2. A **Server-Sent Events (SSE) streaming transport** (`GET /execution/{execution_id}/events`) with reconnection, resume from sequence number (`Last-Event-ID` / `?after_seq=N`), keepalives, and clean disconnection.
3. An **in-process Event Hub / Broadcaster** decoupled from DB writes to stream real-time events as LangGraph agents and tools execute.
4. **Lifecycle Event Production** integrated into `ExecutionEngine`, `CommunicationGraphBuilder`, `BaseAgent`, and evaluation/evolution routes.
5. A redesigned **Live Execution Experience** in the Next.js frontend (`ExecutionTimeline.tsx`, `LiveExecutionStatus.tsx`, and `/execution` + `/run/[task_id]` workbench integration) featuring real-time event ordering, collapsible payload inspectors, connection recovery, and zero fabricated fallbacks.

---

## 2. Current Architecture Baseline

### 2.1 Backend Pipeline
- **API Framework**: FastAPI `v0.2.0` with CORS enabled for `localhost:3000`.
- **Database & Persistence**: SQLAlchemy async engine (`sqlite+aiosqlite`) with ORM models for `tasks`, `architectures`, `executions`, `evaluations`, and `evolution_decisions`.
- **Execution Orchestration**: LangGraph `StateGraph` compiled by `CommunicationGraphBuilder` and executed by `ExecutionEngine`. Each agent is a node function executing `BaseAgent.execute()`.
- **Tool Dispatch**: In `BaseAgent.execute()`, intentional tool matching executes tools like `python_interpreter` (in a hardened subprocess sandbox) and `web_search`.
- **Baseline Test Suite**: 150/150 tests passing in pytest (`tests/`).

### 2.2 Frontend Framework
- **Framework**: Next.js 16.3.5 (Turbopack) with React 19.
- **Design Tokens**: Standardized research-lab dark slate theme (`#080c16`, `#0f172a`, `#1e293b`) with semantic status colors (`ACCEPTED`, `REJECTED`, `INCONCLUSIVE`).
- **Pages**: 12 static/dynamic routes including `/`, `/architecture`, `/execution`, `/diagnosis`, `/evaluation`, `/evolution`, `/history`, `/memory`, `/settings`, and `/run/[task_id]`.
- **Baseline Lint/Build**: 0 ESLint errors, Next.js build passes 12/12 routes.

---

## 3. Gap Analysis & Missing Capabilities

| Capability | Current State | Required State |
| :--- | :--- | :--- |
| **Streaming Transport** | None. Client waits for blocking POST response. | SSE endpoint `GET /execution/{execution_id}/events` supporting real-time streaming, keepalives, and clean disconnects. |
| **Event Persistence** | `ExecutionRecordORM` stores only final JSON blob. | `ExecutionEventORM` table storing indexed, monotonic events surviving server restarts. |
| **Sequence & Reconnection** | No sequence tracking. | Monotonic sequence numbers with `Last-Event-ID` / `?after_seq=N` resume. |
| **Intermediate Telemetry** | Tool calls & agent steps only recorded in final step logs. | Real-time events emitted when agents start, tools invoke, tools return, and stages complete. |
| **Frontend Timeline** | Static `ExecutionTimeline` displaying post-run `AgentLog[]`. | Live timeline component with SSE connection state, deduplication, chronological sorting, and event inspector. |
| **Workflow Agreement** | Polling or batch waiting. | Coordinated state between SSE stream, database records, and UI workbench. |

---

## 4. Proposed Event Lifecycle & Taxonomy

The event taxonomy maps directly to genuine lifecycle transitions in Agent Forge:

```
[execution.queued]
       │
[execution.started]
       │
[execution.stage_started (stage: graph_compilation)]
       │
[execution.stage_completed (stage: graph_compilation)]
       │
[execution.stage_started (stage: agent_execution)]
       │
   ┌───┴───────────────────────────────┐
   │ Loop over LangGraph Agent Nodes   │
   │                                   │
   │  [agent.started]                  │
   │     │                             │
   │     ├─ [tool.started]             │
   │     ├─ [tool.completed / failed]  │
   │     │                             │
   │  [agent.completed]                │
   └───┬───────────────────────────────┘
       │
[execution.stage_completed (stage: agent_execution)]
       │
[evaluation.started] (when evaluation begins)
       │
[evaluation.completed] (with rubric metrics)
       │
[evolution.proposed] (when mutation is drafted)
       │
[evolution.validated] (constraint compliance)
       │
[evolution.accepted / rejected] (deterministic verdict)
       │
[execution.completed / failed] (terminal state)
```

### Event Payload Schema
- `event_id`: Unique string (`evt_<uuid>`)
- `execution_id`: Target execution identifier
- `task_id`: Parent task identifier
- `sequence_number`: Monotonic positive integer (1, 2, 3...)
- `event_type`: Category identifier from taxonomy
- `timestamp`: UTC ISO-8601 string
- `status`: Execution state (`queued`, `running`, `completed`, `failed`, `cancelled`)
- `agent_id`: Identifier of agent (when applicable)
- `stage`: Lifecycle stage (`synthesis`, `graph_compilation`, `agent_execution`, `evaluation`, `reflection`, `evolution_decision`)
- `message`: User-safe descriptive message
- `data`: Arbitrary JSON payload with sanitized parameters and metrics
- `error`: Optional sanitized error message

---

## 5. Streaming Transport Design (SSE)

### Why Server-Sent Events (SSE)?
1. **Unidirectional Telemetry**: The client only needs to receive events from the execution engine; execution commands (run, mutate, evaluate) are already handled via standard HTTP POST APIs.
2. **Built-in Reconnection**: Native browser `EventSource` automatically handles reconnection and transmits `Last-Event-ID`.
3. **HTTP/2 & Proxy Compatibility**: Runs over standard HTTP without WebSocket handshake complexities or firewall blockades.
4. **Resilience**: Simple text protocol (`event: <type>\ndata: <json>\nid: <seq>\n\n`) allowing easy debugging and inspection.

### Endpoint Specification
`GET /execution/{execution_id}/events`
- **Query Parameters**:
  - `after_seq`: Optional integer. If provided, stream only events with `sequence_number > after_seq`.
- **Headers**:
  - `Last-Event-ID`: Standard SSE header used as fallback for `after_seq`.
  - `Accept: text/event-stream`
- **Flow**:
  1. Validate execution existence in database or active store.
  2. Query `ExecutionEventORM` for all events with `sequence_number > after_seq`. Stream them immediately to the client.
  3. If execution is already in a terminal state (`completed`, `failed`), send a final terminal event and close cleanly.
  4. If execution is `running` or `queued`, subscribe to the in-memory `ExecutionEventBroadcaster` for live events.
  5. As live events arrive, format as SSE messages and yield to client.
  6. Send `: keepalive\n\n` comments every 15 seconds to prevent connection timeouts.
  7. When terminal event is received or client disconnects, unsubscribe and close cleanly.

---

## 6. Persistence & Concurrency Strategy

### 6.1 Database Model (`ExecutionEventORM`)
```python
class ExecutionEventORM(Base):
    __tablename__ = "execution_events"

    event_id = Column(String(64), primary_key=True, index=True)
    execution_id = Column(String(64), ForeignKey("executions.execution_id"), index=True, nullable=False)
    task_id = Column(String(64), index=True, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    event_type = Column(String(64), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=_utc_now)
    status = Column(String(32), nullable=False, default="running")
    agent_id = Column(String(64), nullable=True)
    stage = Column(String(64), nullable=False, default="agent_execution")
    message = Column(Text, nullable=False)
    data_json = Column(Text, nullable=False, default="{}")
    error = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_exec_events_seq", "execution_id", "sequence_number", unique=True),
    )
```

### 6.2 Atomic Sequence Assignment
- Each execution maintains an atomic sequence counter managed within `DatabaseRepository.save_execution_event()`.
- Sequence numbers start at `1` and increment monotonically per execution.
- Events are persisted before or concurrently with broadcast, guaranteeing that any reconnecting client receives all missed events from the database.

---

## 7. Frontend Integration Strategy

### 7.1 Reusable Components
1. **`ExecutionTimeline.tsx`**:
   - Upgraded to support both live streaming via SSE and static replay from stored logs.
   - Shows chronological events with sequence badges, status dots, elapsed timestamps, and collapsible payload drawers.
   - Handles empty, loading, reconnecting, and error states gracefully.
2. **`LiveExecutionStatus.tsx`**:
   - Displays execution ID, current status badge, active stage, total event count, and SSE connection pulse (`CONNECTED`, `RECONNECTING`, `TERMINAL`).
3. **Workbench Integration (`frontend/app/run/[task_id]/page.tsx` & `/execution/page.tsx`)**:
   - Automatically opens SSE stream when an execution is running or selected.
   - Displays real-time progress as agents run.
   - Automatically populates evaluation and evolution comparison when terminal events arrive.

---

## 8. Test & Verification Plan

### Backend Unit Tests (`tests/test_execution_events.py`)
- Event schema validation and serialization.
- Sequence assignment atomicity.
- Database persistence and historical replay.
- Error message sanitization (preventing secret leakage).

### Backend API Tests (`tests/test_event_streaming_api.py`)
- Unknown execution returns 404.
- SSE stream yields valid headers and format.
- Reconnection with `after_seq` replays only new events.
- Terminal execution completes stream cleanly.

### End-to-End Integration Tests
- Submit task → initiate execution → stream events → verify ordering → restart server → reconnect and verify full event recovery.

### Frontend Quality Gates
- `npm run lint` passes with 0 errors.
- `npm run build` passes for all 12 routes.

---

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Memory Leak from Unbounded Broadcaster** | Server memory grows with dangling subscribers. | Weak references or explicit cleanup upon client disconnect; subscriber queues bounded to 100 items with timeout. |
| **Database Lock Contention** | Event writes block agent execution. | Asynchronous write with session flushes; minimal indexing. |
| **Client Reconnect Duplication** | Events render twice in UI. | Frontend deduplication using `event_id` and monotonic `sequence_number` set. |
| **Leaking Secrets or Private Prompts** | Security vulnerability. | Input/output sanitization filter stripping environment variables, API keys, and internal traces before event creation. |
