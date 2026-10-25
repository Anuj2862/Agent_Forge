import pytest

from app.controller.architecture_generator import ArchitectureGenerator
from app.schemas.task import (
    TaskSpec,
    Subtask,
    TaskType,
    ComplexityLevel,
)
from app.schemas.architecture import TopologyType


@pytest.fixture
def generator():
    return ArchitectureGenerator()


def create_task_spec(
    task_type=TaskType.DATA_ANALYSIS,
    subtasks=None,
):
    if subtasks is None:
        subtasks = [
            Subtask(
                id="subtask_1",
                title="Load Data",
                description="Load the input dataset.",
                required_capabilities=["data_loading"],
            ),
            Subtask(
                id="subtask_2",
                title="Analyze Data",
                description="Analyze the dataset.",
                required_capabilities=["data_analysis"],
            ),
            Subtask(
                id="subtask_3",
                title="Format Results",
                description="Format the analysis results.",
                required_capabilities=["table_generation"],
            ),
        ]

    return TaskSpec(
        task_id="test_task_001",
        user_prompt="Analyze the dataset and produce results.",
        task_type=task_type,
        complexity=ComplexityLevel.MEDIUM,
        subtasks=subtasks,
        required_capabilities=["data_analysis"],
        constraints=["Use the provided dataset."],
        expected_output_format="table",
    )


def test_generates_valid_architecture(generator):
    task_spec = create_task_spec()

    architecture = generator.generate_architecture(task_spec)

    assert architecture.task_id == task_spec.task_id
    assert architecture.architecture_id.startswith("architecture_")
    assert len(architecture.agents) == len(task_spec.subtasks)


def test_data_analysis_uses_parallel_topology(generator):
    task_spec = create_task_spec(
        task_type=TaskType.DATA_ANALYSIS
    )

    architecture = generator.generate_architecture(task_spec)

    assert architecture.topology == TopologyType.PARALLEL
    assert architecture.connections == []


def test_pipeline_creates_sequential_connections(generator):
    task_spec = create_task_spec(
        task_type=TaskType.CODE_GENERATION
    )

    architecture = generator.generate_architecture(task_spec)

    assert architecture.topology == TopologyType.PIPELINE
    assert len(architecture.connections) == len(task_spec.subtasks) - 1

    assert architecture.connections[0].source == "subtask_1"
    assert architecture.connections[0].target == "subtask_2"

    assert architecture.connections[1].source == "subtask_2"
    assert architecture.connections[1].target == "subtask_3"


def test_agents_preserve_subtask_information(generator):
    task_spec = create_task_spec()

    architecture = generator.generate_architecture(task_spec)

    for agent, subtask in zip(architecture.agents, task_spec.subtasks):
        assert agent.agent_id == subtask.id
        assert agent.role == subtask.title
        assert agent.objective == subtask.description
        assert agent.tools == subtask.required_capabilities


def test_empty_subtasks_raise_error(generator):
    task_spec = create_task_spec(subtasks=[])

    with pytest.raises(ValueError):
        generator.generate_architecture(task_spec)


def test_hybrid_dag_fan_in_topology_synthesis(generator):
    """3 subtasks with final synthesis should produce a HYBRID DAG with fan-in connections."""
    task_spec = TaskSpec(
        task_id="task_hybrid_test",
        user_prompt="Gather market data and synthesize recommendations",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.HIGH,
        subtasks=[
            Subtask(id="st_1", title="Market Search A", description="Scrape segment A", required_capabilities=["web_search"]),
            Subtask(id="st_2", title="Market Search B", description="Scrape segment B", required_capabilities=["web_search"]),
            Subtask(id="st_3", title="Synthesize Executive Report", description="Aggregate and summarize", required_capabilities=[]),
        ],
    )
    arch = generator.generate_architecture(task_spec)
    assert arch.topology == TopologyType.HYBRID
    # Fan-in: st_1 -> st_3, st_2 -> st_3
    assert len(arch.connections) == 2
    sources = {c.source for c in arch.connections}
    targets = {c.target for c in arch.connections}
    assert sources == {"st_1", "st_2"}
    assert targets == {"st_3"}
    assert "Hybrid DAG Fan-In" in arch.meta_reasoning


def test_architecture_incorporates_memory_topology(generator):
    """Historical memory with high success rating should influence topology selection."""
    task_spec = TaskSpec(
        task_id="task_mem_test",
        user_prompt="Run deep audit",
        task_type=TaskType.GENERAL,
        complexity=ComplexityLevel.MEDIUM,
        subtasks=[
            Subtask(id="a", title="Part A", description="Desc", required_capabilities=[]),
            Subtask(id="b", title="Part B", description="Desc", required_capabilities=[]),
        ],
        metadata={
            "retrieved_memories": [
                {"record_id": "m1", "success_rating": 0.95, "topology": "parallel"}
            ]
        },
    )
    arch = generator.generate_architecture(task_spec)
    assert arch.topology == TopologyType.PARALLEL
    assert "Informed by 1 prior high-success evolutionary run(s)" in arch.meta_reasoning
