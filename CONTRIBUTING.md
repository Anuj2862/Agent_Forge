# Agent Forge — Developer & Contribution Guidelines

Welcome to the **Agent Forge** engineering design and innovation repository. To maintain high code quality, integration stability, and clear module isolation across our team of four, all contributors must strictly adhere to these contribution guidelines.

---

## 1. Branch Strategy & Naming Conventions

We utilize a centralized Git workflow with two primary long-lived branches and dedicated short-lived feature branches:

### Primary Branches
- `main`: Stable, tested, and integrated release branch. **No direct pushes permitted.**
- `common`: Shared integration and development branch for all four members.

### Member Branches
Development work occurs on dedicated member branches branched off `common`:
- `member-1`: Meta Controller + Task Analysis + Architecture Generator
- `member-2`: Agent Factory + Tool Planner + Communication Graph + Execution Engine
- `member-3`: Evaluator + Failure Analyzer + Reflection Engine + Architecture Improvement
- `member-4`: Evolution Memory + FastAPI + Next.js Frontend + React Flow Visualization + Integration

---

## 2. Commit Message Standards

Commits should be small, atomic, and descriptive. Use standard conventional commit prefixes:

- `feat`: A new feature or component
- `fix`: A bug fix
- `docs`: Documentation updates
- `style`: Formatting, missing semi-colons, no code logic change
- `refactor`: Refactoring existing logic without changing external behavior
- `test`: Adding or modifying unit tests
- `chore`: Maintenance tasks, dependencies, git configuration

### Format:
```
<type>: <short summary in imperative mood>

[optional detailed description]
```

### Examples:
- `feat: add task complexity analyzer schema`
- `fix: resolve parallel executor message passing deadlock`
- `docs: update API documentation for evaluation endpoints`

---

## 3. Pull Request (PR) Workflow

```
Member Branch  ──► Local Testing  ──► Git Commit  ──► PR to common  ──► Integration Testing  ──► Merge to main
```

1. **Keep PRs Focused**: A PR should address a single responsibility domain.
2. **Self-Review**: Run local tests (`pytest`) before requesting review.
3. **PR Description**: Include a summary of changes, components affected, and verification steps.
4. **Code Review**: At least one other team member must review and approve the PR before merging into `common`.
5. **Merging to Main**: Merges from `common` to `main` occur only during scheduled integration milestones.

---

## 4. Code Ownership & Subsystem Boundaries

Each team member owns specific subsystem directories and is responsible for their stability, test coverage, and documentation:

- **Member 1 (`member-1`)**: `app/controller/`
  - Responsibilities: Meta Controller, Task Decomposer, Complexity Assessor, Architecture Generator.
  - Contract Deliverable: Produces validated `TaskSpec` and `ArchitectureSpec` for dynamic graph creation.
- **Member 2 (`member-2`)**: `app/agents/`, `app/tools/`, `app/execution/`
  - Responsibilities: Dynamic Agent Factory, Agent Runtime, Tool Planner, Tool Registry, LangGraph Execution Engine.
  - Contract Deliverable: Executes agent networks dynamically and produces timestamped `ExecutionResult` with traces and tool logs.
- **Member 3 (`member-3`)**: `app/evaluation/`, `app/reflection/`
  - Responsibilities: Evaluator & Multi-Metric Scorer, Failure Analyzer, Reflection Engine, Architecture Modifier.
  - Contract Deliverable: Produces `EvaluationResult` with qualitative rationale and `ReflectionResult` with actionable recommendations.
- **Member 4 (`member-4`)**: `app/memory/`, `app/api/`, `frontend/`
  - Responsibilities: Evolution Memory Store, FastAPI Endpoints, Next.js Frontend Dashboard (7 screens), React Flow Graph Engine, Integration.
  - Contract Deliverable: Provides the interactive production web interface and REST/WebSocket API endpoints.
- **Shared / All**: `app/schemas/`, `app/core/`, `tests/`, `docs/`

---

## 5. Shared Schema Rules (Strict)

Shared Pydantic contracts in `app/schemas/` define the API boundaries between member modules and the frontend:

- **Do not casually modify existing schema fields.** Changing a shared contract can break other members' components and frontend TypeScript typings.
- If a schema field must be added or altered:
  1. Discuss the change with the affected team members first.
  2. Maintain backward compatibility (e.g., use `Optional` fields with default values).
  3. Mirror updates to `frontend/lib/types.ts`.
  4. Update `tests/test_schemas.py` to verify the schema updates.

---

## 6. Secrets & Environment Rules

- **NEVER commit secrets or API keys.**
- Keep secrets strictly inside your local `.env` file (which is ignored by Git).
- If your component introduces a new environment variable requirement, add a placeholder and comment to `.env.example` in the same commit.

---

## 7. Frontend UI/UX & Coding Guidelines

All frontend contributions under `frontend/` must adhere to the design specification in [`docs/frontend_spec.md`](docs/frontend_spec.md):

1. **AI Laboratory Aesthetic**: Technical, minimal, information-rich, desktop-optimized.
   - Use subtle borders (`border-border/40`), dark-mode elevation, clean typography, and monospace labels for IDs and latencies.
   - **Prohibited**: Excessive decorative gradients, continuous particle simulations, glowing sci-fi borders, or animations that impede user interaction.
2. **Backend is the Source of Truth**:
   - Never hardcode agent topologies, mock scores, or fake execution states in the UI.
   - All graphs, agent roles, and evaluation scores must flow directly from the backend API.
3. **TypeScript Strict Mode**:
   - All components, props, and API payloads must have explicit TypeScript types matching `app/schemas/`.
4. **React Flow Best Practices**:
   - Agent nodes must use custom React Flow node components reflecting live states (`WAITING`, `ACTIVE`, `COMPLETED`, `FAILED`).
   - Node clicks must dynamically populate the `AgentInspector` side drawer.

---

## 8. Mid-Sem Review Demo Mode Guidelines

To ensure 100% reliable presentations during academic and patent milestone reviews:
- Include a dedicated **Demo Mode** toggle in the frontend header.
- Demo mode must run the complete Golden User Journey deterministically (Run 1 initial synthesis ➔ Execution ➔ Evaluation 68% ➔ Reflection ➔ Evolved Run 2 synthesis ➔ Execution ➔ Evaluation 88%).
- The UI must clearly indicate `[DEMO MODE ACTIVE]` to maintain strict academic transparency.

---

## 9. Testing Requirements

- Every new module or schema must include unit tests in `tests/`.
- Ensure all tests pass locally prior to creating a Pull Request:
  ```bash
  pytest -v
  ```
- Untested PRs or broken integration builds will not be merged into `common`.

