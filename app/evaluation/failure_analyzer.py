"""
Architectural Failure Analyzer for Agent Forge.
Diagnoses systemic root causes and architectural weaknesses from execution and evaluation evidence.
"""

from typing import List, Dict, Any, Optional
from app.schemas.task import TaskSpec, ComplexityLevel, TaskType
from app.schemas.architecture import ArchitectureSpec, TopologyType
from app.schemas.execution import ExecutionResult, ExecutionStatus
from app.schemas.evaluation import EvaluationResult
from app.schemas.reflection import ReflectionIssue, IssueCategory
from app.core.logging import logger


class FailureAnalyzer:
    """Diagnoses why an architecture performed poorly and identifies structural root causes."""

    def diagnose(
        self,
        task_spec: Optional[TaskSpec],
        architecture: ArchitectureSpec,
        execution_result: ExecutionResult,
        evaluation_result: EvaluationResult,
    ) -> List[ReflectionIssue]:
        """
        Main diagnostic entrypoint. Analyzes architecture and execution data to produce structured issues.
        """
        if isinstance(execution_result, dict):
            execution_result = ExecutionResult.model_validate(execution_result)

        logger.info(f"[FAILURE] Analyzing root causes for architecture={architecture.architecture_id}")
        issues: List[ReflectionIssue] = []

        # 1. Check Missing Verification Stage
        verif_issue = self._check_missing_verification(task_spec, architecture, execution_result, evaluation_result)
        if verif_issue:
            issues.append(verif_issue)

        # 2. Check Missing / Incorrect Tool Assignment
        tool_issues = self._check_tool_assignment(task_spec, architecture, execution_result)
        issues.extend(tool_issues)

        # 3. Check Incomplete Subtask Coverage / Poor Task Decomposition
        decomp_issue = self._check_task_coverage(task_spec, architecture, evaluation_result)
        if decomp_issue:
            issues.append(decomp_issue)

        # 4. Check Redundant Agents / Inefficient Agent Count
        redundant_issue = self._check_redundant_agents(task_spec, architecture, evaluation_result)
        if redundant_issue:
            issues.append(redundant_issue)

        # 5. Check Communication Topology Issues
        topology_issue = self._check_topology(task_spec, architecture)
        if topology_issue:
            issues.append(topology_issue)

        # 6. Check Agent Execution / Reasoning Failures
        reasoning_issues = self._check_agent_failures(execution_result)
        issues.extend(reasoning_issues)

        # 7. Check Dependency Failures
        dep_issue = self._check_dependency_failures(architecture, execution_result)
        if dep_issue:
            issues.append(dep_issue)

        # 8. Check Excessive Iterations
        iter_issue = self._check_excessive_iterations(execution_result)
        if iter_issue:
            issues.append(iter_issue)

        # 9. Check Insufficient Research
        research_issue = self._check_insufficient_research(task_spec, architecture, execution_result)
        if research_issue:
            issues.append(research_issue)

        for issue in issues:
            logger.info(
                f"[FAILURE] Detected: [{issue.category.value}] severity={issue.severity} | {issue.description}"
            )

        return issues

    def _check_missing_verification(
        self,
        task_spec: Optional[TaskSpec],
        architecture: ArchitectureSpec,
        execution_result: ExecutionResult,
        evaluation_result: EvaluationResult,
    ) -> Optional[ReflectionIssue]:
        """Detects absence of independent verification stage when factual accuracy is needed."""
        # Check if architecture contains any verification agent by role or name
        verifier_agents = [
            a for a in architecture.agents
            if any(term in (a.role + " " + a.name).lower() for term in ["verif", "validator", "fact_check", "fact check", "critic"])
        ]

        # Criteria for needing verification:
        task_requires_verif = False
        if task_spec:
            task_text = (task_spec.user_prompt + " " + " ".join(task_spec.required_capabilities)).lower()
            if any(t in task_text for t in ["verif", "fact", "truth", "accuracy", "reliable", "research"]):
                task_requires_verif = True

        verification_unfulfilled = evaluation_result.metrics.verification_status in ("Unverified", "Failed Verification")

        if not verifier_agents and (task_requires_verif or verification_unfulfilled):
            evidence = (
                f"Evaluation marked verification status as '{evaluation_result.metrics.verification_status}' "
                f"with accuracy {evaluation_result.metrics.accuracy:.2f}. "
                f"Architecture has {len(architecture.agents)} agents ({', '.join(a.agent_id for a in architecture.agents)}) "
                f"with no dedicated verification stage."
            )
            return ReflectionIssue(
                category=IssueCategory.INSUFFICIENT_VERIFICATION,
                description="Architecture lacks an independent verification stage to corroborate factual claims.",
                affected_agent_id=None,
                severity="high",
                evidence=evidence,
                affected_component="architecture",
            )
        return None

    def _check_tool_assignment(
        self,
        task_spec: Optional[TaskSpec],
        architecture: ArchitectureSpec,
        execution_result: ExecutionResult,
    ) -> List[ReflectionIssue]:
        """Detects required capabilities that lack assigned tools."""
        issues = []
        if not task_spec:
            return issues

        all_assigned_tools = set()
        for agent in architecture.agents:
            all_assigned_tools.update(agent.tools)

        # Mapping of capabilities to recommended tools
        capability_tool_map = {
            "web_search": "web_search",
            "search": "web_search",
            "information_retrieval": "web_search",
            "calculation": "calculator",
            "math": "calculator",
            "code_execution": "python_interpreter",
            "coding": "python_interpreter",
        }

        for cap in task_spec.required_capabilities:
            cap_lower = cap.lower()
            for tool_cap, expected_tool in capability_tool_map.items():
                if tool_cap in cap_lower and expected_tool not in all_assigned_tools:
                    issues.append(
                        ReflectionIssue(
                            category=IssueCategory.MISSING_TOOL,
                            description=f"Required capability '{cap}' lacks assigned tool '{expected_tool}'.",
                            affected_agent_id=architecture.agents[0].agent_id if architecture.agents else None,
                            severity="high",
                            evidence=f"Task required '{cap}', but no agent in architecture was assigned '{expected_tool}'.",
                            affected_component="tools",
                        )
                    )
        return issues

    def _check_task_coverage(
        self,
        task_spec: Optional[TaskSpec],
        architecture: ArchitectureSpec,
        evaluation_result: EvaluationResult,
    ) -> Optional[ReflectionIssue]:
        """Checks if decomposed subtasks from TaskSpec have matching agents or coverage."""
        if not task_spec or not task_spec.subtasks:
            return None

        if evaluation_result.metrics.completeness < 0.60:
            agent_roles = " ".join(a.role.lower() + " " + a.objective.lower() for a in architecture.agents)
            uncovered = [
                st.title for st in task_spec.subtasks
                if not any(w.lower() in agent_roles for w in st.title.split() if len(w) > 3)
            ]
            evidence = (
                f"Completeness is {evaluation_result.metrics.completeness:.2f}. "
                f"Uncovered subtasks: {', '.join(uncovered) if uncovered else 'multiple subtasks'}."
            )
            return ReflectionIssue(
                category=IssueCategory.INCOMPLETE_TASK_COVERAGE,
                description="Task decomposition is incomplete; several required subtasks lack specialized agent coverage.",
                affected_agent_id=None,
                severity="high",
                evidence=evidence,
                affected_component="architecture",
            )
        return None

    def _check_redundant_agents(
        self,
        task_spec: Optional[TaskSpec],
        architecture: ArchitectureSpec,
        evaluation_result: EvaluationResult,
    ) -> Optional[ReflectionIssue]:
        """Detects over-provisioned architectures for low complexity tasks."""
        complexity = task_spec.complexity if task_spec else ComplexityLevel.MEDIUM
        agent_count = len(architecture.agents)

        if complexity == ComplexityLevel.LOW and agent_count > 3:
            evidence = f"Task complexity is 'low', but architecture deployed {agent_count} agents with cost efficiency {evaluation_result.metrics.cost_efficiency:.2f}."
            return ReflectionIssue(
                category=IssueCategory.REDUNDANT_AGENTS,
                description=f"Excessive agent count ({agent_count} agents) deployed for low-complexity task, causing redundant computation.",
                affected_agent_id=architecture.agents[-1].agent_id if architecture.agents else None,
                severity="medium",
                evidence=evidence,
                affected_component="architecture",
            )
        return None

    def _check_topology(
        self, task_spec: Optional[TaskSpec], architecture: ArchitectureSpec
    ) -> Optional[ReflectionIssue]:
        """Checks for disconnected nodes or improper graph wiring."""
        if len(architecture.agents) <= 1:
            return None

        # In parallel topology, agents run independently without inter-agent connections
        if architecture.topology == TopologyType.PARALLEL:
            return None

        connected_nodes = set()
        for conn in architecture.connections:
            connected_nodes.add(conn.source)
            connected_nodes.add(conn.target)

        all_nodes = {a.agent_id for a in architecture.agents}
        disconnected = all_nodes - connected_nodes

        if disconnected:
            return ReflectionIssue(
                category=IssueCategory.INCORRECT_TOPOLOGY,
                description=f"Agent(s) {disconnected} are disconnected from the communication graph topology.",
                affected_agent_id=next(iter(disconnected)),
                severity="high",
                evidence=f"Nodes {disconnected} have no incoming or outgoing connections.",
                affected_component="topology",
            )
        return None

    def _check_agent_failures(self, execution_result: ExecutionResult) -> List[ReflectionIssue]:
        """Detects execution errors and failure traces localized to specific agents."""
        issues = []
        for trace in execution_result.agent_traces:
            if trace.status == ExecutionStatus.FAILED:
                issues.append(
                    ReflectionIssue(
                        category=IssueCategory.AGENT_REASONING_FAILURE,
                        description=f"Agent '{trace.agent_id}' encountered an execution or reasoning failure: {trace.error_message or 'Unknown failure'}",
                        affected_agent_id=trace.agent_id,
                        severity="high",
                        evidence=f"Trace error: {trace.error_message}",
                        affected_component="agent",
                    )
                )
        return issues

    def _check_dependency_failures(
        self, architecture: ArchitectureSpec, execution_result: ExecutionResult
    ) -> Optional[ReflectionIssue]:
        """Checks if downstream agents lacked required inputs from upstream agents."""
        for error in execution_result.errors:
            if "KeyError" in error or "missing input" in error.lower() or "dependency" in error.lower():
                return ReflectionIssue(
                    category=IssueCategory.DEPENDENCY_FAILURE,
                    description=f"Graph dependency mismatch or missing state key observed during execution: {error}",
                    affected_agent_id=None,
                    severity="high",
                    evidence=error,
                    affected_component="topology",
                )
        return None

    def _check_excessive_iterations(self, execution_result: ExecutionResult) -> Optional[ReflectionIssue]:
        """Checks if execution looped excessively without resolving."""
        if execution_result.iteration_count >= 5:
            return ReflectionIssue(
                category=IssueCategory.EXCESSIVE_ITERATIONS,
                description=f"Architecture completed {execution_result.iteration_count} iterations without early termination.",
                affected_agent_id=None,
                severity="medium",
                evidence=f"iteration_count={execution_result.iteration_count}",
                affected_component="architecture",
            )
        return None

    def _check_insufficient_research(
        self,
        task_spec: Optional[TaskSpec],
        architecture: ArchitectureSpec,
        execution_result: ExecutionResult,
    ) -> Optional[ReflectionIssue]:
        """Detects shallow research output when the task is research-oriented."""
        if task_spec and task_spec.task_type == TaskType.RESEARCH:
            for trace in execution_result.agent_traces:
                if "research" in trace.agent_id.lower() or "research" in (trace.role or "").lower():
                    out_len = len(str(trace.output_data))
                    if out_len < 120 and len(trace.tool_calls) == 0:
                        return ReflectionIssue(
                            category=IssueCategory.INSUFFICIENT_RESEARCH,
                            description=f"Research agent '{trace.agent_id}' produced shallow findings without tool gathering.",
                            affected_agent_id=trace.agent_id,
                            severity="medium",
                            evidence=f"Research output was {out_len} chars with 0 tool calls.",
                            affected_component="agent",
                        )
        return None

    def analyze_failures(self, execution_logs: List[Dict[str, Any]]) -> List[str]:
        """Backward-compatible helper returning string list of error descriptions."""
        return [log.get("error", "Unknown error") for log in execution_logs if "error" in log]
