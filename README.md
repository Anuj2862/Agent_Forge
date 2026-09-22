# Agent Forge: Autonomous Multi-Agent Architecture Synthesis and Evolution Framework

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js_|_React_|_TypeScript_|_React_Flow-black.svg)](https://nextjs.org)
[![Orchestration](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![LLM](https://img.shields.io/badge/LLM-Gemini_API-brightgreen.svg)](https://ai.google.dev/)
[![Status](https://img.shields.io/badge/Status-Mid--Sem_Development_Phase-yellow.svg)](#current-project-status)

---

## 1. Project Overview & Core Concept

**Agent Forge** is an **autonomous multi-agent architecture synthesis and evolution framework** designed as a software-based AI and Deep-Tech Engineering Design and Innovation (EDI) system with future patent potential.

### The Central Paradigm Shift
Traditional multi-agent frameworks (e.g., rigid DAG chains) force developers to pre-define static agent team topologies (e.g., `User Task ➔ Research Agent ➔ Analysis Agent ➔ Writer Agent`). Regardless of task complexity, domain variations, or past failure patterns, the agent composition and communication topology remain unchanged.

**Agent Forge fundamentally shifts this paradigm:**
> Given an unstructured natural-language task, Agent Forge dynamically determines what AI agent architecture should be synthesized, generates the requisite agents and tool bindings, executes the multi-agent graph, quantitatively evaluates execution quality, reflects on structural weaknesses, and records architectural experience in an **Evolution Memory** so that future architecture synthesis is autonomously improved.

```
                    ┌──────────────────────────────────────────┐
                    │               User Task                  │
                    └───────────────────┬──────────────────────┘
                                        │
                                        ▼
                    ┌──────────────────────────────────────────┐
                    │             Meta Controller              │
                    └───────────────────┬──────────────────────┘
                                        │
                                        ▼
                    ┌──────────────────────────────────────────┐
                    │          Task Analysis Engine            │
                    └───────────────────┬──────────────────────┘
                                        │
                                        ▼
                    ┌──────────────────────────────────────────┐
                    │ Architecture Generator & Tool Planner    │
                    └───────────────────┬──────────────────────┘
                                        │
                                        ▼
                    ┌──────────────────────────────────────────┐
                    │          Dynamic Agent Factory           │
                    └───────────────────┬──────────────────────┘
                                        │
                                        ▼
                    ┌──────────────────────────────────────────┐
                    │      Generated Agent Architecture        │
                    └───────────────────┬──────────────────────┘
                                        │
                                        ▼
                    ┌──────────────────────────────────────────┐
                    │   Execution Engine (LangGraph Runtime)   │
                    └───────────────────┬──────────────────────┘
                                        │
                                        ▼
                    ┌──────────────────────────────────────────┐
                    │         Evaluator & Reflection           │
                    └───────────────────┬──────────────────────┘
                                        │
                                        ▼
                    ┌──────────────────────────────────────────┐
                    │         Evolution Memory Store           │
                    └───────────────────┬──────────────────────┘
                                        │ (Reflective Experience)
                                        └────────► [Feedback Loop to Meta Controller]
```

---

## 2. System Architecture & Component Responsibilities

1. **Meta Controller**: Parses the user task prompt, categorizes task domain, decomposes subtasks, assesses complexity, and formulates high-level capability requirements.
2. **Architecture Generator**: Synthesizes task-specific agent topologies (Pipeline, Parallel) and agent role compositions dynamically.
3. **Tool Planner**: Evaluates agent capability requirements and dynamically binds appropriate tools (Web Search, Python Interpreter, Document Retriever).
4. **Dynamic Agent Factory**: Instantiates executable runtime agent objects from JSON architecture specifications without static `if/else` logic.
5. **Execution Engine (LangGraph)**: Schedules and executes the dynamic agent communication graph, managing state retention, retries, and message passing.
6. **Evaluator**: Computes objective execution metrics (Task Success, Output Quality, Completeness, Execution Time, Tool Usage).
7. **Reflection Engine**: Diagnoses structural root causes for lower scores (e.g., missing verification stage, inadequate research depth) and recommends explicit architectural modifications.
8. **Evolution Memory Store**: Persists architectural experience records `(Task Specification, Architecture, Evaluation, Reflection, Recommendation)` to guide future synthesis.

---

## 3. Modern Frontend Architecture (Next.js + React Flow)

Agent Forge features an enterprise-grade, laboratory-aesthetic web dashboard constructed with **Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, and React Flow**.

The frontend is specifically engineered to make **architecture synthesis, runtime observability, and structural evolution the primary visual elements**, completely moving away from traditional single-thread chatbots or static admin templates.

> Full visual design specifications, component hierarchies, and interface contracts are detailed in [`docs/frontend_spec.md`](docs/frontend_spec.md).

### The 7 Core Application Screens

The persistent application shell provides a navigation sidebar with 7 dedicated functional views:

```text
┌──────────────────────────────────────────────────────────────────┐
│ AGENT FORGE                                      ● SYSTEM READY  │
├──────────────┬───────────────────────────────────────────────────┤
│              │                                                   │
│  WORKSPACE   │                                                   │
│              │                                                   │
│  + New Task  │                  MAIN CONTENT                     │
│              │                                                   │
│  Architecture│                                                   │
│  Execution   │                                                   │
│  Evaluation  │                                                   │
│  Reflection  │                                                   │
│  Evolution   │                                                   │
│  History     │                                                   │
│              │                                                   │
│              │                                                   │
├──────────────┴───────────────────────────────────────────────────┤
│ Agent Forge • Architecture Intelligence                          │
└──────────────────────────────────────────────────────────────────┘
```

1. **Screen 1 — New Task / Forge (`/`)**: Natural-language task input, cross-domain example prompts, and an animated multi-stage synthesis feedback tracker (`Understanding Task` ➔ `Analyzing Complexity` ➔ `Synthesizing Architecture` ➔ `Creating Agents`).
2. **Screen 2 — Architecture [Hero Screen] (`/architecture`)**: Dynamic **React Flow** canvas rendering synthesized agent topologies directly from backend specifications. Features custom `AgentNode` widgets (with live status states `WAITING`, `ACTIVE`, `COMPLETED`, `FAILED`), an inspectable `AgentInspector` side panel, and architecture metadata cards.
3. **Screen 3 — Live Execution (`/execution`)**: Real-time agent progress pipeline, node status synchronization, tool invocation monitors, and a timestamped technical event stream log.
4. **Screen 4 — Evaluation (`/evaluation`)**: Comprehensive evaluation scorecard (Overall Quality %, Task Success, Accuracy, Completeness, Efficiency), runtime statistics (latency, tool calls, retries), and qualitative "Why this score?" explanations.
5. **Screen 5 — Reflection [Hero Screen] (`/reflection`)**: Diagnostic view highlighting architectural deficiencies, root causes, and explicit modifications, featuring an interactive **`[Apply Recommendation]`** button that triggers dynamic graph evolution.
6. **Screen 6 — Evolution (`/evolution`)**: Multi-generation lineage tracker (Run 1 ➔ Run 2 ➔ Run 3) with side-by-side architecture graph diffing and metric progression tables.
7. **Screen 7 — History (`/history`)**: Persistent record of historical tasks with one-click **`[Forge Similar Task]`** functionality to leverage Evolution Memory.

---

## 4. Frontend ↔ Backend System Architecture & Data Contracts

The frontend functions strictly as a visualizer of backend intelligence. **The frontend never becomes the source of truth or fabricates architectural data.**

```text
                             AGENT FORGE SYSTEM ARCHITECTURE
                                            │
                        ┌───────────────────┴───────────────────┐
                        │                                       │
                        ▼                                       ▼
                 NEXT.JS FRONTEND                        FASTAPI BACKEND
                 React 18+ & TypeScript                  Python 3.11+
                 Tailwind CSS & shadcn/ui                LangGraph Orchestration
                 React Flow (Topology Viz)               Google Gemini API
                                                         PostgreSQL & Redis
                        │                                       │
                        └──────── REST API / WebSockets ────────┘
```

### Backend Contract ➔ Frontend Component Mapping

| Backend Data Contract (`app/schemas/`) | Frontend Consumer Component | Visual Representation in UI |
| :--- | :--- | :--- |
| **`TaskSpec`** | `TaskInput.tsx`, `SynthesisProgress.tsx` | Decomposed subtasks, complexity badge, domain pills |
| **`ArchitectureSpec`** | `ArchitectureCanvas.tsx`, `AgentNode.tsx`, `AgentInspector.tsx` | Dynamic React Flow nodes, connection edges, agent inspector drawer |
| **`ExecutionResult`** | `ExecutionTimeline.tsx`, `ExecutionLog.tsx` | Live agent status indicators, tool call traces, execution log |
| **`EvaluationResult`** | `EvaluationSummary.tsx`, `MetricCard.tsx`, `EvaluationDetails.tsx` | Circular overall score, dimension progress bars, qualitative reasoning |
| **`ReflectionResult`** | `ReflectionPanel.tsx`, `FailureCard.tsx`, `RecommendationCard.tsx` | Weakness warnings, root-cause diagnosis, [Apply Recommendation] transition |
| **`EvolutionRecord`** | `EvolutionTimeline.tsx`, `ArchitectureComparison.tsx` | Run 1 vs Run 2 side-by-side canvas diff & metric comparison table |

---

## 5. Technology Stack Matrix

| Layer | Technology | Status |
| :--- | :--- | :--- |
| **Frontend Framework** | Next.js 14 (App Router), React, TypeScript (Strict) | *IN DEVELOPMENT* |
| **Frontend UI & Styling** | Tailwind CSS, shadcn/ui, Lucide React | *IN DEVELOPMENT* |
| **Graph Visualization** | React Flow (`@xyflow/react`) | *IN DEVELOPMENT* |
| **Backend Framework** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2 | **IMPLEMENTED (SCAFFOLDING)** |
| **LLM Provider** | Google Gemini API (`google-genai`) | **CONFIGURED** |
| **Agent Orchestration** | LangGraph | **CONFIGURED** |
| **Database** | PostgreSQL | *CONFIGURED / PLANNED* |
| **Cache / State** | Redis | *CONFIGURED / PLANNED* |
| **Vector Memory** | `pgvector` | *PLANNED (Future Enhancement)* |
| **Testing** | `pytest`, `pytest-asyncio` | **IMPLEMENTED (SCAFFOLDING)** |
| **Containerization** | Docker | *PLANNED* |

---

## 6. Team Ownership & Granular Task Distribution Matrix

Development is distributed across four core modules adhering to a structured multi-branch workflow (`main` ➔ `common` ➔ `member-1` .. `member-4`):

```text
main (Production Stable)
  │
  └── common (Shared Integration Branch)
       │
       ├── member-1 (Meta Controller + Architecture Generator)
       ├── member-2 (Dynamic Agent Factory + LangGraph Execution Engine)
       ├── member-3 (Evaluation + Reflection Engine + Modifier)
       └── member-4 (Evolution Memory + FastAPI + Next.js Frontend)
```

### Granular Member Responsibilities & Deliverables

| Member | Branch & Directory Ownership | Responsibilities & Deliverables |
| :--- | :--- | :--- |
| **Member 1** | `member-1`<br>`app/controller/` | **Meta Controller & Architecture Generator**<br>• Natural language task parsing and domain categorization.<br>• Task complexity assessment (`LOW`, `MEDIUM`, `HIGH`) and subtask decomposition.<br>• Dynamic architecture synthesis: Generates task-specific agent topologies (`PIPELINE`, `PARALLEL`, `HIERARCHICAL`).<br>• Capability extraction and agent team composition.<br>• **Deliverable**: Emits valid, schema-compliant `ArchitectureSpec` for consumption by Member 2 and Member 4. |
| **Member 2** | `member-2`<br>`app/agents/`<br>`app/tools/`<br>`app/execution/` | **Dynamic Agent Runtime & Execution Engine**<br>• Dynamic Agent Factory: Instantiates executable runtime agent instances directly from `AgentConfigSchema` without hardcoded if/else branching.<br>• Tool Planner & Tool Registry: Dynamic binding of Web Search, Document Retrieval, and Python Interpreter tools.<br>• LangGraph Execution Engine: Assembles dynamic StateGraphs according to `ArchitectureSpec` topology.<br>• Multi-agent state retention, retries, and message-passing orchestration.<br>• **Deliverable**: Emits live execution event traces, tool call logs, and complete `ExecutionResult`. |
| **Member 3** | `member-3`<br>`app/evaluation/`<br>`app/reflection/` | **Evaluation, Reflection & Evolution Engine**<br>• Evaluator & Quality Scorer: Computes objective metrics (Task Success %, Accuracy %, Completeness %, Quality %, Efficiency %).<br>• Failure Analyzer: Identifies structural bottlenecks, unverified assertions, and tool failure points.<br>• Reflection Engine: Diagnoses root causes and formulates concrete `ArchitecturalRecommendation` objects (e.g. `ADD_AGENT`, `REPLACE_AGENT`, `MODIFY_TOPOLOGY`).<br>• Architecture Modifier: Programmatically applies recommendations to synthesize evolved `ArchitectureSpec` (Run 2).<br>• **Deliverable**: Emits `EvaluationResult` (with qualitative rationale) and `ReflectionResult`. |
| **Member 4** | `member-4`<br>`app/memory/`<br>`app/api/`<br>`frontend/` | **Evolution Memory, FastAPI Backend & Next.js Frontend Visualizer**<br>• Evolution Memory Store: Persists architectural experience records `(Task, Architecture, Evaluation, Reflection, Recommendation)` for feedback into Meta Controller.<br>• FastAPI REST API routes matching shared data schemas (`/tasks`, `/architectures`, `/execution`, `/evaluation`, `/reflection`, `/memory`).<br>• Next.js App Router Shell, persistent sidebar, and all 7 core functional screens.<br>• Dynamic React Flow canvas engine (topology-to-graph node/edge converter).<br>• Custom `AgentNode`, inspectable `AgentInspector`, live execution event log, evaluation scorecard, reflection transformation CTA, and side-by-side architecture comparison.<br>• Mid-Sem Review Demo Mode for deterministic presentation.<br>• **Deliverable**: Fully functioning full-stack integrated application. |

---

## 7. 15-Day Mid-Sem Development Roadmap

- [x] **Days 1–3**: Repository initialization, shared Pydantic schemas, baseline FastAPI health endpoint, git branch architecture (`main`, `common`, `member-1`..`member-4`).
- [ ] **Days 4–6**: Meta Controller, Task Decomposition, Architecture Generator (`member-1`), and Dynamic Agent Factory (`member-2`).
- [ ] **Days 7–9**: Dynamic LangGraph execution engine (Pipeline & Parallel topologies), Tool Planner integration (`member-2`), and Evaluator scoring (`member-3`).
- [ ] **Days 10–11**: Failure Analyzer, Reflection Engine, Architecture Modifier (`member-3`), and Evolution Memory persistence (`member-4`).
- [ ] **Days 12–13**: FastAPI full REST endpoints, Next.js frontend scaffolding, AppShell, sidebar, and React Flow dynamic canvas (`member-4`).
- [ ] **Day 14**: Frontend integration of all 7 screens (Execution timeline, Evaluation scorecard, Reflection panel, Evolution comparison, Demo Mode) + End-to-End verification.
- [ ] **Day 15**: Feature freeze, comprehensive integration testing (`pytest`), documentation finalization, and Mid-Sem review demonstration.

---

## 8. Intended Mid-Sem Demonstration Flow (The Golden Journey)

The Mid-Sem review directly showcases the complete autonomous synthesis and self-evolution loop through the web dashboard:

```text
                    USER
                     │
                     ▼
              ENTERS TASK (Screen 1)
                     │
                     ▼
           TASK UNDERSTANDING & SYNTHESIS
           (Multi-stage visual thinking tracker)
                     │
                     ▼
          ┌───────────────────────────────────┐
          │ INITIAL SYNTHESIZED ARCHITECTURE  │
          │ (Screen 2: React Flow Canvas)     │
          │                                   │
          │ Research ➔ Analysis ➔ Writer      │
          └─────────────────┬─────────────────┘
                            │
                            ▼
                     LIVE EXECUTION (Screen 3)
                     (Live status pulses & event stream)
                            │
                            ▼
                       EVALUATION (Screen 4)
                       (Scorecard: Quality = 68%,
                        Deficiency: Lacks verification)
                            │
                            ▼
                       REFLECTION (Screen 5)
                       (Root Cause: Inadequate verification,
                        Recommendation: ADD Verifier Agent)
                            │
                            ▼
                   [ APPLY RECOMMENDATION ]
                            │
                            ▼
          ┌───────────────────────────────────┐
          │   EVOLVED ARCHITECTURE (RUN 2)    │
          │                                   │
          │ Research ➔ Analysis ➔             │
          │   VERIFIER ➔ Writer               │
          └─────────────────┬─────────────────┘
                            │
                            ▼
                   RUN 2 RE-EXECUTION
                            │
                            ▼
                  EVOLUTION & COMPARISON (Screen 6)
                  (Side-by-side graph diff:
                   Quality improves from 68% ➔ 88%)
```

---

## 9. Current Project Status

> **Current Phase**: `CORE DEVELOPMENT & INTEGRATION PREPARATION` (Mid-Sem Review Preparation)

| Subsystem / Feature | Status | Implementation Details |
| :--- | :--- | :--- |
| **Shared Pydantic Schemas** | **IMPLEMENTED** | `TaskSpec`, `ArchitectureSpec`, `EvaluationResult`, `ReflectionResult`, `ExecutionResult` |
| **FastAPI Backend Core** | **IMPLEMENTED** | API server with `/health`, `/simulate`, and domain router endpoints |
| **Meta Controller & Generator** | **IMPLEMENTED** | `TaskAnalyzer`, `TaskDecomposer`, `CapabilityExtractor`, `ComplexityAnalyzer`, `ArchitectureGenerator`, `MetaController` (Member 1) |
| **Agent Factory & LangGraph Engine**| **IMPLEMENTED** | Dynamic Agent Factory, `CommunicationGraph`, `ExecutionEngine`, `ToolPlanner`, `ToolRegistry` (Member 2) |
| **Evaluator & Reflection Engine** | **IMPLEMENTED** | `Evaluator`, `MetricsEngine`, `QualityScorer`, `FailureAnalyzer`, `ReflectionEngine`, `ArchitectureModifier` (Member 3) |
| **Evolution Memory Store** | **IMPLEMENTED** | SQLite/PostgreSQL `MemoryStore` & `MemoryRetriever` (Member 4) |
| **Next.js Frontend & React Flow** | **IMPLEMENTED** | Next.js App Router dashboard, interactive graph visualization, execution monitor (Member 4) |
| **WebSocket Streaming** | *PLANNED* | Real-time agent status streaming |
| **pgvector Memory Store** | *PLANNED (FUTURE)* | Semantic memory vector search enhancement |

---

## 10. Member 1 — Meta Controller Implementation

All Member 1 subsystems are implemented and tested on the `member-1` branch.

### Implemented Components

| Component | File | Description |
| :--- | :--- | :--- |
| `TaskAnalyzer` | `app/controller/task_analyzer.py` | Parses a natural-language prompt into a validated `TaskSpec` using Gemini |
| `TaskDecomposer` | `app/controller/task_decomposer.py` | Decomposes a task into a structured `List[Subtask]` using Gemini |
| `CapabilityExtractor` | `app/controller/capability_extractor.py` | Extracts required agent capabilities as a `List[str]` using Gemini |
| `ComplexityAnalyzer` | `app/controller/complexity_analyzer.py` | Estimates task complexity using transparent heuristics (no API call) |
| `ArchitectureGenerator` | `app/controller/architecture_generator.py` | Synthesizes a validated `ArchitectureSpec` from a `TaskSpec` |
| `MetaController` | `app/controller/meta_controller.py` | Orchestrates the full pipeline: prompt → `ArchitectureSpec` |

### Meta Controller Pipeline

```
Natural-Language Prompt
        │
        ▼
┌─────────────────────┐
│    TaskAnalyzer     │  ← Gemini: produces TaskSpec
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   TaskDecomposer    │  ← Gemini: produces List[Subtask]
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│CapabilityExtractor  │  ← Gemini: produces List[str]
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ ComplexityAnalyzer  │  ← Heuristic: produces ComplexityLevel
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ArchitectureGenerator│  ← Deterministic: produces ArchitectureSpec
└──────────┬──────────┘
           ▼
     ArchitectureSpec
```

### Supported Topologies

| Task Type | Topology | Connections |
| :--- | :--- | :--- |
| `data_analysis`, `research` | `parallel` | None (independent agents) |
| All other types | `pipeline` | Sequential edges |

### Running the Mid-Sem Demo

```bash
# Generate two contrasting architectures (parallel vs pipeline)
python generate_demo_architectures.py

# Run the full end-to-end pipeline manually
python test_meta_controller_manual.py

# Run all 19 automated tests
pytest -v
```

### Test Coverage

| Test File | Tests | What It Covers |
| :--- | :--- | :--- |
| `test_task_analyzer.py` | 1 | Pydantic-validated `TaskSpec` from mocked Gemini |
| `test_task_decomposer.py` | 1 | Valid `List[Subtask]` from mocked Gemini |
| `test_capability_extractor.py` | 1 | Unique capability list from mocked Gemini |
| `test_complexity_analyzer.py` | 4 | LOW / MEDIUM / HIGH classification + empty prompt error |
| `test_architecture_generator.py` | 5 | Parallel & pipeline topologies, agent preservation, error handling |
| `test_meta_controller.py` | 2 | Full orchestration order (mocked) + empty prompt rejection |

> See [`docs/member-1-architecture-examples.md`](docs/member-1-architecture-examples.md) for real generated `ArchitectureSpec` examples.

---

## 11. Quick Start & Local Development

### 1. Clone & Set Up Backend
```bash
git clone https://github.com/Anuj2862/Agent_Forge.git
cd Agent_Forge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Fill in GEMINI_API_KEY inside .env
```

### 3. Run FastAPI Backend
```bash
uvicorn app.main:app --reload --port 8000
```
Swagger API docs: `http://localhost:8000/docs` | Health check: `http://localhost:8000/health`

### 4. Run Next.js Frontend Dashboard *(In Development on `member-4`)*
```bash
cd frontend
npm install
npm run dev
```
Dashboard URL: `http://localhost:3000`

---

## 12. License & Academic Context
Developed for the Third-Year (TY) **Engineering Design & Innovation (EDI)** project. Designed with future patent potential in mind.
