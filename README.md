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

Agent Forge is designed with a modern, production-oriented web dashboard architecture using **Next.js, React, TypeScript, Tailwind CSS, shadcn/ui, and React Flow**.

### Rationale for Next.js + React Flow over Legacy Prototypes
- **Interactive Node-Edge Graph Visualization**: Uses **React Flow** to dynamically render synthesized agent network topologies as interactive, inspectable visual node graphs rather than static diagrams.
- **Component-Driven Monitoring**: The frontend architecture is designed to support real-time execution tracking, step-by-step agent monitoring, evaluation metric breakdowns, and side-by-side architecture comparison (Run 1 vs Run 2). *(WebSocket-based real-time streaming is PLANNED.)*
- **Clean Separation of Concerns**: Structured separation between client-side rendering (CSR), server-side rendering (SSR), and REST/WebSocket API endpoints.

```
frontend/
├── app/                  # Next.js App Router (pages & layout containers)
│   ├── layout.tsx        # Root layout & design system providers
│   ├── page.tsx          # Main dashboard & prompt submission portal
│   └── history/          # Evolution memory & architectural run history
├── components/           # UI Component System
│   ├── architecture/     # React Flow graph visualization & node customizers
│   ├── execution/        # Live agent execution status & message stream monitors
│   ├── evaluation/       # Evaluation metrics & quality comparison charts
│   └── ui/               # shadcn/ui design primitives
├── lib/                  # API client, WebSocket hooks, and state utilities
├── public/               # Static assets
├── package.json          # Node.js dependencies & scripts
└── tsconfig.json         # TypeScript configuration
```

---

## 4. Frontend ↔ Backend System Architecture

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
                                                PostgreSQL
                                                Redis
                                                pgvector (PLANNED)
                       │                               │
                       └────── REST API / WebSockets ──┘
```

- **REST API**: Handles task submission, architecture retrieval, evaluation metric querying, and evolution memory search.
- **WebSockets *(PLANNED)***: Enables event streaming of active agent node states and tool execution logs to the React Flow visualizer.

---

## 5. Technology Stack Matrix

| Layer | Technology | Status |
| :--- | :--- | :--- |
| **Frontend Framework** | Next.js (App Router), React, TypeScript | *IN DEVELOPMENT* |
| **Frontend UI & Styling** | Tailwind CSS, shadcn/ui | *IN DEVELOPMENT* |
| **Graph Visualization** | React Flow | *IN DEVELOPMENT* |
| **Backend Framework** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2 | **IMPLEMENTED (SCAFFOLDING)** |
| **LLM Provider** | Google Gemini API (`google-genai`) | **CONFIGURED** |
| **Agent Orchestration** | LangGraph | **CONFIGURED** |
| **Database** | PostgreSQL | *CONFIGURED / PLANNED* |
| **Cache / State** | Redis | *CONFIGURED / PLANNED* |
| **Vector Memory** | `pgvector` | *PLANNED (Future Enhancement)* |
| **Testing** | `pytest`, `pytest-asyncio` | **IMPLEMENTED (SCAFFOLDING)** |
| **Containerization** | Docker | *PLANNED* |

---

## 6. Team Ownership & Git Branch Strategy

Development is distributed across four member modules adhering to a structured multi-branch workflow:

```
main (Stable Release)
  │
  └── common (Shared Integration Branch)
       │
       ├── member-1 (Meta Controller + Architecture Generator)
       ├── member-2 (Agent Runtime + Execution Engine)
       ├── member-3 (Evaluation + Reflection Engine)
       └── member-4 (Memory + FastAPI + Next.js Frontend + Integration)
