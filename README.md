# Agent Forge: Autonomous Multi-Agent Architecture Synthesis and Evolution Framework

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![LLM](https://img.shields.io/badge/LLM-Gemini_API-brightgreen.svg)](https://ai.google.dev/)
[![Status](https://img.shields.io/badge/Status-Mid--Sem_Development_Phase-yellow.svg)](#current-project-status)

---

## 1. Project Overview & Core Concept

**Agent Forge** is an **autonomous multi-agent architecture synthesis and evolution framework** designed for complex software-based AI and Deep-Tech EDI applications.

### The Central Paradigm Shift
Traditional multi-agent systems use developer-defined, hard-coded workflows (e.g., `User Task ➔ Research Agent ➔ Analysis Agent ➔ Writer Agent`). The topology, roles, and tool bindings remain static regardless of task domain or past execution failures.

**Agent Forge fundamentally changes this model:**
> Given a natural-language task, Agent Forge dynamically analyzes the requirements, synthesizes a custom multi-agent architecture (topology, agent roles, capabilities, and tool bindings), instantiates the agents dynamically, executes the graph, evaluates execution quality, reflects on structural weaknesses, and records architectural experience in an **Evolution Memory** to autonomously improve future team synthesis.

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
                    │ Generated Agent Team (Execution Engine)  │
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

## 2. System Architecture & Major Components

1. **Meta Controller**: Decomposes user tasks into subtasks, assesses complexity, extracts required capabilities, and formulates high-level task specifications.
2. **Architecture Generator**: Synthesizes custom agent topologies (Pipeline, Parallel) and agent role compositions dynamically.
3. **Tool Planner**: Evaluates agent needs and dynamically binds appropriate tools (Web Search, Python Exec, Document Retriever).
4. **Agent Factory**: Instantiates executable runtime agent objects from JSON architecture specifications without static `if/else` logic.
5. **Execution Engine (LangGraph)**: Schedules and executes the dynamic agent communication graph, managing state, retries, and message passing.
6. **Evaluator**: Computes objective execution metrics (Task Success, Quality, Completeness, Execution Time, Tool Efficiency).
7. **Reflection Engine**: Diagnoses architectural root causes for lower scores (e.g., missing verification stage, inadequate research depth) and recommends explicit structural modifications.
8. **Evolution Memory Store**: Persists architectural experience pairs `(Task Specification, Architecture, Evaluation, Reflection, Recommendation)` to optimize future synthesis.

---

## 3. Technology Stack

- **Core Programming**: Python 3.11+
- **LLM Engine**: Google Gemini API
- **Agent Orchestration**: LangGraph
- **Backend & Data Validation**: FastAPI, Uvicorn, Pydantic v2
- **Database & Memory**: PostgreSQL + `pgvector`, Redis
- **Frontend Dashboard**: Streamlit
- **Testing**: `pytest`, `pytest-asyncio`

---

## 4. Team Ownership & Responsibilities

Agent Forge is developed by a team of four, divided into modular subsystem domains:

| Member | Primary Modules & Responsibilities | Key Deliverables |
| :--- | :--- | :--- |
| **Member 1** | Meta Controller, Task Analyzer, Task Decomposer, Architecture Generator | Natural language task ➔ Task Specification ➔ Architecture JSON |
| **Member 2** | Base Agent, Agent Factory, Tool Planner, Tool Registry, Execution Engine | Architecture JSON ➔ Dynamic Agent Objects ➔ LangGraph Execution Result |
| **Member 3** | Evaluator, Metrics Engine, Quality Scorer, Failure Analyzer, Reflection Engine | Execution Result ➔ Evaluation ➔ Reflection ➔ Architectural Modification |
| **Member 4** | Evolution Memory, Memory Retriever, FastAPI Backend, Streamlit UI, Integration | Memory Persistence ➔ REST API ➔ Streamlit Dashboard ➔ E2E Integration |

---

## 5. Development Strategy & Roadmap

### Mid-Sem Implementation Target (15-Day Plan)
- [x] Day 1–3: Environment setup, repository initialization, shared Pydantic schemas, Gemini integration.
- [ ] Day 4–6: Meta Controller, Architecture Generator, and Agent Factory core implementation.
- [ ] Day 7–9: Dynamic LangGraph execution (Pipeline & Parallel) and Tool Assignment.
- [ ] Day 10–11: Evaluator, Failure Analyzer, and Reflection Engine integration.
- [ ] Day 12–13: Evolution Memory Store feedback loop integration.
- [ ] Day 14: Full FastAPI & Streamlit integration, demo flow verification (Run 1 vs. Run 2 architecture self-improvement).
- [ ] Day 15: Feature freeze, testing, documentation, and Mid-Sem review demonstration.

### Post-Mid-Sem Planned Features
- Complex topologies (Debate, Tree-of-Thought, Blackboard)
- Advanced evolutionary optimization algorithms for topology mutation
- Deep vector retrieval via `pgvector` & Knowledge Graphs
- Multi-LLM provider fallback & distributed execution

---

## 6. Repository Workflow & Branch Strategy

The team maintains **one common repository** adhering to strict feature-branch isolation:

- `main`: Protected, production-ready release branch.
- `develop`: Integration branch for active feature development.
- `feature/*`: Dedicated branches for member modules (`feature/meta-controller`, `feature/agent-runtime`, `feature/evaluation-reflection`, `feature/memory-platform`).

### Contribution Workflow
```
Feature Branch  ➔  Local Testing  ➔  Commit  ➔  Pull Request  ➔  develop  ➔  Integration Testing  ➔  main
```

---

## 7. Current Project Status

> **Current Phase**: `INITIAL SCAFFOLDING & CORE DEVELOPMENT` (Mid-Sem Review Preparation)

### Status Matrix

| Module / Component | Status | Details |
| :--- | :--- | :--- |
| **Repository Scaffolding** | **IMPLEMENTED** | Directory layout, `.gitignore`, `.env.example`, `requirements.txt`, setup docs |
| **Shared Data Schemas** | **IMPLEMENTED** | Pydantic contracts (`TaskSpec`, `ArchitectureSpec`, `EvaluationResult`, `ReflectionResult`) |
| **API Entry Point** | **IMPLEMENTED** | FastAPI skeleton with health check endpoints |
| **Meta Controller & Generator** | *PLANNED* | Module structure created; business logic under active development |
| **Agent Factory & Execution** | *PLANNED* | Module structure created; LangGraph execution under active development |
| **Evaluator & Reflection** | *PLANNED* | Module structure created; evaluation heuristics under active development |
| **Evolution Memory & UI** | *PLANNED* | Module structure created; Streamlit UI & memory persistence under development |

---

## 8. Quick Start

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/Anuj2862/Agent_Forge.git
cd Agent_Forge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and supply your GEMINI_API_KEY
```

### 3. Run FastAPI Backend
```bash
uvicorn app.main:app --reload --port 8000
```
Verify health: Navigate to `http://localhost:8000/health` or `http://localhost:8000/docs`.

### 4. Run Streamlit Dashboard
```bash
streamlit run frontend/streamlit_app.py
```

---

## 9. License & Academic Context
Developed for the Third-Year (TY) **Engineering Design & Innovation (EDI)** project. Designed with future patent potential in mind.
