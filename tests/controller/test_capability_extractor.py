import json

from app.controller.capability_extractor import CapabilityExtractor


class FakeResponse:
    def __init__(self, data):
        self.text = json.dumps(data)


def test_capability_extractor_returns_unique_capabilities():
    extractor = CapabilityExtractor.__new__(CapabilityExtractor)

    fake_result = {
        "capabilities": [
            "csv_parsing",
            "data_analysis",
            "data_analysis",
            "table_generation",
        ]
    }

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse(fake_result)

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    extractor.client = FakeClient()
    extractor.model = "test-model"

    result = extractor.extract_capabilities(
        "Analyze a CSV and generate a table."
    )

    assert result == [
        "csv_parsing",
        "data_analysis",
        "table_generation",
    ]

    assert len(result) == len(set(result))
