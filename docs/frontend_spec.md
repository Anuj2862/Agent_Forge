# Agent Forge — Complete Frontend / UI-UX Specification

> **Design Contract & Specification Document**  
> **Target Framework:** Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, React Flow  
> **Source of Truth:** Backend API Contracts (`ArchitectureSpec`, `ExecutionResult`, `EvaluationResult`, `ReflectionResult`)

---

## 1. Frontend Objective

The frontend should not behave like a conventional chatbot or ordinary admin dashboard.

It must visually communicate the complete Agent Forge concept:

> **A natural-language task enters the system → Agent Forge understands it → dynamically synthesizes an agent architecture → creates and executes the agents → evaluates the result → reflects on weaknesses → evolves the architecture → stores the experience.**

The UI therefore needs to make the **architecture and its evolution the primary visual elements**.

---

## 2. Technology Stack

### Frontend
- **Framework**: Next.js (App Router)
- **UI & Components**: React, TypeScript, Tailwind CSS, shadcn/ui
- **Graph Visualization**: React Flow
- **Icons**: Lucide React

### Backend Integration
- **Framework**: FastAPI (Python 3.11+)
- **Protocols**: REST APIs, WebSockets *(planned/streaming)*
- **Data Schemas**: Pydantic v2 contracts (`app/schemas/`)

### AI / Backend Engine
- Python 3.11+
- Google Gemini API (`google-genai`)
- LangGraph
- PostgreSQL & Redis

*Note: The frontend must **not use Streamlit**.*

---

## 3. Overall Application Structure

The application features a persistent shell:

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

### Sidebar Navigation
The sidebar provides direct navigation to all 7 primary functional screens:
1. **New Task**: Interactive task prompt submission & synthesis trigger.
2. **Architecture**: Dynamic React Flow graph visualization of synthesized topology.
3. **Execution**: Step-by-step agent execution monitoring and technical event stream.
4. **Evaluation**: Multi-metric scorecard and qualitative rationale cards.
5. **Reflection**: Structural weakness analysis, root-cause diagnosis, and actionable recommendations.
6. **Evolution**: Run timeline and side-by-side architecture & metric comparisons.
7. **History**: Persistent log of past task runs with one-click re-forge capability.

At the top of the sidebar:
```text
AGENT
FORGE
```
accompanied by a subtle real-time system status indicator (`● SYSTEM READY`).

---

## 4. Design Language & Aesthetic Philosophy

The visual language communicates:
**AI laboratory + intelligent systems + engineering platform**

rather than:
- generic chatbot
- ordinary SaaS dashboard
- cybersecurity dashboard
- overly futuristic sci-fi interface

### Desired Characteristics
- **Clean**: Technical, minimal, distraction-free.
- **Interactive**: Direct node inspection, zoomable canvas, expandable details.
- **Information-rich**: Concrete technical metadata, tool parameters, trace timestamps.
- **Professional & Research-Oriented**: Suitable for deep-tech review and patent demonstration.

### UI Styling Rules
- Subtle borders (`border-slate-800`, `border-border/40`)
- Restrained dark-mode elevation and soft shadows
- Rounded cards (`rounded-lg` / `rounded-xl`)
- Clear typographic hierarchy (Inter / Outfit typography)
- Monospace badges for technical IDs, tokens, and durations (`font-mono`)
- Node status indicators (`○ WAITING`, `● ACTIVE`, `✓ COMPLETED`, `! FAILED`)
- **Avoid**: Excessive gradients, constant particle animations, distracting glowing effects, or animations that slow user interaction.

---

## 5. SCREEN 1 — NEW TASK / FORGE

The application's starting point and input portal:

```text
                 FORGE A NEW ARCHITECTURE

        Give Agent Forge a task to solve.

┌──────────────────────────────────────────────────────┐
│ Research the impact of AI on healthcare and create   │
│ a verified comparative report.                       │
│                                                      │
│                                                      │
└──────────────────────────────────────────────────────┘

              [ Forge Architecture ]
```

Below the input area, curated example prompts demonstrate cross-domain versatility:
- **Research & Analysis**: *"Research the impact of Generative AI on cybersecurity and produce a verified report."*
- **Code & Debugging**: *"Analyze an authentication service deadlock, isolate root causes, and generate a verified fix."*
- **Data Analysis**: *"Evaluate quarterly financial performance dataset and synthesize trend projections."*
- **Document Processing**: *"Extract compliance risk factors from legal contracts and cross-validate against regulations."*
- **Planning**: *"Formulate a disaster response logistical deployment plan with resource constraints."*

