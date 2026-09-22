# Agent Forge — Next.js Frontend Dashboard (Owned by Member 4)

[![Framework](https://img.shields.io/badge/Framework-Next.js_14_App_Router-black.svg)](https://nextjs.org)
[![Visualization](https://img.shields.io/badge/Visualization-React_Flow-red.svg)](https://reactflow.dev/)
[![Styling](https://img.shields.io/badge/Styling-Tailwind_CSS_+_shadcn/ui-blue.svg)](https://tailwindcss.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-Strict_Mode-brightgreen.svg)](https://www.typescriptlang.org)

This directory contains the production web dashboard for **Agent Forge**, an autonomous multi-agent architecture synthesis and evolution framework.

The frontend is specifically designed to visually communicate the core Agent Forge paradigm:
> **Natural-Language Task ➔ Dynamic Architecture Synthesis ➔ Runtime Agent Execution ➔ Multi-Metric Evaluation ➔ Weakness Reflection ➔ Architectural Evolution ➔ Experience Memory Persistence.**

The complete design contract and screen specifications are documented in [`docs/frontend_spec.md`](../docs/frontend_spec.md).

---

## 1. Technical Stack & Key Libraries

- **Framework**: Next.js (App Router, Server & Client Components)
- **UI & Components**: React 18+, TypeScript (Strict), Tailwind CSS, shadcn/ui
- **Graph & Topology Visualization**: React Flow (`@xyflow/react`)
- **Icons**: Lucide React (`lucide-react`)
- **Data Fetching & State**: Typed API client (`lib/api.ts`), React Hooks, SWR / React Query
- **Backend API Contract**: FastAPI REST API (`http://localhost:8000`), shared Pydantic data schemas

*Note: Streamlit is strictly prohibited. The interface is engineered as an AI laboratory & engineering platform.*

---

## 2. The 7 Primary Application Screens

The dashboard provides a persistent shell with a sidebar navigating across 7 dedicated functional views:

| Screen | Route | Core Role & Visual Elements |
| :--- | :--- | :--- |
| **1. New Task / Forge** | `/` | Natural-language prompt submission, domain quick-examples, multi-stage synthesis progress animation (`Understanding Task` ➔ `Synthesizing Architecture`). |
| **2. Architecture** *(Hero)* | `/architecture` | Dynamic **React Flow** interactive canvas displaying synthesized agent network topology, custom `AgentNode` status chips, click-to-open `AgentInspector` side panel, and architecture metadata. |
| **3. Live Execution** | `/execution` | Real-time agent progress pipeline, active agent state indicators (`WAITING`, `RUNNING`, `COMPLETED`, `FAILED`), and technical timestamped runtime event log. |
| **4. Evaluation** | `/evaluation` | Multi-metric scorecard (Overall %, Task Success, Accuracy, Completeness, Quality, Efficiency), execution statistics, and qualitative "Why this score?" rationale cards. |
| **5. Reflection** *(Hero)* | `/reflection` | Structural vulnerability diagnostics, root-cause analysis, and actionable modification recommendations with an interactive **[Apply Recommendation]** transformation trigger. |
| **6. Evolution** | `/evolution` | Multi-generation evolutionary timeline (Run 1 ➔ Run 2 ➔ Run 3) and side-by-side architecture & metric comparative diffing. |
| **7. History** | `/history` | Persistent log of historical task runs with topology tags, quality scores, and a one-click **[Forge Similar Task]** re-use flow. |

---

## 3. Directory Structure

```text
frontend/
├── app/
│   ├── layout.tsx                     # Persistent App Shell, Sidebar, System Status Header
│   ├── page.tsx                       # Screen 1: New Task / Forge Entrypoint
│   ├── history/
│   │   └── page.tsx                   # Historical Task Logs & Experience Re-use
│   └── run/[task_id]/
│       └── page.tsx                   # Live Run, Execution Timeline, Metrics, & Reflection
├── components/
│   ├── NavBar.tsx                     # Top navigation & system status
│   ├── TaskSubmitForm.tsx             # Task prompt submission with domain chips
│   ├── architecture/
│   │   └── ArchitectureGraph.tsx      # Interactive agent network graph visualization
│   ├── execution/
│   │   └── ExecutionTimeline.tsx      # Step-by-step agent execution timeline
│   └── evaluation/
│       ├── MetricsPanel.tsx           # Multi-metric score breakdown
│       ├── ReflectionPanel.tsx        # Deficiencies, root causes, & recommendations
│       └── EvolutionHistoryTable.tsx  # Multi-run architecture comparison table
├── lib/                               # API utilities and helpers
├── public/                            # Static assets and icons
├── package.json                       # Dependencies & scripts
└── tsconfig.json                      # Strict TypeScript configuration
```

---

## 4. Core Engineering Rules for the Frontend

1. **Backend is the Source of Truth**:
   - The frontend never fabricates or hardcodes agent topologies (`Research ➔ Analysis ➔ Writer`).
   - All graphs, agent roles, tool bindings, execution traces, metric scores, and reflection diagnoses originate from backend API responses (`ArchitectureSpec`, `ExecutionResult`, `EvaluationResult`, `ReflectionResult`).
2. **Design Language**:
   - Technical, minimal, information-rich AI laboratory aesthetic.
   - Clean borders, restrained dark-mode elevation, clear typography, monospace tags for technical identifiers.
   - Avoid distracting animations, heavy glowing effects, or excessive decorative gradients.
3. **Desktop-First Optimization**:
   - Primary target: High-density laptop and desktop displays (1280px+).
4. **Deterministic Demo Mode**:
   - Includes a Mid-Sem review Demo Mode toggle that walks through the full end-to-end journey reliably without reliance on third-party live network availability.

---

## 5. Implementation Priority Phases

```text
Phase 1: Foundation
└── Next.js setup, AppShell, Sidebar, Header, Routing, Tailwind CSS & shadcn/ui

Phase 2: Core Visual
└── TaskInput + SynthesisProgress + React Flow Canvas + AgentNode + AgentInspector

Phase 3: Execution
└── ExecutionTimeline + ExecutionLog + Live dynamic node status indicators

Phase 4: Intelligence
└── Evaluation scorecard + Metric breakdown + ReflectionPanel + [Apply Recommendation]

Phase 5: Evolution
└── Evolution timeline + ArchitectureComparison side-by-side diff + History table

Phase 6: Polish & Demo
└── Micro-transitions, error/empty states, Mid-Sem review Demo Mode
```

---

## 6. Local Setup & Running

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

The application will be accessible at: `http://localhost:3000`  
Ensure the FastAPI backend is running simultaneously at `http://localhost:8000`.
