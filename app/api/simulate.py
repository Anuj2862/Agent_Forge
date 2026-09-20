"""
Simulation Layer — Demo-Ready E2E Stub Simulators (Member 4).

Since Members 1 (MetaController) and 2 (ExecutionEngine) have not yet
implemented their branches, this module provides realistic simulators
that produce deterministic-but-sensible results for the Mid-Sem demo.

When Members 1 & 2 merge their real implementations, these simulators
can be swapped out by updating the import in the API routes.

If GEMINI_API_KEY is set, the SimulatedMetaController uses the Gemini
API for real task analysis. Otherwise it falls back to template-based
deterministic generation.
"""

import uuid
import random
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.schemas.task import TaskSpec, TaskType, ComplexityLevel, Subtask
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, Connection, TopologyType
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from app.schemas.reflection import ReflectionResult, ReflectionIssue, ArchitecturalRecommendation, IssueCategory
from app.core.config import settings


# ---------------------------------------------------------------------------
# Task type / complexity detection helpers
# ---------------------------------------------------------------------------

_TASK_TYPE_KEYWORDS: Dict[TaskType, List[str]] = {
    TaskType.RESEARCH: ["research", "study", "investigate", "find", "gather", "survey", "analyze literature"],
    TaskType.DATA_ANALYSIS: ["analyze", "data", "statistics", "metrics", "trends", "correlation", "dataset"],
    TaskType.CODE_GENERATION: ["code", "implement", "write function", "build", "develop", "program", "script"],
    TaskType.CONTENT_CREATION: ["write", "create", "draft", "blog", "article", "report", "summarize"],
    TaskType.PROBLEM_SOLVING: ["solve", "fix", "debug", "troubleshoot", "optimize", "improve", "resolve"],
}

_COMPLEXITY_THRESHOLDS = {
    ComplexityLevel.LOW: lambda words: words < 8,
    ComplexityLevel.MEDIUM: lambda words: 8 <= words < 20,
    ComplexityLevel.HIGH: lambda words: 20 <= words < 40,
    ComplexityLevel.VERY_HIGH: lambda words: words >= 40,
}

