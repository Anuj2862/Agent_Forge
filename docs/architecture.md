# Agent Forge — Subsystem Architecture & Flow

This document details the subsystem design, module interactions, frontend-backend communications, and self-evolution loop of **Agent Forge**.

---

## 1. High-Level Architecture Flow

```
Natural Language User Task
            │
            ▼
┌───────────────────────┐
│    Meta Controller    │ ──► Analyzes prompt, decomposes subtasks & extracts required capabilities
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Architecture Generator│ ──► Synthesizes dynamic topology & assigns tools
│    & Tool Planner     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Dynamic Agent Factory │ ──► Instantiates executable runtime Agent Objects from JSON config
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   Execution Engine    │ ──► Runs Pipeline / Parallel multi-agent graph via LangGraph
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│       Evaluator       │ ──► Computes Task Success, Output Quality & Resource Metrics
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   Reflection Engine   │ ──► Identifies structural vulnerabilities (e.g. missing verifier)
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Evolution Memory Store│ ──► Persists experience pairs for future architecture synthesis optimization
└───────────┬───────────┘
            │ (Reflective Experience)
            └─────────────────────────► [Feedback Loop to Meta Controller]
```

---

## 2. System Architecture & Tier Breakdown

```
                    AGENT FORGE ARCHITECTURE
                               │
               ┌───────────────┴───────────────┐
               │                               │
               ▼                               ▼
       NEXT.JS FRONTEND                 FASTAPI BACKEND
       React + TypeScript              Python 3.11+
       Tailwind CSS + shadcn/ui        LangGraph Orchestration
       React Flow (Graph Viz)          Google Gemini API
                                       PostgreSQL & Redis
               │                               │
               └────── REST API / WebSockets ──┘
```

### Frontend Tier (Next.js + React Flow)
- **Role**: Dynamic visualization, interactive user task submission, agent graph inspection, real-time execution monitoring, and evolution comparison.
- **Key Modules**:
  - `components/architecture/`: Interactive React Flow graph visualizing dynamically synthesized agent topologies.
  - `components/execution/`: Real-time agent status indicators and step-by-step logs.
  - `components/evaluation/`: Metric charts comparing Run 1 vs. Run 2 architectures.

### Backend Tier (FastAPI + LangGraph)
- **Role**: Task analysis, architecture synthesis, dynamic agent instantiation, graph execution, quantitative evaluation, reflection, and memory persistence.
- **Key Modules**:
  - `app/controller/`: Meta Controller & Architecture Generator (Member 1).
  - `app/agents/`, `app/tools/`, `app/execution/`: Agent Factory, Tool Planner, and LangGraph Engine (Member 2).
  - `app/evaluation/`, `app/reflection/`: Metric scoring & Reflection Engine (Member 3).
  - `app/memory/`, `app/api/`: Evolution Memory & REST API Endpoints (Member 4).