### Key Principle
The user **never directly selects agents**. The entire core concept is:
```text
USER ➔ TASK ➔ AGENT FORGE ➔ SYSTEM DECIDES ARCHITECTURE
```

---

## 6. Task Processing Animation

When the user clicks **Forge Architecture**, the UI provides visual feedback through dynamic synthesis stages rather than a static spinner:

```text
✓ Understanding Task
✓ Analyzing Complexity
✓ Decomposing Task
● Synthesizing Architecture
○ Selecting Tools
○ Creating Agents
○ Preparing Execution
```

The active stage updates dynamically, providing clear visual evidence of multi-stage architectural reasoning.

---

## 7. SCREEN 2 — ARCHITECTURE (Hero Screen)

The hero screen of Agent Forge, centered around an interactive **React Flow** canvas.

```text
                  GENERATED ARCHITECTURE

       ┌───────────────┐
       │   Research    │
       │     Agent     │
       │   ● COMPLETE  │
       └───────┬───────┘
               │
               ▼
       ┌───────────────┐
       │    Analyst    │
       │     Agent     │
       │   ● ACTIVE    │
       └───────┬───────┘
               │
        ┌──────┴──────┐
        ▼             ▼
 ┌────────────┐ ┌────────────┐
 │  Verifier  │ │   Critic   │
 └──────┬─────┘ └──────┬─────┘
        └──────┬───────┘
               ▼
       ┌───────────────┐
       │     Writer    │
       │      Agent    │
       └───────────────┘
```

### React Flow Dynamic Mapping
- The graph is **strictly generated from the backend `ArchitectureSpec`**.
- Agent nodes and connection edges are computed dynamically from `agents[]`, `connections[]`, and `topology` (e.g. `PIPELINE`, `PARALLEL`, `HIERARCHICAL`).
- Never hardcode static chains into the UI.

---

## 8. Custom Agent Nodes

Each synthesized agent renders using a dedicated custom React Flow node component:

```text
┌────────────────────────────┐
│ ● ACTIVE                   │
│                            │
│ 🔎 RESEARCH AGENT          │
│                            │
│ Research Specialist        │
│                            │
│ Tools   Web Search         │
│         Documents          │
│                            │
│ Goal                       │
│ Gather relevant evidence   │
└────────────────────────────┘
```

### Node State Variations
- `○ WAITING`: Muted border, idle state.
- `● ACTIVE`: Accent highlight, pulse indicator, live working state.
- `✓ COMPLETED`: Green confirmation badge, execution duration chip.
- `! FAILED`: Amber/Red error badge with retry counter.

---

## 9. Agent Inspector Side Panel

Clicking any agent node opens an inspectable side drawer:

```text
AGENT INSPECTOR

RESEARCH AGENT

Status
✓ Completed

Role
Research Specialist

Objective
Gather relevant evidence

Capabilities
• Research
• Verification

Tools
• Web Search
• Document Retrieval

Input
Task Specification

Output
Research Findings

Execution
4.82 seconds
```

Every generated agent is completely transparent, inspectable, and auditable.

---

## 10. Architecture Metadata Panel

Positioned adjacent to or above the canvas:

```text
ARCHITECTURE

Topology             PIPELINE
Agents               4
Connections          3
Tools                5
Generated            19:21:04
Architecture ID      AF-0241
Complexity           HIGH
Generation Strategy  Dynamic Synthesis
```

---

## 11. SCREEN 3 — LIVE EXECUTION

Visually monitors runtime execution progress in real time:

```text
LIVE EXECUTION

Task
Research AI impact on healthcare...

────────────────────────────────────────────

✓ Research Agent              4.8s
✓ Web Search                  2.1s
● Analysis Agent              RUNNING
○ Verification Agent          WAITING
○ Writer Agent                WAITING
```

Simultaneously, node statuses update on the React Flow canvas:
```text
Research ✓ ➔ Analysis ● ➔ Verifier ○ ➔ Writer ○
```

---

## 12. Execution Event Stream

A dedicated technical event stream panel logging granular runtime milestones:

```text
EXECUTION LOG

19:21:03  Task received
19:21:04  Architecture generated
19:21:05  Research Agent started
19:21:06  Web Search invoked
19:21:08  12 results collected
19:21:09  Research Agent completed
19:21:09  Analysis Agent started
```

---

## 13. SCREEN 4 — EVALUATION

Upon execution completion, objective evaluation results are presented:

