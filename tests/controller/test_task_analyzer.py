import json

from app.controller.task_analyzer import TaskAnalyzer


class FakeResponse:
    def __init__(self, data):
        self.text = json.dumps(data)


def test_task_analyzer_returns_valid_task_spec(monkeypatch):
    analyzer = TaskAnalyzer.__new__(TaskAnalyzer)

    fake_result = {
        "task_type": "data_analysis",
        "complexity": "medium",
        "subtasks": [
            {
                "id": "1",
                "title": "Analyze data",
                "description": "Analyze the provided dataset.",
                "required_capabilities": [
                    "data_analysis"
                ],
            }
        ],
        "required_capabilities": [
            "data_analysis"
        ],
        "constraints": [
            "Use the provided dataset."
        ],
        "expected_output_format": "table",
    }

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse(fake_result)

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    analyzer.client = FakeClient()
    analyzer.model = "test-model"

    result = analyzer.analyze(
        "Analyze the provided dataset and return the results as a table."
    )

    assert result.user_prompt == (
        "Analyze the provided dataset and return the results as a table."
    )

    assert result.task_type == "data_analysis"
    assert result.complexity == "medium"
    assert len(result.subtasks) == 1
    assert result.subtasks[0].title == "Analyze data"
    assert "data_analysis" in result.required_capabilities
    assert result.expected_output_format == "table"
