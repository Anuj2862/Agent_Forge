import os
import pytest
import asyncio
from app.core.config import settings
from app.memory.database import init_db


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Ensure test environment has mock credentials configured for offline unit testing."""
    if not settings.GEMINI_API_KEY:
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-api-key")


@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    """Ensure database schema is created before tests execute."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                ex.submit(asyncio.run, init_db()).result()
        else:
            loop.run_until_complete(init_db())
    except RuntimeError:
        asyncio.run(init_db())
