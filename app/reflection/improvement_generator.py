"""
Improvement Generator Subsystem for Agent Forge.
Translates diagnosed architectural issues into concrete, validated architectural recommendations.
"""

from typing import List, Dict, Any, Optional
from app.schemas.reflection import ArchitecturalRecommendation, ReflectionIssue, IssueCategory
from app.schemas.architecture import ArchitectureSpec
from app.core.logging import logger


class ImprovementGenerator:
    """Generates explicit structural modifications to evolve an ArchitectureSpec."""

    def generate_recommendations(
        self,
        issues: List[ReflectionIssue],
        architecture: Optional[ArchitectureSpec] = None,
    ) -> List[ArchitecturalRecommendation]:
        """
        Maps a list of ReflectionIssue objects into actionable ArchitecturalRecommendation instances.
        """
        recommendations: List[ArchitecturalRecommendation] = []

        for issue in issues:
            rec = self._map_issue_to_recommendation(issue, architecture)
            if rec:
                recommendations.append(rec)
                logger.info(
                    f"[REFLECTION] Recommendation generated: action={rec.action} | priority={rec.priority} | {rec.reason}"
                )

        return recommendations

    def _map_issue_to_recommendation(
        self, issue: ReflectionIssue, architecture: Optional[ArchitectureSpec]
    ) -> Optional[ArchitecturalRecommendation]:
        """Converts an individual issue into a concrete architectural modification."""

        # 1. Missing Verification -> ADD_AGENT (Verification Agent)
        if issue.category == IssueCategory.INSUFFICIENT_VERIFICATION:
            insert_after = None
            insert_before = None

            if architecture and architecture.agents:
                # Place after research or analysis, before writer or aggregator
                agent_ids = [a.agent_id for a in architecture.agents]
                for aid in agent_ids:
                    if any(term in aid.lower() for term in ["research", "gather", "search", "analys"]):
                        insert_after = aid
                for aid in reversed(agent_ids):
                    if any(term in aid.lower() for term in ["write", "report", "summar", "aggreg"]):
                        insert_before = aid

                if not insert_after:
                    insert_after = agent_ids[0]
                if not insert_before and len(agent_ids) > 1:
                    insert_before = agent_ids[-1]

            return ArchitecturalRecommendation(
                action="ADD_AGENT",
                details={
                    "agent_id": "fact_verification_agent",
                    "name": "Fact Verification Agent",
                    "role": "Factual Verification Specialist",
                    "objective": "Cross-reference claims against gathered research data, verify factual assertions, and eliminate contradictions.",
                    "system_prompt": (
                        "You are a rigorous Fact Verification Agent. Inspect incoming findings, "
                        "validate claims with source evidence, mark verified assertions, and filter unsupported claims."
                    ),
                    "tools": ["web_search"],
                    "input_keys": ["raw_research"],
                    "output_keys": ["verified_findings"],
                    "constraints": ["Do not let unverified assertions pass to final report"],
                    "insert_after": insert_after or "research_agent",
                    "insert_before": insert_before or "writer_agent",
                },
                priority="high",
                reason="Absence of independent verification stage caused low accuracy and unverified claims.",
                expected_benefit="Substantially increases accuracy, validates assertions, and ensures verified output.",
            )

        # 2. Missing Tool -> ADD_TOOL
        elif issue.category == IssueCategory.MISSING_TOOL:
            # Extract tool name from description
            tool_name = "web_search"
            if "calculator" in issue.description.lower():
                tool_name = "calculator"
            elif "python_interpreter" in issue.description.lower() or "code" in issue.description.lower():
                tool_name = "python_interpreter"

            target_agent = issue.affected_agent_id
            if not target_agent and architecture and architecture.agents:
                target_agent = architecture.agents[0].agent_id

            return ArchitecturalRecommendation(
                action="ADD_TOOL",
                details={
                    "target_agent_id": target_agent,
                    "tool_name": tool_name,
                },
                priority="high",
                reason=issue.description,
                expected_benefit=f"Empowers agent '{target_agent}' with '{tool_name}' capability to complete required task operations.",
            )

        # 3. Redundant Agents -> REMOVE_AGENT
        elif issue.category == IssueCategory.REDUNDANT_AGENTS:
            target_agent = issue.affected_agent_id
            if not target_agent and architecture and len(architecture.agents) > 1:
                target_agent = architecture.agents[-1].agent_id

            return ArchitecturalRecommendation(
                action="REMOVE_AGENT",
                details={
                    "target_agent_id": target_agent,
                },
                priority="medium",
                reason="Pruning redundant agent from low-complexity task pipeline.",
                expected_benefit="Reduces latency and resource cost while maintaining output quality.",
            )

        # 4. Incorrect Topology -> ADD_CONNECTION or REWIRE
        elif issue.category == IssueCategory.INCORRECT_TOPOLOGY:
            disconnected_agent = issue.affected_agent_id
            source_agent = None
            if architecture and architecture.agents:
                for a in architecture.agents:
                    if a.agent_id != disconnected_agent:
                        source_agent = a.agent_id
                        break

            return ArchitecturalRecommendation(
                action="ADD_CONNECTION",
                details={
                    "source": source_agent or "agent_0",
                    "target": disconnected_agent or "agent_1",
                },
                priority="high",
                reason="Reconnecting isolated agent into communication graph topology.",
                expected_benefit="Ensures end-to-end data flow and message propagation across all agents.",
            )

        # 5. Incomplete Task Coverage -> ADD_AGENT (Specialist Agent)
        elif issue.category == IssueCategory.INCOMPLETE_TASK_COVERAGE:
            return ArchitecturalRecommendation(
                action="ADD_AGENT",
                details={
                    "agent_id": "analysis_specialist_agent",
                    "name": "Analysis Specialist Agent",
                    "role": "Deep Domain Analyst",
                    "objective": "Perform detailed structured analysis on gathered data to satisfy all subtask requirements.",
                    "system_prompt": "You are a Domain Analyst. Examine raw data, extract insights, and format structured analytical findings.",
                    "tools": [],
                    "input_keys": ["raw_research"],
                    "output_keys": ["analysis_data"],
                    "constraints": [],
                    "insert_after": architecture.agents[0].agent_id if architecture and architecture.agents else None,
                },
                priority="high",
                reason="Subtasks lacked specialized coverage in current architecture.",
                expected_benefit="Fulfills missing subtasks, raising overall task completeness score.",
            )

        # 6. Insufficient Research -> ADD_TOOL to Research Agent
        elif issue.category == IssueCategory.INSUFFICIENT_RESEARCH:
            target_agent = issue.affected_agent_id or "research_agent"
            return ArchitecturalRecommendation(
                action="ADD_TOOL",
                details={
                    "target_agent_id": target_agent,
                    "tool_name": "web_search",
                },
                priority="medium",
                reason="Research agent produced shallow findings due to lack of web search tooling.",
                expected_benefit="Enables research agent to fetch comprehensive real-time external data.",
            )

        # 7. Agent Reasoning Failure -> REPLACE_AGENT
        elif issue.category == IssueCategory.AGENT_REASONING_FAILURE:
            target_agent = issue.affected_agent_id
            return ArchitecturalRecommendation(
                action="CHANGE_AGENT_ROLE",
                details={
                    "target_agent_id": target_agent,
                    "updated_system_prompt": "Follow step-by-step chain of thought. Double-check all intermediate steps before producing output.",
                },
                priority="high",
                reason=f"Agent '{target_agent}' failed execution; upgrading prompts and constraints.",
                expected_benefit="Mitigates execution errors through robust step-by-step reasoning prompts.",
            )

        return None