```text
EXECUTION EVALUATION

                 84%
             OVERALL SCORE

┌──────────────────────────────────────────┐
│ Task Success                94%          │
│ Accuracy                    87%          │
│ Completeness                82%          │
│ Quality                     84%          │
│ Efficiency                  76%          │
└──────────────────────────────────────────┘
```

### Execution Statistics
```text
Agents Used          4
Execution Time       18.4 sec
Tool Calls           9
Retries              1
Failures             0
```

*All numbers must originate from backend `EvaluationResult`. The frontend never fabricates metrics.*

---

## 14. Evaluation Explanation ("Why This Score?")

Qualitative explanations contextualize the quantitative score:

```text
WHY THIS SCORE?

✓ Task requirements were completed.
✓ Major claims were independently verified.
⚠ Some supporting details lacked verification.
⚠ Execution used one additional retry.
```

---

## 15. SCREEN 5 — REFLECTION (Hero Feature)

Diagnoses architectural deficiencies and pinpoints root causes:

```text
REFLECTION

Architecture analysis detected a weakness.

┌──────────────────────────────────────────┐
│ ⚠ MISSING VERIFICATION STAGE             │
│                                          │
│ Research outputs were passed directly    │
│ to the Writer without independent        │
│ verification.                            │
└──────────────────────────────────────────┘

ROOT CAUSE
Architecture-level verification capability is insufficient.

RECOMMENDED CHANGE
+ ADD AGENT
Fact Verification Agent
Reason: Improve reliability of research claims.
```

---

## 16. Architectural Transformation Transition

The user triggers self-evolution with an explicit action:

```text
[ Apply Recommendation ]
```

When clicked, the interface triggers an animated transition:

```text
ARCHITECTURE UPDATED

BEFORE: Research ➔ Analysis ➔ Writer
AFTER:  Research ➔ Analysis ➔ Verification ➔ Writer
```

The React Flow canvas updates dynamically to render the transformed topology.

---

## 17. SCREEN 6 — EVOLUTION

Tracks the multi-generation evolutionary history of architectures for a task:

```text
ARCHITECTURE EVOLUTION

┌───────────────────────────────────────────┐
│ RUN 01                                    │
│ Research ➔ Writer                         │
│ Quality: 68%                              │
└─────────────────────┬─────────────────────┘
                      │ Reflection
                      ▼
┌───────────────────────────────────────────┐
│ RUN 02                                    │
│ Research ➔ Analysis ➔ Writer              │
│ Quality: 79%                              │
└─────────────────────┬─────────────────────┘
                      │ Reflection
                      ▼
┌───────────────────────────────────────────┐
│ RUN 03                                    │
│ Research ➔ Analysis ➔ Verification        │
│ ➔ Writer                                  │
│ Quality: 88%                              │
└───────────────────────────────────────────┘
```

---

## 18. Architecture Side-by-Side Comparison

Allows comparative inspection of different architectural runs:

```text
              ARCHITECTURE COMPARISON

        RUN 01                     RUN 02

   ┌───────────┐              ┌───────────┐
   │ Research  │              │ Research  │
   └─────┬─────┘              └─────┬─────┘
         ↓                          ↓
   ┌───────────┐              ┌───────────┐
   │  Writer   │              │ Analysis  │
   └───────────┘              └─────┬─────┘
                                     ↓
                               ┌───────────┐
                               │ Verifier  │
                               └─────┬─────┘
                                     ↓
                               ┌───────────┐
                               │  Writer   │
                               └───────────┘

METRIC              RUN 01       RUN 02
Task Success         72%          94%
Accuracy             65%          88%
Completeness         70%          85%
Quality              68%          88%
Execution Time       11.2s        18.4s
```

---

## 19. SCREEN 7 — HISTORY

Lists all historical task runs with status, topology badges, and timestamps:

```text
RECENT TASKS

┌────────────────────────────────────────────────────────┐
│ Research AI in healthcare              Completed       │
│ 4 Agents • Pipeline                    19:21           │
├────────────────────────────────────────────────────────┤
│ Debug authentication service           Completed       │
│ 3 Agents • Pipeline                    18:47           │
├────────────────────────────────────────────────────────┤
│ Analyze sales dataset                  Completed       │
│ 5 Agents • Parallel                    17:32           │
└────────────────────────────────────────────────────────┘
```

Clicking a task opens its stored architecture, execution traces, evaluation scorecard, and evolution details.

---

## 20. New Task Flow & Experience Re-use

From the History or Evolution view, users can easily trigger:
```text
[ Forge Similar Task ]
```
Allowing the system to leverage Evolution Memory to pre-seed optimal architectural patterns.

---

## 21. Backend API Contract Alignment

