# Agent Forge — Real-Time Execution Streaming Operations Guide

## 1. Overview & Architecture

Agent Forge implements a real-time event-streaming architecture designed for multi-agent execution telemetry and evolutionary lifecycle tracking.

The real-time streaming pipeline consists of four decoupled layers:

```
[Agent Execution / LangGraph Engine]
                 │
                 ▼
     [ExecutionEventEmitter]
        ├── Persist ──► [ExecutionEventORM (DB)]
        └── Broadcast ► [EventBroadcaster (In-Memory Pub/Sub)]
                               │
                               ▼
               [GET /execution/{id}/events (SSE)]
                               │
                               ▼
        [Frontend: EventSource / LiveExecutionStatus / Timeline]
```

### Key Capabilities
- **Transport**: Server-Sent Events (SSE) via FastAPI `StreamingResponse(media_type="text/event-stream")`.
- **Durable Persistence**: Every event is written atomically to `ExecutionEventORM` in PostgreSQL or SQLite.
- **Monotonic Ordering**: Each event carries a strictly increasing integer `sequence_number` per execution.
- **Resilient Reconnection**: Clients can reconnect via standard HTTP `Last-Event-ID` header or `?after_seq=N` query parameter. Replays historical events from database before seamlessly joining the live broadcaster queue.
- **Payload Sanitization**: `sanitize_payload()` scrubs all sensitive environment variables, credentials, bearer tokens, and private keys before events leave the process boundary.

---

## 2. API Reference

### 2.1 Start Execution Asynchronously
- **Endpoint**: `POST /execution/start`
- **Request Body**:
```json
{
  "task_id": "task_abc123",
  "architecture_id": "architecture_xyz789",
  "run_number": 1,
  "use_real_engine": true
}
```
- **Response**: `200 OK`
```json
{
  "execution_id": "exec_4f92d1",
  "task_id": "task_abc123",
  "architecture_id": "architecture_xyz789",
  "run_number": 1,
  "status": "running",
  "stream_url": "/execution/exec_4f92d1/events"
}
```

### 2.2 Live Event Stream (SSE)
- **Endpoint**: `GET /execution/{execution_id}/events`
- **Headers**:
  - `Accept: text/event-stream`
  - `Last-Event-ID`: Optional last received integer sequence number.
- **Query Parameters**:
  - `after_seq`: Optional integer sequence number (default `0`).
- **SSE Format**:
```
id: 1
event: execution.queued
data: {"event_id": "evt_...", "execution_id": "exec_4f92d1", "sequence_number": 1, "event_type": "execution.queued", ...}

: keepalive

id: 2
event: execution.started
data: {"event_id": "evt_...", ...}
```
- **Keepalive**: Emits `: keepalive\n\n` comments every 15 seconds of inactivity to prevent proxy/load balancer disconnects.

### 2.3 Persisted Event History (JSON)
- **Endpoint**: `GET /execution/{execution_id}/events/history`
- **Query Parameters**:
  - `after_seq`: Return events with sequence numbers strictly greater than this (default `0`).
  - `limit`: Maximum events to return (default `500`).
- **Response**: `200 OK`
```json
{
  "execution_id": "exec_4f92d1",
  "count": 7,
  "events": [
    {
      "event_id": "evt_d5b5a548331a",
      "execution_id": "exec_4f92d1",
      "task_id": "task_abc123",
      "sequence_number": 1,
      "event_type": "execution.queued",
      "timestamp": "2026-10-24T07:49:08.067476",
      "status": "running",
      "stage": "synthesis",
      "message": "Execution 'exec_4f92d1' queued for task 'task_abc123'",
      "data": {"run_number": 1, "agent_count": 2},
      "error": null
    }
  ]
}
```

---

## 3. Event Taxonomy & Stages

| Event Type | Stage | Meaning |
|---|---|---|
| `execution.queued` | `synthesis` | Execution initialized and registered in database. |
| `execution.started` | `synthesis` | Execution engine active, architecture validated. |
| `execution.stage_started` | `graph_compilation` / `agent_execution` | A named execution phase has started. |
| `execution.stage_completed` | `graph_compilation` / `agent_execution` | A named execution phase finished. |
| `agent.started` | `agent_execution` | Specific agent dispatched. |
| `tool.started` | `agent_execution` | Tool invocation initiated. |
| `tool.completed` | `agent_execution` | Tool invocation finished successfully. |
| `tool.failed` | `agent_execution` | Tool invocation raised an error or timed out. |
| `agent.completed` | `agent_execution` | Agent task complete and output generated. |
| `evaluation.started` | `evaluation` | Evaluator measuring task success rate and constraints. |
| `evaluation.completed` | `evaluation` | Metrics computed and persisted. |
| `evolution.proposed` | `reflection` | Failure diagnosed and architecture mutation proposed. |
| `evolution.validated` | `reflection` | Candidate architecture validated against constraints. |
| `evolution.accepted` | `reflection` | Candidate promoted to `v2`. |
| `evolution.rejected` | `reflection` | Candidate rejected due to constraint violation. |
| `execution.completed` | `agent_execution` / `synthesis` | Terminal success state for the run. |
| `execution.failed` | `agent_execution` / `synthesis` | Terminal failure state with sanitized error payload. |
| `execution.cancelled` | `agent_execution` / `synthesis` | Terminal cancellation state. |

---

## 4. Reconnection & Client Recovery Runbook

1. **Client Startup**:
   - Call `GET /execution/{execution_id}/events/history` to prime local state.
   - If execution status is not terminal (`status === "running"`), open `EventSource` to `/execution/{execution_id}/events?after_seq={last_seq}`.
2. **On Message**:
   - Check if `event_id` already exists in timeline; deduplicate if seen.
   - Update `last_seq = max(last_seq, event.sequence_number)`.
   - On terminal event (`execution.completed`, `execution.failed`, `execution.cancelled`), close `EventSource` connection.
3. **On Network Drop**:
   - Browser `EventSource` automatically reconnects with `Last-Event-ID: {last_seq}`.
   - The backend reads `Last-Event-ID`, replays missing events from DB, then attaches back to broadcaster queue.

---

## 5. Security & Data Protection Guarantees

- **Credential Redaction**: Recursive scrubber scans all payload keys for:
  - `*api_key*`, `*token*`, `*secret*`, `*password*`, `*credential*`, `*auth*`, `*private*`.
  - Matching values are replaced with `"[REDACTED]"`.
- **Sandbox Preservation**: Tool executions and Python sandbox execution timeouts and limits remain strictly enforced.
- **Trace Sanitization**: Raw system stack traces are logged on the server and sanitized before sending in `error` fields to clients.

---

## 6. Verification Commands

```bash
# 1. Run all backend unit and API tests
pytest

# 2. Check frontend linting
cd frontend && npm run lint

# 3. Check frontend production compilation
cd frontend && npm run build

# 4. Run end-to-end streaming verification test
python3 scratch/verify_live_stream.py
```
