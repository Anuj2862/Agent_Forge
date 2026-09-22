import os
import pytest
from app.core.config import settings


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Ensure test environment has mock credentials configured for offline unit testing."""
    if not settings.GEMINI_API_KEY:
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-api-key")
