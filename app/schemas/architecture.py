"""
Shared Pydantic Schemas for Architecture Synthesis & Agent Configuration.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TopologyType(str, Enum):
    PIPELINE = "pipeline"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    # Future topologies (Post Mid-Sem)
    DEBATE = "debate"
    TREE = "tree"
    BLACKBOARD = "blackboard"


class AgentConfigSchema(BaseModel):
    agent_id: str = Field(..., description="Unique agent identifier in the graph, e.g. research_agent")
    name: str = Field(..., description="Human-readable name of the agent")
    role: str = Field(..., description="Role specification, e.g. Web Researcher")
    objective: str = Field(..., description="Primary objective or instructions for this agent")
    system_prompt: str = Field(..., description="Customized system prompt generated for this agent")
    tools: List[str] = Field(default_factory=list, description="List of tool names assigned to this agent")
    input_keys: List[str] = Field(default_factory=list, description="Keys expected in the input state")
    output_keys: List[str] = Field(default_factory=list, description="Keys written to the state")
    constraints: List[str] = Field(default_factory=list, description="Agent-specific execution constraints")


class Connection(BaseModel):
    source: str = Field(..., description="Source agent ID")
    target: str = Field(..., description="Target agent ID")
    condition: Optional[str] = Field(default=None, description="Optional conditional route criteria")


class ArchitectureSpec(BaseModel):
    architecture_id: str = Field(..., description="Unique architecture specification ID")
    task_id: str = Field(..., description="ID of the task this architecture was synthesized for")
    topology: TopologyType = Field(default=TopologyType.PIPELINE, description="Graph communication topology")
    agents: List[AgentConfigSchema] = Field(default_factory=list, description="Dynamic agents composition")
    connections: List[Connection] = Field(default_factory=list, description="Agent dependency edges")
    meta_reasoning: Optional[str] = Field(
        default=None, description="Explanation of why this architecture was synthesized"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "architecture_id": "arch_001",
                "task_id": "task_001",
                "topology": "pipeline",
                "agents": [
                    {
                        "agent_id": "research_agent",
                        "name": "Research Agent",
                        "role": "Information Researcher",
                        "objective": "Gather domain information",
                        "system_prompt": "You are a research agent...",
                        "tools": ["web_search"],
                        "input_keys": ["task_prompt"],
                        "output_keys": ["raw_research"],
                        "constraints": []
                    }
                ],
                "connections": [
                    {"source": "research_agent", "target": "analysis_agent"}
                ],
                "meta_reasoning": "Synthesized 3-agent pipeline for linear research and analysis workflow"
            }
        }
