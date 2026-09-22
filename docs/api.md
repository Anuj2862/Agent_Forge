# Agent Forge — REST API & Streaming Specifications

This document outlines the REST and WebSocket API contracts exposed by the FastAPI backend server for consumption by the Next.js frontend application, as defined in [`docs/frontend_spec.md`](frontend_spec.md).

---

## 1. System Health & Status

### GET `/health`
- **Status**: **IMPLEMENTED**
- **Description**: Returns backend service health, app version, and environment. Used by the frontend persistent status badge (`Header.tsx`).
- **Response**:
```json
{
  "status": "healthy",
  "app": "Agent Forge",
  "environment": "development",
  "phase": "Mid-Sem Scaffolding Setup"
}
```

---

## 2. API Endpoints & Contract Matrix

The frontend strictly visualizes data returned by the backend contracts.

### Tasks Domain (`/tasks`) — Screen 1: New Task / Forge

#### POST `/tasks/analyze`
- **Description**: Submits a natural-language prompt for Meta Controller analysis, domain classification, complexity evaluation, and subtask decomposition.
- **Request Body**:
```json
{
  "prompt": "Research the impact of AI on healthcare and create a verified comparative report."
}
```
- **Response (`TaskSpec`)**:
```json
{
  "task_id": "task_af_0241",
  "prompt": "Research the impact of AI on healthcare and create a verified comparative report.",
  "task_type": "research",
  "complexity": "high",
  "subtasks": [
    {
      "id": "subtask_1",
      "description": "Gather literature on healthcare AI models",
      "required_capabilities": ["web_search", "information_retrieval"]
    },
    {
      "id": "subtask_2",
      "description": "Analyze clinical validation metrics",
      "required_capabilities": ["data_analysis"]
    },
    {
      "id": "subtask_3",
      "description": "Synthesize comparative findings",
      "required_capabilities": ["technical_writing"]
    }
  ]
}
```

---

### Architecture Domain (`/architectures`) — Screen 2: Architecture Hero Canvas

#### POST `/architectures/generate`
- **Description**: Requests dynamic multi-agent architecture synthesis for a decomposed `TaskSpec`.
- **Request Body**: `TaskSpec`
- **Response (`ArchitectureSpec`)**:
```json
{
  "architecture_id": "arch_0241_v1",
  "task_id": "task_af_0241",
  "topology": "pipeline",
  "agents": [
    {
      "name": "Research Agent",
      "role": "Research Specialist",
      "objective": "Gather relevant clinical AI evidence",
      "capabilities": ["web_search", "document_retrieval"],
      "tools": ["web_search", "document_retriever"]
    },
    {
      "name": "Analysis Agent",
      "role": "Data Analyst",
      "objective": "Evaluate clinical outcomes and metrics",
      "capabilities": ["data_analysis"],
      "tools": ["python_interpreter"]
    },
    {
      "name": "Writer Agent",
      "role": "Technical Synthesizer",
      "objective": "Produce structured comparative report",
      "capabilities": ["technical_writing"],
      "tools": []
    }
  ],
  "connections": [
    {"source": "Research Agent", "target": "Analysis Agent", "data_type": "evidence_bundle"},
    {"source": "Analysis Agent", "target": "Writer Agent", "data_type": "analysis_summary"}
  ]
}
```

#### GET `/architectures/{architecture_id}`
- **Description**: Retrieves synthesized architecture specification for React Flow graph rendering and Agent Inspector hydration.
- **Response**: `ArchitectureSpec`

---

### Execution Domain (`/execution`) — Screen 3: Live Execution & Event Stream

#### POST `/execution/run`
- **Description**: Triggers LangGraph multi-agent runtime execution for a synthesized architecture.
- **Request Body**:
```json
{
  "task_id": "task_af_0241",
  "architecture_id": "arch_0241_v1"
}
```
- **Response (`ExecutionResult`)**:
```json
{
  "execution_id": "exec_8812",
  "task_id": "task_af_0241",
  "architecture_id": "arch_0241_v1",
  "status": "completed",
  "total_latency_seconds": 18.4,
  "traces": [
    {
      "agent_name": "Research Agent",
      "status": "completed",
      "latency_seconds": 4.8,
      "tool_calls": [
        {"tool_name": "web_search", "latency_seconds": 2.1, "success": true}
      ],
      "output_preview": "Found 14 relevant clinical trials..."
    },
    {
      "agent_name": "Analysis Agent",
      "status": "completed",
      "latency_seconds": 6.2,
      "tool_calls": [
        {"tool_name": "python_interpreter", "latency_seconds": 1.4, "success": true}
      ],
      "output_preview": "Correlation matrix generated..."
    },
    {
      "agent_name": "Writer Agent",
      "status": "completed",
      "latency_seconds": 7.4,
      "tool_calls": [],
      "output_preview": "Comparative Healthcare AI Report..."
    }
  ],
  "final_output": "Comprehensive final report..."
}
```

