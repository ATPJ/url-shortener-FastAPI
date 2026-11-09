import os

from pathlib import Path

import pytest

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import get_settings


ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"
TEST_DATABASE_URL = f"{get_settings().DATABASE_URL}_test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
get_settings.cache_clear()

from app.database import engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    cfg = Config(str(ALEMBIC_INI))
    command.upgrade(cfg, "head")

@pytest.fixture(autouse=True)
def clean_db() -> None:
    assert engine.url.database.endswith("_test")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE links RESTART IDENTITY"))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, follow_redirects=False)
