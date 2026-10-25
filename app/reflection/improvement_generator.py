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

            domain_hint = "general"
            if architecture and architecture.agents:
                all_text = " ".join(
                    f"{a.role} {a.objective} {a.agent_id}" for a in architecture.agents
                ).lower()
                if any(w in all_text for w in ["code", "python", "script", "program", "developer"]):
                    domain_hint = "code"
                elif any(w in all_text for w in ["data", "sales", "metric", "financial", "numerical"]):
                    domain_hint = "data"

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

            if domain_hint == "code":
                agent_name = "Code Integrity Verification Specialist"
                agent_role = "Code Verification Specialist"
                agent_obj = "Audit generated source code, verify edge case handling, and validate execution requirements."
                system_prompt = (
                    "You are a rigorous Code Verification Specialist. Scrutinize all incoming code artifacts, "
                    "check syntax and algorithm correctness, identify potential runtime regressions, "
                    "and ensure adherence to operational specifications before passing output downstream."
                )
            elif domain_hint == "data":
                agent_name = "Quantitative Integrity Verification Specialist"
                agent_role = "Data Verification Specialist"
                agent_obj = "Cross-examine numerical data, check statistical consistency, and ensure verified computations."
                system_prompt = (
                    "You are a Quantitative Data Verification Specialist. Verify all statistical claims, "
                    "cross-check numerical calculations against raw inputs, eliminate contradictory numbers, "
                    "and certify data integrity."
                )
            else:
                agent_name = "Fact Verification Specialist"
                agent_role = "Factual Verification Specialist"
                agent_obj = "Cross-reference claims against gathered research data, verify factual assertions, and eliminate contradictions."
                system_prompt = (
                    "You are a rigorous Fact Verification Agent. Inspect incoming findings, "
                    "validate claims with source evidence, mark verified assertions, and filter unsupported claims."
                )

            return ArchitecturalRecommendation(
                action="ADD_AGENT",
                details={
                    "agent_id": "fact_verification_agent",
                    "name": agent_name,
                    "role": agent_role,
                    "objective": agent_obj,
                    "system_prompt": system_prompt,
                    "tools": ["web_search"],
                    "input_keys": ["raw_research"],
                    "output_keys": ["verified_findings"],
                    "constraints": ["Do not let unverified assertions pass to final report"],
                    "insert_after": insert_after or "research_agent",
                    "insert_before": insert_before or "writer_agent",
                },
                priority="high",
                reason=f"Absence of independent verification stage caused unverified claims. Synthesizing specialized {agent_role} to ensure grounded outputs.",
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
            specialist_role = "Deep Domain Analyst"
            specialist_name = "Analysis Specialist Agent"
            desc_lower = issue.description.lower()
            if "market" in desc_lower or "industry" in desc_lower:
                specialist_role = "Market Intelligence Specialist"
                specialist_name = "Market Intelligence Agent"
            elif "security" in desc_lower or "vulnerability" in desc_lower:
                specialist_role = "Security Audit Specialist"
                specialist_name = "Security Audit Agent"

            return ArchitecturalRecommendation(
                action="ADD_AGENT",
                details={
                    "agent_id": "analysis_specialist_agent",
                    "name": specialist_name,
                    "role": specialist_role,
                    "objective": "Perform detailed structured analysis on gathered data to satisfy all subtask requirements.",
                    "system_prompt": (
                        f"You are the {specialist_name}. Examine raw findings in depth, extract key structural insights, "
                        "address specific uncovered task deliverables, and formulate structured analytical findings."
                    ),
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
            existing_agent = None
            if architecture and architecture.agents:
                for a in architecture.agents:
                    if a.agent_id == target_agent:
                        existing_agent = a
                        break

            role_label = existing_agent.role if existing_agent else "Specialist Agent"
            mutated_prompt = (
                f"You are an evolved {role_label} operating under elevated reasoning and zero-defect guidelines.\n"
                "Enhanced Execution Protocol: Follow an explicit chain-of-thought scratchpad before emitting output. "
                "Step 1: Parse input requirements and identify implicit assumptions.\n"
                "Step 2: Cross-check intermediate deductions against supplied evidence.\n"
                "Step 3: Self-correct any discrepancies or formatting flaws.\n"
                "Step 4: Emit high-confidence, well-structured final output."
            )

            return ArchitecturalRecommendation(
                action="CHANGE_AGENT_ROLE",
                details={
                    "target_agent_id": target_agent,
                    "updated_system_prompt": mutated_prompt,
                },
                priority="high",
                reason=f"Agent '{target_agent}' failed execution; evolving system prompt with chain-of-thought verification protocol.",
                expected_benefit="Mitigates execution errors through robust step-by-step reasoning prompts and self-correction.",
            )

        return None
