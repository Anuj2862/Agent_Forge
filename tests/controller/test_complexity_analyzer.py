import pytest

from app.controller.complexity_analyzer import ComplexityAnalyzer
from app.schemas.task import ComplexityLevel


@pytest.fixture
def analyzer():
    return ComplexityAnalyzer()


def test_simple_task_is_low_complexity(analyzer):
    result = analyzer.assess_complexity(
        "Write a Python function to add two numbers."
    )

    assert result == ComplexityLevel.LOW


def test_data_analysis_task_is_medium_complexity(analyzer):
    result = analyzer.assess_complexity(
        "Analyze a CSV sales dataset and identify "
        "the top 5 products by revenue."
    )

    assert result == ComplexityLevel.MEDIUM


def test_complex_research_task_is_high_complexity(analyzer):
    result = analyzer.assess_complexity(
        "Research recent cybersecurity threats, compare "
        "different attack techniques, analyze their impact, "
        "validate the findings, and produce a detailed report "
        "with recommendations."
    )

    assert result == ComplexityLevel.HIGH


def test_empty_prompt_raises_error(analyzer):
    with pytest.raises(ValueError):
        analyzer.assess_complexity("")