```

| Member | Branch | Domain & Subsystem Responsibilities |
| :--- | :--- | :--- |
| **Member 1** | `member-1` | Meta Controller, Task Analyzer, Task Decomposer, Complexity Analyzer, Capability Extractor, Architecture Generator |
| **Member 2** | `member-2` | Agent Factory, Base Agent, Agent Runtime, Tool Planner, Tool Registry, Communication Graph, LangGraph Execution Engine |
| **Member 3** | `member-3` | Evaluator, Metrics Engine, Quality Scorer, Failure Analyzer, Reflection Engine, Architecture Modifier |
| **Member 4** | `member-4` | Evolution Memory, Memory Retriever, FastAPI Backend, Next.js Frontend, React Flow Visualization, Integration |

---

## 7. 15-Day Mid-Sem Development Roadmap

- [x] **Days 1–3**: Repository initialization, shared Pydantic schemas, baseline FastAPI health endpoint, git branch architecture (`main`, `common`, `member-1`..`member-4`).
- [ ] **Days 4–6**: Meta Controller, Task Decomposition, Architecture Generator, and Agent Factory core implementation.
- [ ] **Days 7–9**: Dynamic LangGraph execution engine (Pipeline & Parallel topologies) and Tool Planner integration.
- [ ] **Days 10–11**: Evaluator, Failure Analyzer, and Reflection Engine integration.
- [ ] **Days 12–13**: Evolution Memory Store persistence & feedback loop integration.
- [ ] **Day 14**: Next.js dashboard foundation + React Flow architecture visualization integration + End-to-End flow verification.
- [ ] **Day 15**: Feature freeze, integration testing, documentation, and Mid-Sem review demonstration.

---

## 8. Intended Mid-Sem Demonstration Flow

### Target Demonstration Scenario
Input Task: *"Research the impact of Generative AI on cybersecurity and produce a verified report."*

#### RUN 1 (Initial Architecture Synthesis)
- **Synthesized Architecture**: `Research Agent ➔ Analysis Agent ➔ Writer Agent`
- **Evaluation Score**: `Quality = 68%`
- **Reflection Engine Output**: `"Deficiency detected: Report lacks factual cross-reference verification step."`
- **Recommendation**: `"Action: ADD_AGENT | Role: Verification Agent | Position: between Analysis and Writer"`

#### RUN 2 (Reflected / Evolved Architecture)
- **Evolved Architecture**: `Research Agent ➔ Analysis Agent ➔ Verification Agent ➔ Writer Agent`
- **Evaluation Score**: `Quality = 86%`
- **Demonstrated Concept**: Proof of architecture-level self-adaptation and continuous evolution.

---

## 9. Current Project Status

> **Current Phase**: `INITIAL SCAFFOLDING & CORE DEVELOPMENT` (Mid-Sem Review Preparation)

| Subsystem / Feature | Status | Implementation Details |
| :--- | :--- | :--- |
| **Repository Scaffolding** | **IMPLEMENTED** | Folder structure, `.gitignore`, `.env.example`, `requirements.txt`, docs |
| **Shared Pydantic Schemas** | **IMPLEMENTED** | `TaskSpec`, `ArchitectureSpec`, `EvaluationResult`, `ReflectionResult` |
| **FastAPI Backend Core** | **IMPLEMENTED** | Scaffolding API server with `/health` route & router modules |
| **Meta Controller & Generator** | **IMPLEMENTED** | `TaskAnalyzer`, `TaskDecomposer`, `CapabilityExtractor`, `ComplexityAnalyzer`, `ArchitectureGenerator`, `MetaController` — all implemented & tested on `member-1` |
| **Agent Factory & LangGraph Engine**| *IN DEVELOPMENT* | Subsystem structure initialized; logic assigned to `member-2` |
| **Evaluator & Reflection Engine** | *IN DEVELOPMENT* | Subsystem structure initialized; logic assigned to `member-3` |
| **Evolution Memory Store** | *IN DEVELOPMENT* | Subsystem structure initialized; logic assigned to `member-4` |
| **Next.js Frontend & React Flow** | *IN DEVELOPMENT* | Architecture defined; dashboard assigned to `member-4` |
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