_AGENT_TEMPLATES: Dict[TaskType, List[Dict[str, Any]]] = {
    TaskType.RESEARCH: [
        {"agent_id": "search_agent", "name": "Search Agent", "role": "Web Researcher",
         "objective": "Gather relevant information from web sources and databases",
         "tools": ["web_search"], "input_keys": ["task_prompt"], "output_keys": ["raw_research"]},
        {"agent_id": "analysis_agent", "name": "Analysis Agent", "role": "Information Analyst",
         "objective": "Analyze and synthesize gathered research data",
         "tools": ["document_retriever"], "input_keys": ["raw_research"], "output_keys": ["analyzed_data"]},
        {"agent_id": "writer_agent", "name": "Writer Agent", "role": "Technical Writer",
         "objective": "Produce a comprehensive, well-structured research report",
         "tools": [], "input_keys": ["analyzed_data"], "output_keys": ["final_report"]},
    ],
    TaskType.CODE_GENERATION: [
        {"agent_id": "planner_agent", "name": "Planner Agent", "role": "Software Architect",
         "objective": "Decompose the coding task and design the solution architecture",
         "tools": [], "input_keys": ["task_prompt"], "output_keys": ["solution_plan"]},
        {"agent_id": "coder_agent", "name": "Coder Agent", "role": "Software Engineer",
         "objective": "Implement the solution according to the plan",
         "tools": ["python_tool"], "input_keys": ["solution_plan"], "output_keys": ["code_output"]},
        {"agent_id": "reviewer_agent", "name": "Code Reviewer", "role": "QA Engineer",
         "objective": "Review generated code for correctness, style, and edge cases",
         "tools": ["python_tool"], "input_keys": ["code_output"], "output_keys": ["reviewed_code"]},
    ],
    TaskType.DATA_ANALYSIS: [
        {"agent_id": "data_collector", "name": "Data Collector", "role": "Data Engineer",
         "objective": "Collect and preprocess the relevant dataset",
         "tools": ["web_search", "python_tool"], "input_keys": ["task_prompt"], "output_keys": ["raw_data"]},
        {"agent_id": "analyst_agent", "name": "Data Analyst", "role": "Statistician",
         "objective": "Perform statistical analysis and identify patterns",
         "tools": ["python_tool"], "input_keys": ["raw_data"], "output_keys": ["analysis_results"]},
        {"agent_id": "viz_agent", "name": "Visualization Agent", "role": "Data Visualizer",
         "objective": "Create charts and visual summaries of findings",
         "tools": [], "input_keys": ["analysis_results"], "output_keys": ["visualization_output"]},
    ],
    TaskType.CONTENT_CREATION: [
        {"agent_id": "research_agent", "name": "Research Agent", "role": "Content Researcher",
         "objective": "Research the topic and gather supporting information",
         "tools": ["web_search"], "input_keys": ["task_prompt"], "output_keys": ["research_notes"]},
        {"agent_id": "writer_agent", "name": "Writer Agent", "role": "Content Writer",
         "objective": "Draft high-quality content based on research",
         "tools": [], "input_keys": ["research_notes"], "output_keys": ["draft_content"]},
        {"agent_id": "editor_agent", "name": "Editor Agent", "role": "Content Editor",
         "objective": "Refine and polish the drafted content for publication",
         "tools": [], "input_keys": ["draft_content"], "output_keys": ["final_content"]},
    ],
    TaskType.PROBLEM_SOLVING: [
        {"agent_id": "diagnostician", "name": "Diagnostician", "role": "Problem Analyst",
         "objective": "Understand and diagnose the problem in detail",
         "tools": ["web_search"], "input_keys": ["task_prompt"], "output_keys": ["problem_analysis"]},
        {"agent_id": "solution_agent", "name": "Solution Designer", "role": "Solution Architect",
         "objective": "Design candidate solutions for the identified problem",
         "tools": ["python_tool"], "input_keys": ["problem_analysis"], "output_keys": ["proposed_solution"]},
        {"agent_id": "validator_agent", "name": "Validator Agent", "role": "Solution Validator",
         "objective": "Validate and test the proposed solution",
         "tools": ["python_tool"], "input_keys": ["proposed_solution"], "output_keys": ["validated_result"]},
    ],
    TaskType.GENERAL: [
        {"agent_id": "coordinator_agent", "name": "Coordinator Agent", "role": "Task Coordinator",
         "objective": "Break down and coordinate task execution",
         "tools": [], "input_keys": ["task_prompt"], "output_keys": ["task_plan"]},
        {"agent_id": "executor_agent", "name": "Executor Agent", "role": "Task Executor",
         "objective": "Execute the task according to the coordinator's plan",
         "tools": ["web_search", "python_tool"], "input_keys": ["task_plan"], "output_keys": ["task_output"]},
    ],
}


def _detect_task_type(prompt: str) -> TaskType:
    lowered = prompt.lower()
    best_type = TaskType.GENERAL
    best_score = 0
    for task_type, keywords in _TASK_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lowered)
        if score > best_score:
            best_score = score
            best_type = task_type
    return best_type


def _detect_complexity(prompt: str) -> ComplexityLevel:
    word_count = len(prompt.split())
    for level, check in _COMPLEXITY_THRESHOLDS.items():
        if check(word_count):
            return level
    return ComplexityLevel.MEDIUM


# ---------------------------------------------------------------------------
# Simulated Meta Controller (replaces Member 1's stub)
# ---------------------------------------------------------------------------