The frontend communicates with FastAPI endpoints strictly bound to shared Pydantic schemas:

| Endpoint | Method | Input Schema | Output Schema | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `/tasks/analyze` | `POST` | `{"prompt": str}` | `TaskSpec` | Analyzes and decomposes task |
| `/architectures/generate` | `POST` | `TaskSpec` | `ArchitectureSpec` | Synthesizes agent architecture |
| `/architectures/{id}` | `GET` | — | `ArchitectureSpec` | Fetches architecture topology |
| `/execution/run` | `POST` | `{"task_id": str, "architecture_id": str}` | `ExecutionResult` | Executes agent team |
| `/execution/{id}` | `GET` | — | `ExecutionResult` | Retrieves execution trace |
| `/evaluation/{id}` | `GET` | — | `EvaluationResult` | Fetches evaluation scorecard |
| `/reflection/{id}` | `GET` | — | `ReflectionResult` | Fetches reflection & recommendations |
| `/memory` | `GET` | Query params | `List[EvolutionRecord]` | Lists past evolution records |
| `/memory/{task_id}` | `GET` | — | `EvolutionRecord` | Fetches task experience record |

---

## 22. State Management Architecture

Keep frontend state cleanly partitioned:
- `Current Task`: Active prompt, decomposed subtasks, complexity rating.
- `Architecture`: Active `ArchitectureSpec`, computed React Flow nodes/edges.
- `Execution State`: Agent run status map, active tool calls, event stream log.
- `Selected Agent`: Active agent inspected in side drawer.
- `Evaluation`: Current `EvaluationResult` scorecard & reasoning points.
- `Reflection`: Detected weaknesses, root cause, architectural recommendation.
- `Evolution History`: Historical runs for the current task chain.

All API utilities and TypeScript type definitions live under:
```text
frontend/
└── lib/
    ├── api.ts      # REST API client matching backend routes
    ├── types.ts    # TypeScript types mirrors of app/schemas/
    └── utils.ts    # React Flow node/edge converters & layout helpers
```

---

## 23. Suggested Frontend Directory Structure

```text
frontend/
├── app/
│   ├── layout.tsx                     # Root shell, sidebar, system status
│   ├── page.tsx                       # Screen 1: New Task / Forge
│   ├── architecture/
│   │   └── page.tsx                   # Screen 2: Dynamic React Flow Canvas
│   ├── execution/
│   │   └── page.tsx                   # Screen 3: Live Execution & Event Stream
│   ├── evaluation/
│   │   └── page.tsx                   # Screen 4: Evaluation Scorecard & Rationale
│   ├── reflection/
│   │   └── page.tsx                   # Screen 5: Reflection & Apply Recommendation
│   ├── evolution/
│   │   └── page.tsx                   # Screen 6: Evolution Timeline & Comparison
│   └── history/
│       └── page.tsx                   # Screen 7: Historical Tasks & Re-forge
├── components/
│   ├── layout/
│   │   ├── AppShell.tsx               # Persistent topbar & sidebar container
│   │   ├── Sidebar.tsx                # Sidebar navigation
│   │   └── SystemStatus.tsx           # Backend health indicator
│   ├── task/
│   │   ├── TaskInput.tsx              # Task input textarea & example chips
│   │   ├── SynthesisProgress.tsx      # Task processing animated stages
│   │   └── ForgeButton.tsx            # Forge submission CTA
│   ├── architecture/
│   │   ├── ArchitectureCanvas.tsx     # React Flow canvas wrapper
│   │   ├── AgentNode.tsx              # Custom React Flow agent node
│   │   ├── AgentInspector.tsx         # Node details side panel
│   │   └── ArchitectureMetadata.tsx   # Topology, agent count, tool metadata
│   ├── execution/
│   │   ├── ExecutionTimeline.tsx      # Step-by-step agent progress
│   │   ├── ExecutionLog.tsx           # Technical runtime event stream
│   │   └── AgentStatus.tsx            # Live state badge
│   ├── evaluation/
│   │   ├── EvaluationSummary.tsx      # Overall score & circular ring
│   │   ├── MetricCard.tsx             # Accuracy, Completeness, Quality bars
│   │   └── EvaluationDetails.tsx      # "Why this score" explanation list
│   ├── reflection/
│   │   ├── ReflectionPanel.tsx        # Main reflection card container
│   │   ├── FailureCard.tsx            # Weakness & root-cause card
│   │   └── RecommendationCard.tsx     # Recommended change & Apply CTA
│   ├── evolution/
│   │   ├── EvolutionTimeline.tsx      # Run 1 ➔ Run 2 ➔ Run 3 timeline
│   │   └── ArchitectureComparison.tsx # Side-by-side graph & metric diff
│   └── ui/                            # Base shadcn/ui components
├── lib/
│   ├── api.ts                         # Typed API client
│   ├── types.ts                       # TypeScript contracts matching backend
│   └── utils.ts                       # Topology-to-ReactFlow converters
└── public/                            # Static assets
```

