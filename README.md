# URL Shortener

A small URL shortener API: create a short link, get redirected, count clicks, and let links expire. Built as a learning/portfolio project to practice a clean Python backend: FastAPI, PostgreSQL, SQLAlchemy, Docker Compose and pytest.

## Features

- Create a short link (random 8-character code)
- Redirect to the original URL (`302`) and count every click
- Link expiration with a configurable TTL
- Per-link analytics (click count, created/expires dates)
- Input validation, clear status codes (`404`, `410`, `422`, `503`)
- Automated tests running against a real PostgreSQL database

## Tech stack

FastAPI · PostgreSQL 16 · SQLAlchemy 2.x (sync, psycopg 3) · Pydantic / pydantic-settings · Docker Compose · pytest · uv · ruff

## Quick start

```bash
cp .env.example .env      # then fill in the values
docker compose up --build
```

The API is available at http://localhost:8000.

You can try every endpoint without `curl`: open the interactive docs at http://localhost:8000/docs (Swagger UI), pick an endpoint, click **Try it out** and **Execute**.

## Configuration

All settings come from environment variables (`.env`).

| Variable | Description |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Credentials and name of the PostgreSQL database |
| `DATABASE_URL` | Used for local runs and tests (`postgresql+psycopg://USER:PASS@127.0.0.1:5432/DB`). Inside Docker Compose the host is overridden to `db` |
| `LINK_TTL_DAYS` | How many days a link stays valid |
| `BASE_URL` | Base address used to build the `short_url` in responses |

## API

| Method | Path | Success | Errors |
|---|---|---|---|
| `POST` | `/links` | `201` with the new link | `422` invalid URL, `503` no unique code could be generated |
| `GET` | `/{code}` | `302` redirect to the original URL | `404` unknown code, `410` link expired |
| `GET` | `/analytics/{code}` | `200` with link statistics | `404` unknown code |
| `GET` | `/health` | `200` | `503` database unavailable |

> **Tip:** all endpoints can be tested from the interactive docs at `/docs`. The only exception is the redirect (`GET /{code}`): Swagger UI follows redirects automatically, so to see the redirect, open `http://localhost:8000/<code>` in the browser address bar (or use `curl -i`).

Example with `curl`:

```bash
curl -X POST http://localhost:8000/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

Response (shape):

```json
{
  "short_code": "aB3dE5gH",
  "short_url": "http://localhost:8000/aB3dE5gH",
  "original_url": "https://example.com/",
  "expires_at": "..."
}
```

Note: Pydantic normalizes URLs, so `https://example.com` is stored as `https://example.com/`.

## Running tests

Tests need a running PostgreSQL and a separate database named `<POSTGRES_DB>_test` (they truncate the `links` table, so they never touch the development database).

```bash
docker compose up -d db
docker compose exec db createdb -U <POSTGRES_USER> <POSTGRES_DB>_test
uv sync
uv run pytest -v
```

## Design decisions

- **`302`, not `301`:** a `301` is cached by browsers, so later clicks would never reach the server. Clicks would not be counted and expiration would not be enforced.
- **Unique codes:** codes are generated with `secrets` (not `random`). Uniqueness is guaranteed by a `UNIQUE` constraint in the database; on a collision the insert is rolled back and retried (up to 5 times, then `503`). A "check, then insert" approach would have a race condition between concurrent requests.
- **Atomic click counter:** the counter is incremented with a single `UPDATE ... SET click_count = click_count + 1`, so concurrent requests cannot lose clicks (a read-modify-write in Python could).
- **Expired links are kept:** this allows `410 Gone` (it existed, now expired) instead of `404` (never existed), keeps analytics available, and prevents a code from being reused for a different URL.
- **No request to the target URL on creation:** avoids SSRF risks. URLs are validated with Pydantic instead (http/https only, max 2048 characters).
- **One engine, one session per request:** the engine holds the connection pool (`pool_pre_ping`, `connect_timeout`); `get_db` yields a session per request and always closes it.
- **Sync SQLAlchemy:** simpler to reason about and enough for this scale.
- **Docker:** dependency files are copied and installed before the app code to use the layer cache (`uv sync --locked --no-dev`). The API waits for the database healthcheck (`depends_on: service_healthy`). The database port is bound to `127.0.0.1` only.
- **Tests on real PostgreSQL:** SQLite returns naive datetimes, which breaks the expiration check. Rare cases (code collisions) are forced with `monkeypatch`.

## Project structure

```
app/
  main.py          # FastAPI app and /health
  config.py        # settings from environment variables
  database.py      # engine, session, get_db dependency
  models.py        # SQLAlchemy model (links table)
  schemas.py       # Pydantic request/response models
  routers/links.py # HTTP endpoints
  services/links.py# business logic (create, resolve, analytics)
tests/             # pytest tests (conftest.py selects the test database)
Dockerfile
docker-compose.yml
```

## Status and roadmap

**Done**

- [x] Create link, redirect, click counting, expiration, analytics
- [x] Validation and error handling
- [x] Docker Compose setup with database healthcheck
- [x] Tests: create link, invalid URL, redirect, click count, unknown code, expired link, health, code collision and retry limit
- [x] Linting and formatting with ruff

**Planned (not implemented yet)**

- [ ] Database migrations with Alembic (currently `create_all` on startup)
- [ ] CI with GitHub Actions (ruff + pytest with a PostgreSQL service)
- [ ] Rate limiting on `POST /links`
- [ ] Concurrency test for the click counter
- [ ] Cleanup/archive job for very old expired links
- [ ] Run the container as a non-root user
- [ ] Log the underlying error when `/health` fails
- [ ] Deployment

**Known limitations**

- No authentication or users
- No migrations; schema changes are not applied automatically
- Expired rows are never removed, so the table only grows
- The atomic click counter is explained by design but not covered by a concurrency test
