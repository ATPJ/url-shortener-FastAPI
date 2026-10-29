import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import get_settings

TEST_DATABASE_URL = f"{get_settings().DATABASE_URL}_test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
get_settings.cache_clear()


from app.database import engine
from app.main import app


@pytest.fixture(autouse=True)
def clean_db() -> None:
    assert engine.url.database.endswith("_test")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE links RESTART IDENTITY"))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, follow_redirects=False)