#### GET `/execution/{execution_id}`
- **Description**: Retrieves full execution trace and tool logs for an execution run.
- **Response**: `ExecutionResult`

#### WS `/execution/ws/{execution_id}` *(PLANNED)*
- **Description**: WebSocket stream emitting real-time agent status changes (`WAITING` ➔ `ACTIVE` ➔ `COMPLETED`) and tool execution logs to the React Flow visualizer.

---

### Evaluation Domain (`/evaluation`) — Screen 4: Evaluation Scorecard

#### POST `/evaluation/evaluate`
- **Description**: Evaluates execution quality across multiple dimensions.
- **Request Body**:
```json
{
  "execution_id": "exec_8812"
}
```
- **Response (`EvaluationResult`)**:
```json
{
  "evaluation_id": "eval_4401",
  "execution_id": "exec_8812",
  "metrics": {
    "task_success": 0.94,
    "accuracy": 0.87,
    "completeness": 0.82,
    "quality": 0.68,
    "efficiency": 0.76,
    "overall_score": 0.68
  },
  "score_explanations": [
    "Task requirements were completed.",
    "Major claims were independently cited.",
    "Research outputs lacked explicit fact-verification stage.",
    "Execution used one additional retry."
  ]
}
```

#### GET `/evaluation/{evaluation_id}`
- **Description**: Fetches stored evaluation metrics and qualitative explanations.
- **Response**: `EvaluationResult`

---

### Reflection Domain (`/reflection`) — Screen 5: Reflection & Evolution Trigger

#### POST `/reflection/reflect`
- **Description**: Diagnoses architectural root causes for performance deficiencies and produces actionable modification recommendations.
- **Request Body**:
```json
{
  "evaluation_id": "eval_4401"
}
```
- **Response (`ReflectionResult`)**:
```json
{
  "reflection_id": "refl_9912",
  "evaluation_id": "eval_4401",
  "issues": [
    {
      "category": "missing_capability",
      "severity": "high",
      "description": "Research outputs passed directly to Writer without independent verification.",
      "root_cause": "Architecture-level verification capability is insufficient."
    }
  ],
  "recommendations": [
    {
      "action": "add_agent",
      "target_agent": {
        "name": "Verification Agent",
        "role": "Fact Verification Specialist",
        "objective": "Cross-check empirical claims against medical literature",
        "capabilities": ["fact_checking", "evidence_validation"],
        "tools": ["web_search", "document_retriever"]
      },
      "insert_after": "Analysis Agent",
      "insert_before": "Writer Agent",
      "reason": "Improve reliability and factual cross-checking of research claims."
    }
  ]
}
```

#### POST `/reflection/apply`
- **Description**: Programmatically applies an architectural recommendation, compiling an evolved `ArchitectureSpec` (Run 2).
- **Request Body**:
```json
{
  "architecture_id": "arch_0241_v1",
  "recommendation_id": "refl_9912"
}
```
- **Response**: Evolved `ArchitectureSpec` (Run 2)

---

### Memory & Evolution Domain (`/memory`) — Screens 6 & 7: Evolution & History

#### GET `/memory`
- **Description**: Retrieves historical task records and evolutionary chains.
- **Query Params**: `limit=20&offset=0`
- **Response**:
```json
[
  {
    "task_id": "task_af_0241",
    "prompt": "Research the impact of AI on healthcare...",
    "runs": [
      {
        "run_index": 1,
        "architecture_id": "arch_0241_v1",
        "topology": "pipeline",
        "agent_count": 3,
        "quality_score": 0.68,
        "timestamp": "2026-09-16T19:21:04Z"
      },
      {
        "run_index": 2,
        "architecture_id": "arch_0241_v2",
        "topology": "pipeline",
        "agent_count": 4,
        "quality_score": 0.88,
        "timestamp": "2026-09-16T19:24:12Z"
      }
    ]
  }
]
```

#### GET `/memory/{task_id}`
- **Description**: Retrieves complete multi-run lineage for a task to populate the side-by-side comparative diff on `/evolution`.
