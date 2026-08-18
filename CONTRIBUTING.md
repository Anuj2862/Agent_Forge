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
- `member-4`: Evolution Memory + FastAPI + Streamlit + Integration

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

Each team member owns specific subsystem directories. Modify files outside your assigned domain only when necessary for integration, and notify the owner:

- **Member 1**: `app/controller/`
- **Member 2**: `app/agents/`, `app/tools/`, `app/execution/`
- **Member 3**: `app/evaluation/`, `app/reflection/`
- **Member 4**: `app/memory/`, `app/api/`, `frontend/`
- **Shared / All**: `app/schemas/`, `app/core/`, `tests/`

---

## 5. Shared Schema Rules (Strict)

Shared Pydantic contracts in `app/schemas/` define the API boundaries between member modules.

- **Do not casually modify existing schema fields.** Changing a shared contract can break other members' components.
- If a schema field must be added or altered:
  1. Discuss the change with the affected team members first.
  2. Maintain backward compatibility (e.g., use `Optional` fields with default values).
  3. Update `tests/test_schemas.py` to verify the schema updates.

---

## 6. Secrets & Environment Rules

- **NEVER commit secrets or API keys.**
- Keep secrets strictly inside your local `.env` file (which is ignored by Git).
- If your component introduces a new environment variable requirement, add a placeholder and comment to `.env.example` in the same commit.

---

## 7. Testing Requirements

- Every new module or schema must include unit tests in `tests/`.
- Ensure all tests pass locally prior to creating a Pull Request:
  ```bash
  pytest
  ```
- Un-tested PRs or broken integration builds will not be merged into `common`.
