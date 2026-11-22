import pytest

from core import db


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Point the storage layer at a throwaway SQLite file."""
    path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    return path
