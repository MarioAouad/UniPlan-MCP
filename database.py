"""Small SQLite repository. Only the API uses it; MCP never opens the database."""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent


def database_path() -> Path:
    """Resolve even a relative override against the project, never the shell directory."""
    configured = Path(os.environ.get("UNIPLAN_DB_PATH", "tasks.db"))
    return (PROJECT_DIR / configured).resolve()


class TaskStore:
    """Use a short-lived connection per operation, safe across FastAPI worker threads."""

    def __init__(self, path: Path) -> None:
        """Keep the database location explicit so tests can use isolated files."""
        self.path = path.resolve()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Commit successful writes, roll back failures, and always close the connection."""
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            # SQLite's connection context manager commits but does not close the file.
            connection.close()

    def initialize(self) -> None:
        """Create the one-table schema without erasing any existing tasks."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 200),
                    course TEXT CHECK(course IS NULL OR length(trim(course)) BETWEEN 1 AND 80),
                    due_date TEXT,
                    completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0, 1))
                )
            """)

    @staticmethod
    def record(row: sqlite3.Row) -> dict[str, Any]:
        """Expose a JSON boolean rather than SQLite's integer representation."""
        return {**dict(row), "completed": bool(row["completed"])}

    def list_tasks(
        self,
        completed: bool | None = None,
        course: str | None = None,
        due_before: str | None = None,
    ) -> list[dict[str, Any]]:
        """Apply parameterized filters; ISO date strings sort chronologically."""
        conditions: list[str] = []
        parameters: list[Any] = []
        for column, operator, value in (
            ("completed", "=", completed),
            ("course", "=", course),
            ("due_date", "<=", due_before),
        ):
            if value is not None:
                # Column names/operators come only from this fixed internal tuple.
                conditions.append(f"{column} {operator} ?")
                parameters.append(value)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM tasks" + where + " ORDER BY id DESC", parameters
            ).fetchall()
        return [self.record(row) for row in rows]

    def create_task(
        self, title: str, course: str | None = None, due_date: str | None = None
    ) -> dict[str, Any]:
        """Return the actual inserted row from the same database transaction."""
        with self.connection() as connection:
            row = connection.execute(
                "INSERT INTO tasks (title, course, due_date) VALUES (?, ?, ?) RETURNING *",
                (title, course, due_date),
            ).fetchone()
        return self.record(row)

    def update_task(self, task_id: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        """Update only supplied fields atomically, returning None for a missing ID."""
        # Defense in depth: SQL identifiers must never originate from arbitrary input.
        if changes.keys() - {"title", "course", "due_date", "completed"}:
            raise ValueError("Unknown task field.")
        with self.connection() as connection:
            if changes:
                assignments = ", ".join(f"{field} = ?" for field in changes)
                row = connection.execute(
                    f"UPDATE tasks SET {assignments} WHERE id = ? RETURNING *",
                    [*changes.values(), task_id],
                ).fetchone()
            else:
                # An empty PATCH is an explicit no-op, and still checks that the ID exists.
                row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self.record(row) if row is not None else None