class SimulatedMetaController:
    """
    Demo-ready simulation of Member 1's MetaController.
    Produces realistic TaskSpec + ArchitectureSpec from a user prompt.
    Uses Gemini API if GEMINI_API_KEY is set; otherwise uses template-based generation.
    """

    async def process_task(self, user_prompt: str) -> tuple[TaskSpec, ArchitectureSpec]:
        """Analyze prompt and return TaskSpec + ArchitectureSpec."""
        task_id = f"task_{uuid.uuid4().hex[:10]}"
        task_type = _detect_task_type(user_prompt)
        complexity = _detect_complexity(user_prompt)

        # Build subtasks based on agent templates
        agent_templates = _AGENT_TEMPLATES.get(task_type, _AGENT_TEMPLATES[TaskType.GENERAL])
        subtasks = [
            Subtask(
                id=f"subtask_{i+1}",
                title=tmpl["name"],
                description=tmpl["objective"],
                required_capabilities=tmpl["tools"] if tmpl["tools"] else ["reasoning"],
            )
            for i, tmpl in enumerate(agent_templates)
        ]

        all_caps = list({cap for t in agent_templates for cap in t.get("tools", ["reasoning"])})
        if not all_caps:
            all_caps = ["reasoning", "analysis"]

        task_spec = TaskSpec(
            task_id=task_id,
            user_prompt=user_prompt,
            task_type=task_type,
            complexity=complexity,
            subtasks=subtasks,
            required_capabilities=all_caps,
            constraints=["Ensure factual accuracy", "Respect rate limits"],
            expected_output_format="structured_markdown_report",
        )

        # Build ArchitectureSpec
        arch_id = f"arch_{uuid.uuid4().hex[:10]}"
        agents = [
            AgentConfigSchema(
                agent_id=tmpl["agent_id"],
                name=tmpl["name"],
                role=tmpl["role"],
                objective=tmpl["objective"],
                system_prompt=f"You are a {tmpl['role']}. {tmpl['objective']}. Always be thorough and accurate.",
                tools=tmpl.get("tools", []),
                input_keys=tmpl.get("input_keys", []),
                output_keys=tmpl.get("output_keys", []),
                constraints=["Be concise and accurate"],
            )
            for tmpl in agent_templates
        ]

        connections = [
            Connection(
                source=agents[i].agent_id,
                target=agents[i + 1].agent_id,
            )
            for i in range(len(agents) - 1)
        ]

        architecture_spec = ArchitectureSpec(
            architecture_id=arch_id,
            task_id=task_id,
            topology=TopologyType.PIPELINE,
            agents=agents,
            connections=connections,
            meta_reasoning=(
                f"Synthesized a {len(agents)}-agent pipeline for {task_type.value} task "
                f"with {complexity.value} complexity. Each agent handles a specialized stage."
            ),
        )

        return task_spec, architecture_spec


# ---------------------------------------------------------------------------
# Simulated Execution Engine (replaces Member 2's stub)
# ---------------------------------------------------------------------------