---

## 24. Animation Strategy

Animations must explain system behavior, never serve as superficial decoration:
- **Agent Node Status Transitions**: Smooth color and badge changes (`WAITING` ➔ `ACTIVE` ➔ `COMPLETED` / `FAILED`).
- **Connection Edges**: Subtle animated stroke when data is flowing between agents.
- **Synthesis Progress**: Sequential checkmarks illuminating reasoning stages.
- **Architecture Transformation**: Visual layout re-calculation when recommendations are applied.

---

## 25. Responsive Design Principles

- **Primary Target**: Desktop & Laptop workstations (1280px+), optimized for dense technical oversight.
- **Sub-1024px Behavior**: Sidebar collapses to navigation rail; React Flow canvas supports touch-drag and pinch-zoom; Agent Inspector docks as a bottom sheet.

---

## 26. Demo Mode (Mid-Sem Review)

A dedicated **Demo Mode toggle** allows running the full Golden User Journey deterministically:
```text
[ Toggle Demo Mode ] ➔ Run Healthcare / Cyber Task ➔ Synthesize ➔ Execute ➔ Evaluate ➔ Reflect ➔ Evolve
```
- Demo data is clearly segregated from production data.
- The UI explicitly denotes `[DEMO MODE ACTIVE]`, upholding academic integrity while guaranteeing 100% reliable live demonstration.

---

## 27. The Golden User Journey

```text
                    USER
                     │
                     ▼
              ENTERS TASK
                     │
                     ▼
              [ FORGE TASK ]
                     │
                     ▼
           TASK UNDERSTANDING
                     │
                     ▼
          ARCHITECTURE SYNTHESIS
                     │
                     ▼
          ┌─────────────────────┐
          │ GENERATED TEAM      │
          │                     │
          │ Research            │
          │ Analysis            │
          │ Verification        │
          │ Writer              │
          └──────────┬──────────┘
                     │
                     ▼
                EXECUTION
                     │
                     ▼
                EVALUATION
                     │
                     ▼
                 REFLECTION
                     │
                     ▼
             ARCHITECTURE CHANGE
                     │
                     ▼
                 RUN AGAIN
                     │
                     ▼
               EVOLUTION
```

---

## 28. What Makes This UI Different

| Paradigm | Workflow | UI Visualization |
| :--- | :--- | :--- |
| **Traditional Chatbot** | Prompt ➔ LLM ➔ Answer | Single text chat thread |
| **Static Multi-Agent** | Prompt ➔ Fixed DAG ➔ Output | Fixed hardcoded graph |
| **Agent Forge** | **Prompt ➔ Dynamic Synthesis ➔ Execution ➔ Evaluation ➔ Reflection ➔ Evolution ➔ Memory** | **Dynamic React Flow topology, live node inspection, qualitative reflection cards, and multi-run architecture comparison** |

---

## 29. Implementation Priority Phases

1. **Phase 1 — Foundation**: Next.js shell, App Router layout, sidebar navigation, system status indicator, Tailwind & shadcn/ui setup.
2. **Phase 2 — Core Visual**: Screen 1 (Task Input & Synthesis Animation) + Screen 2 (Architecture Canvas, custom `AgentNode`, `AgentInspector`, metadata panel).
3. **Phase 3 — Execution**: Screen 3 (Live Execution timeline, technical event stream log, dynamic node status propagation).
4. **Phase 4 — Intelligence**: Screen 4 (Evaluation scorecard, metric bars, "Why this score" cards) + Screen 5 (Reflection weakness card, root cause, [Apply Recommendation] button).
5. **Phase 5 — Evolution**: Screen 6 (Multi-run evolution timeline, side-by-side comparison) + Screen 7 (Recent tasks history table & re-forge).
6. **Phase 6 — Polish**: Refined micro-transitions, error/empty states, responsive touch controls, and Mid-Sem Demo Mode.

---

## 30. One Critical Technical Rule

**The frontend must never become the source of truth for Agent Forge architecture.**

All topologies, agent roles, tool bindings, execution traces, metric scores, and reflection diagnoses must originate from the FastAPI backend and shared Pydantic data contracts.
