"""UniPlan's local HTTP API and plain web interface. Run with uvicorn app:app."""

import logging
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from database import PROJECT_DIR, TaskStore, database_path
from models import Task, TaskChanges, TaskCreate, TaskFilters

logger = logging.getLogger(__name__)


def create_app(db_path: Path | None = None) -> FastAPI:
    """Build an independent API instance; a custom path keeps tests away from real data."""
    store = TaskStore(db_path if db_path is not None else database_path())

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        """Initialize storage once at startup rather than while importing modules."""
        store.initialize()
        yield

    api = FastAPI(title="UniPlan", version="1.0.0", lifespan=lifespan)
    api.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )

    @api.middleware("http")
    async def local_browser_policy(request: Request, call_next):
        """Reject cross-origin browser writes and apply a small, self-hosted content policy."""
        origin = request.headers.get("origin")
        if (
            request.method in {"POST", "PATCH", "PUT", "DELETE"}
            and origin
            and origin != str(request.base_url).rstrip("/")
        ):
            return JSONResponse(status_code=403, content={"detail": "Cross-origin write rejected."})
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        # Swagger has its own CDN requirements; the application page uses only local files.
        if request.url.path == "/" or request.url.path.startswith("/static/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
            )
        response.headers["Cache-Control"] = "no-store"
        return response

    @api.exception_handler(sqlite3.Error)
    async def storage_error(request: Request, error: sqlite3.Error):
        """Log details locally while returning an actionable, non-sensitive API error."""
        logger.error("SQLite operation failed", exc_info=error)
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Task storage is unavailable. Check the app terminal and database file."
            },
        )

    @api.get("/", include_in_schema=False)
    def home():
        """Serve the same small interface regardless of the process working directory."""
        return FileResponse(PROJECT_DIR / "static" / "index.html")

    @api.get("/tasks", response_model=list[Task])
    def list_tasks(filters: Annotated[TaskFilters, Query()]):
        """List saved tasks using an exact course match and inclusive date cutoff."""
        return store.list_tasks(**filters.model_dump())

    @api.post("/tasks", response_model=Task, status_code=201)
    def create_task(task: TaskCreate):
        """Validate and persist a new incomplete task."""
        return store.create_task(**task.model_dump())

    def saved_or_404(task_id: int, changes: dict) -> dict:
        """Share missing-ID behavior between the two update operations."""
        task = store.update_task(task_id, changes)
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} was not found.")
        return task

    @api.patch("/tasks/{task_id}", response_model=Task)
    def update_task(task_id: int, changes: TaskChanges):
        """Preserve omitted fields; retain explicit null for optional-field clearing."""
        return saved_or_404(task_id, changes.model_dump(exclude_unset=True))

    @api.post("/tasks/{task_id}/complete", response_model=Task)
    def complete_task(task_id: int):
        """Idempotently mark a task complete; reopening is a PATCH with completed=false."""
        return saved_or_404(task_id, {"completed": True})

    api.mount("/static", StaticFiles(directory=PROJECT_DIR / "static"), name="static")
    return api


app = create_app()
