from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine


def create_link(client: TestClient, url: str = "https://example.com") -> dict[str, Any]:
    response = client.post("/links", json={"url": url})
    assert response.status_code == 201
    return response.json()


def expire_link(code: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE links SET expires_at = now() - interval '1 day' "
                "WHERE short_code = :code"
            ),
            {"code": code},
        )


def test_create_link(client: TestClient) -> None:
    response = client.post("/links", json={"url": "https://example.com"})
    assert response.status_code == 201
    data = response.json()
    assert len(data["short_code"]) == 8
    assert data["short_url"].endswith(data["short_code"])
    assert data["original_url"] == "https://example.com/"


@pytest.mark.parametrize(
    "bad_url",
    ["not-a-url", "ftp://example.com", "", "https://example.com/" + "a" * 2100],
)
def test_create_link_invalid_url(client: TestClient, bad_url: str) -> None:
    response = client.post("/links", json={"url": bad_url})
    assert response.status_code == 422


def test_redirect(client: TestClient) -> None:
    code = create_link(client)["short_code"]
    response = client.get(f"/{code}")
    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/"


def test_click_count_increments(client: TestClient) -> None:
    code = create_link(client)["short_code"]
    for _ in range(3):
        client.get(f"/{code}")
    response = client.get(f"/analytics/{code}")
    assert response.status_code == 200
    assert response.json()["click_count"] == 3


def test_unknown_code(client: TestClient) -> None:
    assert client.get("/nope1234").status_code == 404
    assert client.get("/analytics/nope1234").status_code == 404


def test_expired_link(client: TestClient) -> None:
    code = create_link(client)["short_code"]
    expire_link(code)
    assert client.get(f"/{code}").status_code == 410
    response = client.get(f"/analytics/{code}")
    assert response.status_code == 200
    assert response.json()["click_count"] == 0


def test_health(client: TestClient) -> None:
    assert client.get("/health").status_code == 200


def test_short_code_collision_is_retried(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = create_link(client)["short_code"]
    codes = iter([first, first, "ZZZZZZZZ"])
    monkeypatch.setattr("app.services.links.generate_short_code", lambda: next(codes))
    second = create_link(client)
    assert second["short_code"] == "ZZZZZZZZ"


def test_503_when_all_retries_collide(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = create_link(client)["short_code"]
    monkeypatch.setattr("app.services.links.generate_short_code", lambda: first)
    response = client.post("/links", json={"url": "https://example.org"})
    assert response.status_code == 503