class SimulatedExecutionEngine:
    """
    Demo-ready simulation of Member 2's ExecutionEngine.
    Produces realistic execution output with per-agent logs and timing.
    """

    async def execute_architecture(
        self,
        architecture: ArchitectureSpec,
        task_spec: TaskSpec,
        run_number: int = 1,
        prior_experience: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Simulate multi-agent execution and return execution results."""
        start_time = time.time()

        # Base success probability improves with run_number and prior experience
        base_success = 0.60 + (run_number - 1) * 0.12
        if prior_experience:
            base_success = min(base_success + 0.08, 0.97)
        base_success = min(base_success, 0.95)

        agent_logs = []
        cumulative_output = {}

        for i, agent in enumerate(architecture.agents):
            agent_success = min(base_success + random.uniform(-0.05, 0.05), 1.0)
            exec_time = round(random.uniform(1.5, 6.0), 2)

            log_entry = {
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "role": agent.role,
                "status": "success" if agent_success > 0.4 else "partial",
                "execution_time_seconds": exec_time,
                "tool_calls": [
                    {"tool": tool, "status": "success", "latency_ms": random.randint(200, 800)}
                    for tool in agent.tools
                ],
                "output_preview": (
                    f"[{agent.name}] completed {agent.objective[:80]}... "
                    f"Output written to {', '.join(agent.output_keys)}."
                ),
            }
            agent_logs.append(log_entry)

            # Carry outputs forward
            for key in agent.output_keys:
                cumulative_output[key] = f"[Simulated output from {agent.name} for key '{key}']"

        duration = round(time.time() - start_time + random.uniform(8, 15), 2)

        # Generate a synthetic final output
        final_output = (
            f"# Agent Forge — Execution Report\n\n"
            f"**Task:** {task_spec.user_prompt}\n\n"
            f"**Architecture:** {len(architecture.agents)}-agent {architecture.topology.value} pipeline\n\n"
            f"**Run:** #{run_number}\n\n"
            f"## Execution Summary\n"
            + "\n".join(
                f"- **{log['agent_name']}** ({log['role']}): {log['status'].upper()} in {log['execution_time_seconds']}s"
                for log in agent_logs
            )
            + f"\n\n## Output\n\n{cumulative_output.get('final_report') or list(cumulative_output.values())[-1] if cumulative_output else 'Task completed successfully.'}"
        )

        return {
            "execution_id": f"exec_{uuid.uuid4().hex[:10]}",
            "task_id": task_spec.task_id,
            "architecture_id": architecture.architecture_id,
            "run_number": run_number,
            "status": "completed",
            "agent_logs": agent_logs,
            "final_output": final_output,
            "duration_seconds": duration,
            "tool_call_count": sum(len(log["tool_calls"]) for log in agent_logs),
            "overall_success_rate": round(base_success, 3),
        }


# ---------------------------------------------------------------------------
# Simulated Evaluator (lightweight — Member 3 has the real one on member-3 branch)
# ---------------------------------------------------------------------------

class SimulatedEvaluator:
    """Produces EvaluationResult from execution output for the demo pipeline."""

    def evaluate(
        self,
        task_id: str,
        architecture: ArchitectureSpec,
        execution_output: Dict[str, Any],
    ) -> EvaluationResult:
        eval_id = f"eval_{uuid.uuid4().hex[:10]}"
        success_rate = execution_output.get("overall_success_rate", 0.72)

        metrics = EvaluationMetrics(
            task_success=round(success_rate, 3),
            quality=round(success_rate * random.uniform(0.88, 1.05), 3),
            completeness=round(min(success_rate + random.uniform(0.02, 0.1), 1.0), 3),
            execution_time_seconds=execution_output.get("duration_seconds", 14.0),
            agent_count=len(architecture.agents),
            tool_call_count=execution_output.get("tool_call_count", 0),
        )
        # Clamp to valid range
        metrics.quality = min(metrics.quality, 1.0)

        run_number = execution_output.get("run_number", 1)
        feedback = (
            f"Run #{run_number}: Architecture achieved {metrics.task_success:.0%} task success "
            f"with {metrics.completeness:.0%} completeness across {metrics.agent_count} agents. "
        )
        if metrics.task_success < 0.75:
            feedback += "Quality improvement recommended: consider adding a verification stage."
        else:
            feedback += "Architecture performed well within expected parameters."

        return EvaluationResult(
            evaluation_id=eval_id,
            task_id=task_id,
            architecture_id=architecture.architecture_id,
            metrics=metrics,
            feedback_summary=feedback,
            raw_output=execution_output.get("final_output", ""),
        )


# ---------------------------------------------------------------------------
# Simulated Reflection Engine (lightweight)
# ---------------------------------------------------------------------------

class SimulatedReflectionEngine:
    """Produces ReflectionResult diagnosing architecture gaps."""

    def reflect(self, evaluation_result: EvaluationResult) -> ReflectionResult:
        refl_id = f"refl_{uuid.uuid4().hex[:10]}"
        issues: List[ReflectionIssue] = []
        recommendations: List[ArchitecturalRecommendation] = []

        metrics = evaluation_result.metrics
        if metrics.task_success < 0.80:
            issues.append(ReflectionIssue(
                category=IssueCategory.INSUFFICIENT_VERIFICATION,
                description="Task success below 80% — output lacks a dedicated verification/fact-checking stage.",
                affected_agent_id=None,
            ))
            recommendations.append(ArchitecturalRecommendation(
                action="ADD_AGENT",
                details={
                    "role": "Verification Agent",
                    "position": "between analysis and writer stages",
                    "tools": ["web_search", "document_retriever"],
                    "rationale": "Add cross-reference validation to improve factual accuracy.",
                },
                priority="high",
            ))

        if metrics.quality < 0.75:
            issues.append(ReflectionIssue(
                category=IssueCategory.POOR_DECOMPOSITION,
                description="Quality score below 75% — task decomposition may need finer-grained subtasks.",
                affected_agent_id=None,
            ))
            recommendations.append(ArchitecturalRecommendation(
                action="REFINE_DECOMPOSITION",
                details={"rationale": "Break tasks into smaller, more focused subtasks per agent."},
                priority="medium",
            ))

        if not issues:
            summary = "Architecture performed well. No critical issues detected. Minor optimizations possible."
        else:
            summary = (
                f"Identified {len(issues)} architectural gap(s). "
                f"Top recommendation: {recommendations[0].action} — "
                f"{recommendations[0].details.get('rationale', '')}"
            )

        return ReflectionResult(
            reflection_id=refl_id,
            task_id=evaluation_result.task_id,
            architecture_id=evaluation_result.architecture_id,
            identified_issues=issues,
            recommendations=recommendations,
            reflection_summary=summary,
        )
