# AGENT FORGE — EXECUTION EVENT SCHEMA & TAXONOMY

**Repository**: `https://github.com/Anuj2862/Agent_Forge`  
**Thesis**: *Failure-Driven, Constraint-Aware Self-Evolution of Multi-Agent Architectures*  
**Specification Version**: 1.0.0  
**Transport Protocol**: Server-Sent Events (SSE) / JSON REST Replay  

---

## 1. Overview

Agent Forge uses a strongly typed, deterministic execution event model to communicate real-time lifecycle transitions across the multi-agent execution pipeline. Events are emitted directly by the execution engine, persisted durably to SQLite with monotonic sequence numbers, and streamed to web clients using standard Server-Sent Events.

---

## 2. Event Model Specification

Each event follows this JSON structure:

```json
{
  "event_id": "evt_4f89b9a2c1d448",
  "execution_id": "exec_d7e21a80",
  "task_id": "task-25",
  "sequence_number": 3,
  "event_type": "tool.started",
  "timestamp": "2026-10-24T07:15:20.123456Z",
  "status": "running",
  "agent_id": "agent_data_analyst",
  "stage": "agent_execution",
  "message": "Invoking python_interpreter with calculation script",
  "data": {
    "tool": "python_interpreter",
    "input_preview": "result = 42 * 1.05",
    "timeout_seconds": 5
  },
  "error": null
}
```

### Field Definitions

| Field | Type | Description |
| :--- | :--- | :--- |
| `event_id` | `string` | Unique identifier prefixed with `evt_` and a 16-character hex UUID. |
| `execution_id` | `string` | ID of the parent execution run (`exec_...`). |
| `task_id` | `string` | ID of the parent task being solved (`task-...`). |
| `sequence_number` | `integer` | Strictly monotonic, 1-indexed integer per execution. Used for deduplication and ordered reconstruction. |
| `event_type` | `string` | Category identifier from the documented taxonomy below. |
| `timestamp` | `string` (ISO-8601 UTC) | Exact UTC timestamp of event generation. |
| `status` | `string` | Authoritative execution state: `queued`, `running`, `completed`, `failed`, or `cancelled`. |
| `agent_id` | `string \| null` | Originating agent identifier when applicable (e.g., `agent_researcher`). Null for system-level stages. |
| `stage` | `string` | Pipeline stage: `synthesis`, `graph_compilation`, `agent_execution`, `evaluation`, `reflection`, `evolution_decision`. |
| `message` | `string` | Concise, human-readable description for UI display. |
| `data` | `object` | Structured, sanitized payload with event-specific parameters. All credentials and private keys are redacted. |
| `error` | `string \| null` | Sanitized error message if an operation or execution failed. |

---

## 3. Event Taxonomy & Emission Points

| Event Type | Stage | Trigger Point | Payload (`data`) Fields |
| :--- | :--- | :--- | :--- |
| `execution.queued` | `synthesis` | Execution run request accepted and assigned an `execution_id`. | `run_number`, `architecture_id`, `topology` |
| `execution.started` | `synthesis` | Execution worker initialized, task context prepared. | `run_number`, `agent_count`, `constraints` |
| `execution.stage_started` | Any | A major pipeline stage begins (e.g., `graph_compilation`). | `stage_name`, `target_component` |
| `execution.stage_completed` | Any | A major pipeline stage completes successfully. | `stage_name`, `duration_seconds` |
| `agent.started` | `agent_execution` | LangGraph node function executes for an agent. | `role`, `objective`, `assigned_tools` |
| `agent.action` | `agent_execution` | Agent prepares action or generates intermediate response. | `action_type`, `preview` |
| `tool.started` | `agent_execution` | Agent invokes an assigned tool (e.g., Python sandbox, search). | `tool`, `input_preview` |
| `tool.completed` | `agent_execution` | Tool returns a successful execution result. | `tool`, `duration_seconds`, `output_preview` |
| `tool.failed` | `agent_execution` | Tool raises an exception, timeout, or security violation. | `tool`, `error`, `duration_seconds` |
| `agent.completed` | `agent_execution` | Agent completes execution and outputs state delta. | `status`, `duration_seconds`, `tool_call_count`, `output_preview` |
| `evaluation.started` | `evaluation` | Evaluator begins scoring task success and quality metrics. | `evaluation_id`, `rubric_dimensions` |
| `evaluation.completed` | `evaluation` | Evaluator finalizes score and verification compliance. | `evaluation_id`, `composite_score`, `metrics` |
| `evolution.proposed` | `reflection` | Failure diagnosis identifies weaknesses and drafts mutation. | `reflection_id`, `vulnerabilities_count`, `recommendations` |
| `evolution.validated` | `evolution_decision` | Centralized `ArchitectureValidator` checks hard constraints. | `is_valid`, `violations`, `max_agents_budget` |
| `evolution.accepted` | `evolution_decision` | `EvolutionDecisionPolicy` accepts mutated architecture candidate. | `decision_id`, `reason_code`, `score_delta` |
| `evolution.rejected` | `evolution_decision` | `EvolutionDecisionPolicy` rejects mutated architecture candidate. | `decision_id`, `reason_code`, `score_delta` |
| `execution.warning` | Any | Non-fatal anomaly observed (e.g., retry count incremented). | `warning_code`, `details` |
| `execution.failed` | Any | Fatal exception or graph invocation failure terminates execution. | `error`, `step_index` |
| `execution.cancelled` | Any | User or system cancelled in-flight execution. | `cancellation_reason` |
| `execution.completed` | Any | Terminal execution step reached; all outputs aggregated. | `total_steps`, `duration_seconds`, `agent_count`, `tool_call_count` |

---

## 4. Server-Sent Events (SSE) Wire Format

When subscribing via `GET /execution/{execution_id}/events`, each event is streamed as:

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no

id: 1
event: execution.started
data: {"event_id":"evt_1","execution_id":"exec_1","sequence_number":1,"event_type":"execution.started",...}

id: 2
event: agent.started
data: {"event_id":"evt_2","execution_id":"exec_1","sequence_number":2,"event_type":"agent.started",...}

: keepalive

id: 3
event: execution.completed
data: {"event_id":"evt_3","execution_id":"exec_1","sequence_number":3,"event_type":"execution.completed",...}
```

### Keepalives
The server emits an SSE comment (`: keepalive\n\n`) every 15 seconds during idle periods to prevent intermediate proxies from closing the connection.

### Reconnection and Resume
Clients that disconnect can reconnect with:
1. `GET /execution/{execution_id}/events?after_seq=2`
2. Or the HTTP header `Last-Event-ID: 2`

The server replays only events with `sequence_number > 2`.

---

## 5. Security and Sanitization
All event payloads pass through `sanitize_payload()` before serialization:
- Keys matching `api_key`, `secret`, `token`, `password`, `environ`, `gemini_key` are replaced with `[REDACTED_SECRET]`.
- String outputs exceeding 10,000 characters are safely truncated.
- Stack traces are sanitized to prevent leaking file system layouts or internal credentials.
