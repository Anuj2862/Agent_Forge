# Member 1 — Architecture Generation Examples

## Overview

These examples demonstrate the dynamic architecture synthesis implemented by
Member 1's Meta Controller.

The system accepts a natural-language task and produces a validated
`ArchitectureSpec` containing dynamically generated agents, tools,
topology, connections, and meta-reasoning.

---

# Example 1 — Data Analysis

## Input Task

> Analyze a CSV sales dataset, identify the top 5 products by revenue,
> and return the results as a table.

## Generated Topology

```text
parallel
```

## Generated Agent Team

| Agent                               | Role                          | Tools                                                        |
| ----------------------------------- | ----------------------------- | ------------------------------------------------------------ |
| Load Sales Dataset Agent            | Load Sales Dataset            | file_system_access, data_loading                             |
| Calculate Product Revenue Agent     | Calculate Product Revenue     | data_manipulation, mathematical_operations, data_aggregation |
| Identify Top 5 Products Agent       | Identify Top 5 Products       | data_sorting, data_filtering                                 |
| Format Results As Table Agent       | Format Results As Table       | data_formatting, output_generation                           |

## Connections

```text
None

Parallel topology — agents are represented as independent subtasks.
```

## Architecture Reasoning

The task was classified as `data_analysis`. Its subtasks can be handled
independently, so a parallel multi-agent topology was selected.

---

# Example 2 — Code Generation

## Input Task

> Create a Python program that reads a list of numbers, finds the largest
> value, validates the input, and returns the result with a short explanation.

## Generated Topology

```text
pipeline
```

## Generated Agent Team

| Agent                                       | Role                                  | Tools                                                            |
| ------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------- |
| Design Input & Validation Strategy Agent    | Design Input & Validation Strategy    | program_design, input_specification, validation_rule_definition  |
| Implement Input Reading And Parsing Agent   | Implement Input Reading and Parsing   | python_programming, console_input_handling, string_parsing       |
| Implement Robust Input Validation Logic Agent | Implement Robust Input Validation Logic | python_programming, data_type_validation, error_handling       |
| Implement Largest Value Finding Algorithm Agent | Implement Largest Value Finding Algorithm | python_programming, list_iteration, max_value_finding_algorithm |
| Generate Output With Explanation Agent      | Generate Output with Explanation      | python_programming, string_formatting, user_output_generation    |

## Connections

```text
subtask_1 → subtask_2 → subtask_3 → subtask_4 → subtask_5
```

## Architecture Reasoning

The task was classified as `code_generation`. Its subtasks were represented
as an ordered workflow, so a pipeline topology was selected.

---

# Dynamic Architecture Comparison

| Property     | Data Analysis                                 | Code Generation                                    |
| ------------ | --------------------------------------------- | -------------------------------------------------- |
| Task Type    | `data_analysis`                               | `code_generation`                                  |
| Topology     | `parallel`                                    | `pipeline`                                         |
| Agents       | 4                                             | 5                                                  |
| Agent Team   | Data-processing agents                        | Code-implementation agents                         |
| Capabilities | Data loading, aggregation, sorting, filtering | Python programming, parsing, validation, iteration |
| Connections  | None (independent)                            | 4 sequential edges                                 |

## Result

The examples demonstrate that the architecture is not a fixed workflow.

Different natural-language tasks produce different:

* Agent teams
* Agent roles
* Required tools/capabilities
* Topologies
* Connection structures

Both generated architectures were successfully validated as
`ArchitectureSpec` objects using the shared Pydantic schemas.
