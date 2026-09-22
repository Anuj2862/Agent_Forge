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
- **Role**: Dynamic visualization, interactive task submission, agent graph inspection, real-time execution monitoring, evaluation scorecards, reflection transformation, and evolutionary comparison.
- **Design Philosophy**: AI laboratory + intelligent systems + engineering platform (minimalist, information-rich, desktop-optimized).
- **Core Screen Breakdown**:
  1. `/` (New Task / Forge): Prompt input, domain examples, animated synthesis feedback stages.
  2. `/architecture` (Architecture Hero): Interactive React Flow canvas, custom `AgentNode` states (`WAITING`, `ACTIVE`, `COMPLETED`, `FAILED`), click-to-inspect `AgentInspector` side panel, and metadata cards.
  3. `/execution` (Live Execution): Step-by-step agent progress, tool invocation status, and technical event stream.
  4. `/evaluation` (Evaluation): Multi-metric scorecard (Quality, Success, Accuracy, Completeness, Efficiency), execution statistics, and "Why this score?" qualitative reasoning.
  5. `/reflection` (Reflection Hero): Structural weakness diagnosis, root causes, and explicit modification cards with interactive `[Apply Recommendation]` transition.
  6. `/evolution` (Evolution): Multi-generation lineage timeline and side-by-side architecture & metric comparative diff.
  7. `/history` (History): Persistent task run logs with `[Forge Similar Task]` experience re-use.
- **Key Modules**:
  - `components/architecture/`: Interactive React Flow graph visualizing dynamically synthesized agent topologies.
  - `components/execution/`: Real-time agent status indicators and step-by-step logs.
  - `components/evaluation/`: Metric scorecards and qualitative reasoning cards.
  - `components/reflection/`: Weakness cards and architectural evolution transition triggers.
  - `components/evolution/`: Side-by-side graph diffing and historical run timelines.
  - `lib/api.ts`, `lib/types.ts`: Strongly typed API client and contract interfaces matching backend schemas.

### Backend Tier (FastAPI + LangGraph)
- **Role**: Task analysis, architecture synthesis, dynamic agent instantiation, graph execution, quantitative evaluation, reflection, and memory persistence.
- **Key Modules**:
  - `app/controller/`: Meta Controller, Complexity Analyzer, Task Decomposer, & Architecture Generator (Member 1).
  - `app/agents/`, `app/tools/`, `app/execution/`: Dynamic Agent Factory, Tool Planner, Tool Registry, and LangGraph Engine (Member 2).
  - `app/evaluation/`, `app/reflection/`: Multi-metric scoring, Failure Analyzer, Reflection Engine, & Architecture Modifier (Member 3).
  - `app/memory/`, `app/api/`: Evolution Memory Store, FastAPI REST API Endpoints, and Next.js Frontend Integration (Member 4).

---

## 3. Paradigm Comparison

| Architecture Model | Workflow | UI Behavior |
| :--- | :--- | :--- |
| **Traditional Chatbot** | Prompt ➔ Single LLM ➔ Answer | Monolithic text message stream |
| **Static Multi-Agent** | Prompt ➔ Hardcoded Fixed Graph ➔ Output | Static predefined pipeline diagram |
| **Agent Forge** | **Prompt ➔ Dynamic Synthesis ➔ Execution ➔ Evaluation ➔ Reflection ➔ Evolution ➔ Memory** | **Dynamic React Flow topology, live node inspection, qualitative reflection cards, and multi-run architecture comparison** |

