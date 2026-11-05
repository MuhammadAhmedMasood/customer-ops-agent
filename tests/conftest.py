"""Shared pytest fixtures. pytest finds this file automatically."""

import pytest
from fastapi.testclient import TestClient

from app.api.webhook import webhook_limiter
from app.db import database
from app.main import app
from data.seed import seed


@pytest.fixture(autouse=True)
def reset_rate_limit():
    """Every test starts with an empty rate-limit history."""
    webhook_limiter.hits.clear()


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client for the API, backed by a fresh database in a temp folder."""
    db_path = tmp_path / "test.db"
    seed(db_path)
    monkeypatch.setattr(database, "DB_PATH", db_path)  # undone after each test
    return TestClient(app)
