# Agent Forge — Master Implementation Plan

**Objective**: Complete the Agent Forge repository into a fully functional, constraint-aware, failure-driven, persistent, and secure multi-agent architecture laboratory.

---

## Phase A: Baseline, Contracts & Shared Validator
1. **Extend `TaskSpec` and `TaskSubmitRequest`**:
   - Add typed fields: `max_agents: Optional[int]`, `max_execution_time_seconds: Optional[float]`, `allowed_tools: List[str]`, `forbidden_tools: List[str]`, `required_capabilities: List[str]`.
   - Update `app/schemas/task.py` and `app/api/task_routes.py`.
2. **Implement Centralized `ArchitectureValidator`**:
   - Create `app/schemas/validator.py` (or `app/core/validator.py`).
   - Validate: unique non-empty agent IDs, valid connections without dangling edges, cycle safety, tool restrictions (forbidden/allowed), agent-count hard limits, required verification stages.
   - Return structured `ValidationResult(is_valid: bool, errors: List[ValidationErrorDetail])`.

---

## Phase B: Correctness-Critical Backend
1. **Constraint Parsing & Preservation in `TaskAnalyzer`**:
   - In `app/controller/task_analyzer.py`:
     - Structured fields take precedence.
     - Natural-language pattern matching for `max_agents=(\d+)`, `maximum (\d+) agents`, `forbidden_tools`, `no web search`, etc.
2. **Constraint-Aware Synthesis in `ArchitectureGenerator`**:
   - In `app/controller/architecture_generator.py`:
     - If subtask count exceeds `max_agents`, cluster subtasks into at most `max_agents` agents.
     - Run `ArchitectureValidator` before returning `ArchitectureSpec`.
3. **Constraint-Safe Mutation in `ArchitectureModifier`**:
   - In `app/reflection/architecture_modifier.py`:
     - Run `ArchitectureValidator` against `task_spec` constraints (especially `max_agents`).
     - If an `ADD_AGENT` recommendation violates `max_agents`, reject the mutation or substitute a tool/prompt change.
4. **Build the Evolution Decision Engine**:
   - Create `app/evaluation/decision_policy.py`:
     - Class `EvolutionDecisionPolicy` returning typed `EvolutionDecision(status: ACCEPTED|REJECTED|INCONCLUSIVE, reason_codes: List[str], rationale: str, deltas: Dict[str, float])`.
     - Reject on hard-constraint violation.
     - Reject on quality regression or failed candidate execution.
     - Accept on quality improvement meeting threshold.
     - Inconclusive on marginal deltas or missing data.
5. **Complete Orchestration Service**:
   - Create `app/controller/orchestration_service.py` to coordinate the full end-to-end loop: Task → V1 → Execute V1 → Evaluate V1 → Diagnose → Reflect → Mutate → Validate V2 → Execute V2 → Evaluate V2 → Decide → Persist.

---

## Phase C: Persistence & Active Evolutionary Memory
1. **SQLAlchemy ORM Entities**:
   - In `app/memory/database.py` and `memory_store.py`:
     - `TaskRecordORM`: `task_id`, `user_prompt`, `max_agents`, `constraints`, `status`, `created_at`, `task_spec_json`, `architecture_spec_json`.
     - `ExecutionRecordORM`: `execution_id`, `task_id`, `architecture_id`, `run_number`, `status`, `duration_seconds`, `result_json`, `created_at`.
     - `EvaluationRecordORM`: `evaluation_id`, `task_id`, `execution_id`, `run_number`, `overall_score`, `metrics_json`, `feedback_summary`, `reflection_json`.
     - `EvolutionDecisionORM`: `decision_id`, `task_id`, `v1_arch_id`, `v2_arch_id`, `status`, `reason_codes`, `rationale`, `deltas_json`.
2. **Replace In-Memory Dictionaries**:
   - Refactor `task_routes.py`, `execution_routes.py`, `evaluation_routes.py`, and `architecture_routes.py` to read and write database records asynchronously.
3. **Active Memory Integration**:
   - In `app/controller/meta_controller.py`:
     - Call `MemoryRetriever` before synthesis to retrieve prior high-rated architectures for the matching task type and complexity.
     - Feed prior successful patterns into `ArchitectureGenerator`.

---

## Phase D: Execution Quality, Tool Dispatch & Sandboxed Python
1. **Intentional Tool Dispatch**:
   - In `app/agents/base_agent.py`:
     - Do not execute tools blindly in a loop.
     - Parse input / objective to decide whether a tool call is needed.
2. **Clean Offline Provider States**:
   - In `app/tools/web_search.py`:
     - Remove `example.com` fake results.
     - Return explicit status: `UNAVAILABLE` or `NO_CREDENTIALS` when API keys are absent.
3. **Safe Python Tool Execution**:
   - In `app/tools/python_tool.py`:
     - Implement subprocess / isolated execution with strict timeout (e.g. 5s), memory limits, restricted builtins, and sanitized environment.

---

## Phase E: Full-Stack Integration & Quality Gates
1. **Fix API Contracts**:
   - Ensure `GET /tasks/{id}` includes `latest_evaluation` and `evolution_decision`.
   - Update `frontend/lib/api.ts` with typed interfaces.
2. **UI Enhancements**:
   - In `frontend/components/TaskSubmitForm.tsx`: add expandable inputs for `max_agents` and constraints.
   - In `frontend/app/evolution/page.tsx`: remove hardcoded `+48.0%` and bind dynamic deltas + decision status banner (`ACCEPTED` / `REJECTED`).
   - In `frontend/app/memory/page.tsx`: align dropdown options with backend `TaskType` enum.
   - In `frontend/app/settings/page.tsx`: bind actual settings or show as read-only.
3. **Clean ESLint & TypeScript**:
   - Fix `@typescript-eslint/no-explicit-any` and unescaped entities across all frontend files.
   - Verify `npm --prefix frontend run lint` and `npm --prefix frontend run build` pass cleanly.

---

## Phase F: Testing, CI & Final Verification
1. **Unit & Integration Tests**:
   - Test constraint parsing, enforcement, decision policy, DB restart persistence, and security isolation.
2. **CI Workflow**:
   - Create `.github/workflows/ci.yml` running pytest, frontend lint, and Next.js build.
3. **Documentation & Final Delivery**:
   - Update `README.md` and `.env.example`.
   - Generate `docs/IMPLEMENTATION_REPORT.md`.
