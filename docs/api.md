# Agent Forge — REST API & Streaming Specifications

This document outlines the REST API routes exposed by the FastAPI backend server for consumption by the Next.js frontend application.

---

## 1. System Health Endpoint

### GET `/health`
- **Status**: **IMPLEMENTED**
- **Description**: Returns backend service health, app version, and environment.
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

## 2. Planned API Endpoint Overview

All endpoints listed below are planned for the Mid-Sem implementation milestone and will be consumed by the Next.js React Flow dashboard:

### Tasks Domain (`/tasks`)
- `POST /tasks/analyze`: Submits a raw prompt for Meta Controller analysis and subtask decomposition.

### Architecture Domain (`/architectures`)
- `POST /architectures/generate`: Requests dynamic architecture synthesis for a given task specification.
- `GET /architectures/{architecture_id}`: Retrieves synthesized architecture specification JSON (consumed by React Flow graph builder).

### Execution Domain (`/execution`)
- `POST /execution/run`: Triggers dynamic agent team execution via LangGraph.
- `GET /execution/status/{execution_id}`: Polls real-time execution status and agent message logs.
- `WS /execution/ws/{execution_id}`: *(PLANNED)* WebSocket endpoint for real-time live execution event streaming.

### Evaluation & Reflection Domain (`/evaluation`)
- `POST /evaluation/evaluate`: Triggers quantitative scoring on execution output.
- `POST /evaluation/reflect`: Triggers reflection analysis and architectural evolution recommendations.

### Memory Domain (`/memory`)
- `POST /memory/store`: Persists an execution experience record.
- `GET /memory/search`: Retrieves past architectural experiences similar to a target task prompt.
