"""Focused acceptance checks using temporary files, never the user's task database."""

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from database import PROJECT_DIR, database_path
from scripts.smoke_mcp import run_smoke


@pytest.fixture
def client(tmp_path):
    """Run the actual API lifecycle with an isolated SQLite database."""
    with TestClient(create_app(tmp_path / "tasks.db")) as api:
        yield api


def test_api_round_trip_and_restart(tmp_path):
    """Data survives a new API instance, and a partial update preserves omitted fields."""
    path = tmp_path / "persistent.db"
    with TestClient(create_app(path)) as api:
        created = api.post(
            "/tasks", json={"title": "  Study EAI  ", "course": "EAI", "due_date": "2028-02-29"}
        )
        assert created.status_code == 201
        task = created.json()
        assert task["title"] == "Study EAI" and task["completed"] is False
        changed = api.patch(f"/tasks/{task['id']}", json={"course": None}).json()
        assert changed == {**task, "course": None}
        assert api.patch(f"/tasks/{task['id']}", json={}).json() == changed
        for _ in range(2):
            assert api.post(f"/tasks/{task['id']}/complete").json()["completed"] is True
        saved = api.patch(
            f"/tasks/{task['id']}", json={"completed": False, "due_date": None}
        ).json()
    with TestClient(create_app(path)) as restarted:
        assert restarted.get("/tasks").json() == [saved]


def test_filters_combine_and_include_cutoff(client):
    """A due cutoff includes that day, excludes undated tasks, and combines with other filters."""
    for payload in (
        {"title": "At cutoff", "course": "EAI", "due_date": "2026-11-20"},
        {"title": "Later", "course": "EAI", "due_date": "2026-11-21"},
        {"title": "Undated", "course": "EAI"},
        {"title": "Other course", "course": "Math", "due_date": "2026-11-19"},
    ):
        assert client.post("/tasks", json=payload).status_code == 201
    result = client.get(
        "/tasks", params={"course": "EAI", "due_before": "2026-11-20", "completed": "false"}
    ).json()
    assert [task["title"] for task in result] == ["At cutoff"]
    client.post(f"/tasks/{result[0]['id']}/complete")
    assert client.get("/tasks", params={"completed": "true"}).json()[0]["id"] == result[0]["id"]
    # SQL-like input is a value, not executable SQL or a wildcard.
    assert client.get("/tasks", params={"course": "' OR 1=1 --"}).json() == []


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": " "},
        {"title": None},
        {"title": 5},
        {"title": "x", "due_date": "2026-02-29"},
        {"title": "x", "due_date": "2026-11-20T00:00:00"},
        {"title": "x", "due_date": "20261120"},
        {"title": "x", "due_date": 1795132800},
        {"title": "x", "course": " "},
        {"title": "x", "completed": True},
        {"title": "x", "unknown": "ignored?"},
    ],
)
def test_invalid_create_does_not_write(client, payload):
    """Invalid or unexpected creation fields yield 422 with no partial database write."""
    assert client.post("/tasks", json=payload).status_code == 422
    assert client.get("/tasks").json() == []


@pytest.mark.parametrize(
    "changes",
    [
        {"title": None},
        {"title": ""},
        {"completed": None},
        {"completed": "false"},
        {"due_date": "2026-04-31"},
        {"typo": "value"},
    ],
)
def test_invalid_update_preserves_task(client, changes):
    """Rejected updates must not change even one field of a saved task."""
    task = client.post("/tasks", json={"title": "Original"}).json()
    assert client.patch(f"/tasks/{task['id']}", json=changes).status_code == 422
    assert client.get("/tasks").json() == [task]


def test_missing_ids_and_invalid_filters(client):
    """Missing integer IDs return 404; malformed paths/query fields are validation errors."""
    assert client.patch("/tasks/999", json={"title": "Missing"}).status_code == 404
    assert client.post("/tasks/999/complete").status_code == 404
    assert client.patch("/tasks/no-id", json={"title": "Bad"}).status_code == 422
    for params in ({"due_before": "2026-02-30"}, {"completed": "maybe"}, {"typo": "EAI"}):
        assert client.get("/tasks", params=params).status_code == 422


def test_static_page_and_local_browser_boundary(client):
    """Serve the UI assets and block cross-origin browser writes and untrusted hostnames."""
    home = client.get("/")
    assert home.status_code == 200 and "UniPlan" in home.text
    assert "script-src 'self'" in home.headers["content-security-policy"]
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert (
        client.post(
            "/tasks", json={"title": "Cross origin"}, headers={"Origin": "https://example.com"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/tasks", json={"title": "Local"}, headers={"Origin": "http://testserver"}
        ).status_code
        == 201
    )
    assert client.get("/tasks", headers={"Host": "evil.example"}).status_code == 400


def test_database_location_is_independent_of_working_directory(monkeypatch, tmp_path):
    """A different launch directory must not silently select an empty database."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("UNIPLAN_DB_PATH", raising=False)
    assert database_path() == PROJECT_DIR / "tasks.db"
    monkeypatch.setenv("UNIPLAN_DB_PATH", "relative.db")
    assert database_path() == PROJECT_DIR / "relative.db"


def test_real_mcp_stdio_and_http(tmp_path: Path):
    """Discover/call the real connector against a real API, including process restart."""
    evidence = asyncio.run(run_smoke(tmp_path / "integration.db"))
    assert evidence["persisted_tasks_after_restart"] == 2
