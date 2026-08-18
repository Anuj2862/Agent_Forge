"""
Agent Configuration Helpers (Owned by Member 2).
"""

from app.schemas.architecture import AgentConfigSchema


def build_default_agent_config(agent_id: str, role: str) -> AgentConfigSchema:
    return AgentConfigSchema(
        agent_id=agent_id,
        name=role,
        role=role,
        objective=f"Perform tasks for {role}",
        system_prompt=f"You are {role}.",
        tools=[],
        input_keys=[],
        output_keys=[],
    )
