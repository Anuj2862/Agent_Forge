"""
Unit Tests for ArchitectureModifier and Graph Safety Validation.
"""

from app.reflection.architecture_modifier import ArchitectureModifier
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType, Connection
from app.schemas.reflection import ReflectionResult, ArchitecturalRecommendation
from tests.fixtures.mock_scenarios import get_run1_architecture


def test_modifier_add_agent_rewires_pipeline():
    modifier = ArchitectureModifier()
    base_arch = get_run1_architecture()
    assert len(base_arch.agents) == 2
    assert len(base_arch.connections) == 1
    assert base_arch.connections[0].source == "research_agent"
    assert base_arch.connections[0].target == "writer_agent"

    rec = ArchitecturalRecommendation(
        action="ADD_AGENT",
        details={
            "agent_id": "fact_verification_agent",
            "name": "Fact Verification Agent",
            "role": "Factual Verification Specialist",
            "objective": "Verify claims",
            "system_prompt": "You verify claims.",
            "tools": ["web_search"],
            "insert_after": "research_agent",
            "insert_before": "writer_agent",
        },
        priority="high",
    )
    reflection = ReflectionResult(
        reflection_id="refl_test",
        task_id=base_arch.task_id,
        architecture_id=base_arch.architecture_id,
        recommendations=[rec],
        reflection_summary="Add verification stage",
    )

    mutated = modifier.mutate_architecture(base_arch, reflection)

    assert isinstance(mutated, ArchitectureSpec)
    assert len(mutated.agents) == 3
    agent_ids = [a.agent_id for a in mutated.agents]
    assert "fact_verification_agent" in agent_ids

    # Check that direct edge was replaced with 2 edges:
    # research_agent -> fact_verification_agent and fact_verification_agent -> writer_agent
    conn_pairs = [(c.source, c.target) for c in mutated.connections]
    assert ("research_agent", "fact_verification_agent") in conn_pairs
    assert ("fact_verification_agent", "writer_agent") in conn_pairs
    assert ("research_agent", "writer_agent") not in conn_pairs


def test_modifier_remove_agent_restitches_edges():
    modifier = ArchitectureModifier()
    # Create 3-agent pipeline: A -> B -> C
    agents = [
        AgentConfigSchema(agent_id="a", name="A", role="Role A", objective="Obj A", system_prompt="Sys A", tools=[]),
        AgentConfigSchema(agent_id="b", name="B", role="Role B", objective="Obj B", system_prompt="Sys B", tools=[]),
        AgentConfigSchema(agent_id="c", name="C", role="Role C", objective="Obj C", system_prompt="Sys C", tools=[]),
    ]
    conns = [
        Connection(source="a", target="b"),
        Connection(source="b", target="c"),
    ]
    arch = ArchitectureSpec(
        architecture_id="arch_3",
        task_id="task_1",
        agents=agents,
        connections=conns,
    )

    rec = ArchitecturalRecommendation(
        action="REMOVE_AGENT",
        details={"target_agent_id": "b"},
        priority="high",
    )
    reflection = ReflectionResult(
        reflection_id="refl_rm",
        task_id="task_1",
        architecture_id="arch_3",
        recommendations=[rec],
        reflection_summary="Remove B",
    )

    mutated = modifier.mutate_architecture(arch, reflection)

    assert len(mutated.agents) == 2
    agent_ids = [a.agent_id for a in mutated.agents]
    assert "b" not in agent_ids
    # Check that edge A -> C was formed
    conn_pairs = [(c.source, c.target) for c in mutated.connections]
    assert ("a", "c") in conn_pairs
    assert not any("b" in pair for pair in conn_pairs)


def test_modifier_add_tool():
    modifier = ArchitectureModifier()
    base_arch = get_run1_architecture()

    rec = ArchitecturalRecommendation(
        action="ADD_TOOL",
        details={"target_agent_id": "writer_agent", "tool_name": "markdown_formatter"},
        priority="high",
    )
    reflection = ReflectionResult(
        reflection_id="refl_tool",
        task_id=base_arch.task_id,
        architecture_id=base_arch.architecture_id,
        recommendations=[rec],
        reflection_summary="Add formatting tool",
    )

    mutated = modifier.mutate_architecture(base_arch, reflection)
    writer = next(a for a in mutated.agents if a.agent_id == "writer_agent")
    assert "markdown_formatter" in writer.tools


def test_modifier_refuses_to_remove_last_agent():
    modifier = ArchitectureModifier()
    single_agent = AgentConfigSchema(
        agent_id="sole_agent", name="Sole", role="Solo", objective="Solo", system_prompt="Solo", tools=[]
    )
    arch = ArchitectureSpec(
        architecture_id="arch_single",
        task_id="task_1",
        agents=[single_agent],
        connections=[],
    )
    rec = ArchitecturalRecommendation(
        action="REMOVE_AGENT",
        details={"target_agent_id": "sole_agent"},
        priority="high",
    )
    reflection = ReflectionResult(
        reflection_id="refl_rm_all",
        task_id="task_1",
        architecture_id="arch_single",
        recommendations=[rec],
        reflection_summary="Attempt to delete sole agent",
    )

    mutated = modifier.mutate_architecture(arch, reflection)
    # Must refuse and keep the agent intact
    assert len(mutated.agents) == 1
    assert mutated.agents[0].agent_id == "sole_agent"


def test_modifier_handles_duplicate_agent_id_gracefully():
    modifier = ArchitectureModifier()
    base_arch = get_run1_architecture()

    # Attempt to add agent with an ID that already exists
    rec = ArchitecturalRecommendation(
        action="ADD_AGENT",
        details={
            "agent_id": "research_agent",  # duplicate!
            "name": "Another Researcher",
            "role": "Secondary Researcher",
            "objective": "Extra research",
            "system_prompt": "Extra research",
            "tools": [],
        },
        priority="high",
    )
    reflection = ReflectionResult(
        reflection_id="refl_dup",
        task_id=base_arch.task_id,
        architecture_id=base_arch.architecture_id,
        recommendations=[rec],
        reflection_summary="Duplicate ID",
    )

    mutated = modifier.mutate_architecture(base_arch, reflection)
    # Should resolve uniqueness or keep valid
    agent_ids = [a.agent_id for a in mutated.agents]
    assert len(agent_ids) == len(set(agent_ids))
