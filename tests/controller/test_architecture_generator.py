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
