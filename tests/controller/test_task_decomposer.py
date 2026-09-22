import json

from app.controller.task_decomposer import TaskDecomposer


class FakeResponse:
    def __init__(self, data):
        self.text = json.dumps(data)


def test_task_decomposer_returns_valid_subtasks():
    decomposer = TaskDecomposer.__new__(TaskDecomposer)

    fake_result = {
        "subtasks": [
            {
                "id": "subtask_1",
                "title": "Collect data",
                "description": "Collect the required input data.",
                "required_capabilities": [
                    "data_collection"
                ],
            },
            {
                "id": "subtask_2",
                "title": "Analyze data",
                "description": "Analyze the collected data.",
                "required_capabilities": [
                    "data_analysis"
                ],
            },
        ]
    }

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse(fake_result)

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    decomposer.client = FakeClient()
    decomposer.model = "test-model"

    result = decomposer.decompose(
        "Collect data and analyze it."
    )

    assert len(result) == 2

    assert result[0].id == "subtask_1"
    assert result[0].title == "Collect data"
    assert "data_collection" in result[0].required_capabilities

    assert result[1].id == "subtask_2"
    assert result[1].title == "Analyze data"
    assert "data_analysis" in result[1].required_capabilities
