# Agent Forge — Subsystem Architecture & Flow

This document details the detailed subsystem design, module interactions, and self-evolution loop of **Agent Forge**.

---

## 1. High-Level Architecture Flow

```
User Task
    │
    ▼
[Meta Controller]  ──► Analyzes prompt, decomposes subtasks & extracts required capabilities
    │
    ▼
[Architecture Generator & Tool Planner]  ──► Synthesizes dynamic topology & assigns tools
    │
    ▼
[Dynamic Agent Factory]  ──► Instantiates executable runtime Agent Objects from JSON config
    │
    ▼
[Execution Engine (LangGraph)]  ──► Runs Pipeline / Parallel multi-agent graph
    │
    ▼
[Evaluator]  ──► Computes Task Success, Output Quality & Resource Metrics
    │
    ▼
[Reflection Engine]  ──► Identifies structural vulnerabilities (e.g. missing verifier)
    │
    ▼
[Evolution Memory Store]  ──► Persists experience pairs for future architecture synthesis optimization
```

---

## 2. Component Details

### Meta Controller (`app/controller/`)
- **Responsibility**: Interprets unstructured natural language task inputs into structured `TaskSpec` models.
- **Sub-modules**:
  - `task_analyzer.py`: Main entry point for task parsing.
  - `task_decomposer.py`: Breaks complex goals into discrete subtasks.
  - `complexity_analyzer.py`: Measures task difficulty to determine required agent team depth.
  - `capability_extractor.py`: Maps subtasks to required agent capabilities.

### Architecture Generator & Tool Planner (`app/controller/architecture_generator.py`, `app/tools/`)
- **Responsibility**: Formulates `ArchitectureSpec` JSON defining topology type, dynamic agent count, prompts, and tool attachments.

### Dynamic Agent Factory (`app/agents/`)
- **Responsibility**: Dynamically constructs executable `BaseAgent` instances at runtime without relying on hard-coded `if/else` logic.

### LangGraph Execution Engine (`app/execution/`)
- **Responsibility**: Constructs dynamic `StateGraph` topologies (Pipeline, Parallel) to manage message passing, state retention, and failure retries across generated agents.

### Evaluator & Failure Analyzer (`app/evaluation/`)
- **Responsibility**: Assesses task completeness, output quality, execution time, and tool utilization.

### Reflection Engine & Architecture Modifier (`app/reflection/`)
- **Responsibility**: Diagnoses why an architecture scored poorly and generates concrete mutation recommendations (e.g. adding a Verification Agent or splitting research into parallel sub-agents).

### Evolution Memory Store (`app/memory/`)
- **Responsibility**: Stores historical execution & reflection records so future similar tasks retrieve previous architectural experience.
