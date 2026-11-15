"""Exercise real HTTP + MCP/stdio processes using a temporary database, then clean up.

Run from the project directory: python -m scripts.smoke_mcp
This is protocol evidence, not an observed conversation with an AI assistant.
"""

import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_DIR = Path(__file__).resolve().parents[1]


class RunningAPI:
    """Own only the API child process we start, allowing a real stop/restart test."""

    def __init__(self, db_path: Path) -> None:
        """Choose a free loopback port and keep the test database path explicit."""
        self.db_path = db_path
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.process: subprocess.Popen | None = None

    def start(self) -> None:
        """Start uvicorn and poll its real HTTP endpoint for at most 15 seconds."""
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--log-level",
                "warning",
            ],
            cwd=PROJECT_DIR,
            env={**os.environ, "UNIPLAN_DB_PATH": str(self.db_path)},
            stdout=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 15
        with httpx.Client(base_url=self.base_url, trust_env=False, timeout=0.5) as client:
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError("Test API exited before it was ready.")
                try:
                    if client.get("/tasks").status_code == 200:
                        return
                except httpx.RequestError:
                    pass
                time.sleep(0.1)
        raise TimeoutError("Test API was not ready within 15 seconds.")

    def stop(self) -> None:
        """Stop our child, wait for its file handles, and avoid orphaned processes."""
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
            self.process = None


def successful_result(result) -> Any:
    """Unwrap the SDK's structured list envelope; fail loudly on tool errors."""
    assert not result.is_error, result.model_dump(mode="json")
    value = result.structured_content
    assert value is not None, "Expected actual structured API results."
    return value["result"] if set(value) == {"result"} else value


async def run_smoke(db_path: Path) -> dict[str, Any]:
    """Discover all four tools, exchange stored data, restart, and verify failure cases."""
    api = RunningAPI(db_path)
    try:
        api.start()
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(PROJECT_DIR / "mcp_server.py")],
            cwd=str(PROJECT_DIR),
            env={**os.environ, "APP_BASE_URL": api.base_url},
        )
        async with stdio_client(parameters) as (read, write):  # noqa: SIM117
            async with ClientSession(read, write, read_timeout_seconds=15) as session:
                initialized = await session.initialize()
                tools = (await session.list_tools()).tools
                names = sorted(tool.name for tool in tools)
                assert names == ["complete_task", "create_task", "list_tasks", "update_task"]
                async with httpx.AsyncClient(base_url=api.base_url, trust_env=False) as http:
                    # The browser uses this same HTTP route; MCP must see the saved ID.
                    response = await http.post(
                        "/tasks", json={"title": "Web-created EAI task", "course": "EAI"}
                    )
                    assert response.status_code == 201
                    web_task = response.json()
                    listed = successful_result(
                        await session.call_tool("list_tasks", {"course": "EAI"})
                    )
                    assert listed == [web_task]

                    created = successful_result(
                        await session.call_tool(
                            "create_task",
                            {
                                "title": "MCP-created assignment",
                                "course": "EAI",
                                "due_date": "2026-11-20",
                            },
                        )
                    )
                    assert created in (await http.get("/tasks")).json()
                    changed = successful_result(
                        await session.call_tool(
                            "update_task",
                            {
                                "task_id": created["id"],
                                "changes": {"due_date": "2026-11-22"},
                            },
                        )
                    )
                    assert changed["due_date"] == "2026-11-22"
                    assert changed["title"] == created["title"]
                    for _ in range(2):
                        completed = successful_result(
                            await session.call_tool("complete_task", {"task_id": created["id"]})
                        )
                        assert completed["completed"] is True
                    assert completed in (await http.get("/tasks")).json()

                    # An app edit must be visible through MCP too, including cleared values.
                    edited = (
                        await http.patch(
                            f"/tasks/{created['id']}", json={"completed": False, "course": None}
                        )
                    ).json()
                    filtered = successful_result(
                        await session.call_tool(
                            "list_tasks",
                            {
                                "completed": False,
                                "due_before": "2026-11-22",
                            },
                        )
                    )
                    assert filtered == [edited]  # Undated tasks are excluded; cutoff is inclusive.

                    for tool, arguments, expected in (
                        ("create_task", {"title": "Invalid", "due_date": "2026-02-30"}, "422"),
                        (
                            "update_task",
                            {"task_id": 999999, "changes": {"title": "Missing"}},
                            "404",
                        ),
                        (
                            "update_task",
                            {"task_id": created["id"], "changes": {"typo": True}},
                            "typo",
                        ),
                        ("create_task", {"title": "Unknown field", "typo": True}, "typo"),
                    ):
                        failed = await session.call_tool(tool, arguments)
                        assert failed.is_error
                        assert expected in str(failed.content)

                    before_restart = (await http.get("/tasks")).json()
                    api.stop()
                    stopped = await session.call_tool("list_tasks", {})
                    assert stopped.is_error and "Cannot reach UniPlan" in str(stopped.content)
                    api.start()
                    after_restart = successful_result(await session.call_tool("list_tasks", {}))
                    assert after_restart == before_restart
                return {
                    "transport": "real subprocess stdio + loopback HTTP",
                    "server": initialized.server_info.name,
                    "tools": names,
                    "web_created_id": web_task["id"],
                    "mcp_created_id": created["id"],
                    "persisted_tasks_after_restart": len(after_restart),
                    "checks": (
                        "bidirectional data, edit, clear, complete twice, reopen, filters, "
                        "validation, 404, stopped API, restart"
                    ),
                    "assistant_connection": (
                        "This run is protocol-only; see docs/screenshots.md for desktop evidence."
                    ),
                }
    finally:
        api.stop()


if __name__ == "__main__":
    # TemporaryDirectory guarantees the demonstration never adds tasks to tasks.db.
    with tempfile.TemporaryDirectory(prefix="uniplan-smoke-") as directory:
        print(json.dumps(asyncio.run(run_smoke(Path(directory) / "tasks.db")), indent=2))
