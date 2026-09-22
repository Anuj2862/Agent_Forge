"""
Shared Pydantic Schemas for Architecture Reflection & Evolution Recommendations.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class IssueCategory(str, Enum):
    INSUFFICIENT_VERIFICATION = "insufficient_verification"
    POOR_DECOMPOSITION = "poor_decomposition"
    MISSING_TOOL = "missing_tool"
    INCORRECT_TOPOLOGY = "incorrect_topology"
    AGENT_REASONING_FAILURE = "agent_reasoning_failure"
    REDUNDANT_AGENTS = "redundant_agents"
    # Extended architectural root causes
    INCORRECT_AGENT_SELECTION = "incorrect_agent_selection"
    INSUFFICIENT_RESEARCH = "insufficient_research"
    EXECUTION_FAILURE = "execution_failure"
    DEPENDENCY_FAILURE = "dependency_failure"
    EXCESSIVE_ITERATIONS = "excessive_iterations"
    INCOMPLETE_TASK_COVERAGE = "incomplete_task_coverage"


class ReflectionIssue(BaseModel):
    category: IssueCategory = Field(..., description="Categorized architecture issue")
    description: str = Field(..., description="Detailed description of identified vulnerability or gap")
    affected_agent_id: Optional[str] = Field(default=None, description="Specific agent ID if issue is localized")
    severity: str = Field(default="medium", description="Severity level: low, medium, high, critical")
    evidence: Optional[str] = Field(default=None, description="Concrete evidence observed in execution trace or output")
    affected_component: str = Field(default="architecture", description="Affected component or layer (architecture, agent, tools, topology)")


class ArchitecturalRecommendation(BaseModel):
    action: str = Field(..., description="Recommended modification action (e.g. ADD_AGENT, REMOVE_AGENT, ADD_TOOL, CHANGE_TOPOLOGY)")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Structural payload (e.g. {'role': 'Verification Agent', 'insert_after': 'research_agent'})"
    )
    priority: str = Field(default="high", description="Priority level: low, medium, high")
    reason: Optional[str] = Field(default=None, description="Rationale for why this recommendation is being made")
    expected_benefit: Optional[str] = Field(default=None, description="Anticipated benefit or metric gain")


class ReflectionResult(BaseModel):
    reflection_id: str = Field(..., description="Unique reflection identifier")
    task_id: str = Field(..., description="Target task ID")
    architecture_id: str = Field(..., description="Evaluated architecture ID")
    identified_issues: List[ReflectionIssue] = Field(default_factory=list, description="List of detected gaps")
    recommendations: List[ArchitecturalRecommendation] = Field(
        default_factory=list, description="Targeted evolution recommendations"
    )
    reflection_summary: str = Field(..., description="High-level synthesis of reflection findings")

    class Config:
        json_schema_extra = {
            "example": {
                "reflection_id": "refl_001",
                "task_id": "task_001",
                "architecture_id": "arch_001",
                "identified_issues": [
                    {
                        "category": "insufficient_verification",
                        "description": "Output lacked cross-reference verification agent step",
                        "severity": "high",
                        "evidence": "Final report contained unverified claims without validation trace",
                        "affected_component": "architecture"
                    }
                ],
                "recommendations": [
                    {
                        "action": "ADD_AGENT",
                        "details": {
                            "role": "Verification Agent",
                            "position": "between analysis and writer",
                            "tools": ["web_search", "document_retriever"]
                        },
                        "priority": "high",
                        "reason": "Missing independent verification stage resulted in low accuracy score",
                        "expected_benefit": "Significantly higher accuracy and verified output claims"
                    }
                ],
                "reflection_summary": "Initial 3-agent pipeline had no verification stage. Recommend adding Verification Agent."
            }
        }
