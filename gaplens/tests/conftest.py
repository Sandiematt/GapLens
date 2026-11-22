import pytest

from core import db, gemini_client
from ui import secrets


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Point the storage layer at a throwaway SQLite file."""
    path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    return path


@pytest.fixture(autouse=True)
def offline_gemini(monkeypatch):
    """No test may reach Gemini or depend on a local key: no key by default, and the
    real SDK client can never be built. Tests that need a key patch these again."""
    def no_network(api_key):
        raise AssertionError("a test tried to create a real Gemini client")

    monkeypatch.setattr(gemini_client, "client_factory", no_network)
    monkeypatch.setattr(secrets, "get_gemini_key", lambda: None)
    monkeypatch.setattr(secrets, "get_gemini_model", lambda: None)
