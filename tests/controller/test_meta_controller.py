import pytest

from app.controller.meta_controller import MetaController
from app.schemas.architecture import (
    ArchitectureSpec,
    TopologyType,
)
from app.schemas.task import (
    ComplexityLevel,
    Subtask,
    TaskSpec,
    TaskType,
)


@pytest.mark.asyncio
async def test_meta_controller_orchestrates_components(monkeypatch):
    controller = MetaController()

    task_spec = TaskSpec(
        task_id="task_001",
        user_prompt="Analyze sales data and produce a report.",
        task_type=TaskType.DATA_ANALYSIS,
        complexity=ComplexityLevel.LOW,
        subtasks=[],
        required_capabilities=[],
        constraints=["Use the provided dataset."],
        expected_output_format="report",
    )

    subtasks = [
        Subtask(
            id="subtask_1",
            title="Analyze Sales",
            description="Analyze the sales data.",
            required_capabilities=["data_analysis"],
        ),
        Subtask(
            id="subtask_2",
            title="Create Report",
            description="Create a report from the analysis.",
            required_capabilities=["report_generation"],
        ),
    ]

    expected_architecture = ArchitectureSpec(
        architecture_id="architecture_test",
        task_id="task_001",
        topology=TopologyType.PIPELINE,
        agents=[],
        connections=[],
        meta_reasoning="Mock architecture",
    )

    calls = []

    def fake_analyze(prompt):
        calls.append("analyze")
        return task_spec

    def fake_decompose(prompt):
        calls.append("decompose")
        return subtasks

    def fake_extract(prompt):
        calls.append("capabilities")
        return ["data_analysis", "report_generation"]

    def fake_complexity(prompt):
        calls.append("complexity")
        return ComplexityLevel.MEDIUM

    def fake_generate(received_task_spec):
        calls.append("architecture")

        assert received_task_spec.subtasks == subtasks
        assert received_task_spec.required_capabilities == [
            "data_analysis",
            "report_generation",
        ]
        assert received_task_spec.complexity == ComplexityLevel.MEDIUM

        return expected_architecture

    monkeypatch.setattr(
        controller.task_analyzer,
        "analyze",
        fake_analyze,
    )

    monkeypatch.setattr(
        controller.task_decomposer,
        "decompose",
        fake_decompose,
    )

    monkeypatch.setattr(
        controller.capability_extractor,
        "extract_capabilities",
        fake_extract,
    )

    monkeypatch.setattr(
        controller.complexity_analyzer,
        "assess_complexity",
        fake_complexity,
    )

    monkeypatch.setattr(
        controller.architecture_generator,
        "generate_architecture",
        fake_generate,
    )

    result = await controller.process_task(
        "Analyze sales data and produce a report."
    )

    assert result == expected_architecture

    assert calls == [
        "analyze",
        "decompose",
        "capabilities",
        "complexity",
        "architecture",
    ]


@pytest.mark.asyncio
async def test_meta_controller_rejects_empty_prompt():
    controller = MetaController()

    with pytest.raises(ValueError):
        await controller.process_task("")
