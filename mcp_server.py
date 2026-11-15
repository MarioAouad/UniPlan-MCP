"""Four real stdio MCP tools adapting the local API, with no direct database access."""

import json
import logging
import os
from typing import Any

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from models import TaskChanges

APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


class StrictMCPServer(MCPServer):
    """Close the SDK's permissive top-level argument handling using public APIs only."""

    async def list_tools(self):
        """Advertise the same unknown-field rule as the HTTP input models."""
        tools = await super().list_tools()
        for tool in tools:
            tool.input_schema["additionalProperties"] = False
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any], context=None):
        """Reject unknown argument names before the SDK can silently drop them."""
        for tool in await self.list_tools():
            if tool.name == name:
                unknown = arguments.keys() - tool.input_schema.get("properties", {}).keys()
                if unknown:
                    raise ToolError(f"Unknown arguments for {name}: {', '.join(sorted(unknown))}")
                break
        return await super().call_tool(name, arguments, context)


mcp = StrictMCPServer(
    "UniPlan",
    log_level="WARNING",
    instructions=(
        "Use list_tasks to find real task IDs before changing data. If a title is ambiguous, "
        "ask which task the user means. Dates must be YYYY-MM-DD. Never claim success after "
        "a tool error. Do not automatically retry a failed create; list tasks first to see "
        "whether it was saved. The API must be running on this laptop."
    ),
)


async def api_request(method: str, path: str, **kwargs: Any) -> Any:
    """Make one bounded HTTP request and let the SDK turn exceptions into tool errors."""
    try:
        # Local traffic must not accidentally pass through a machine-wide HTTP proxy.
        # No retries: a timed-out write may already have committed successfully.
        async with httpx.AsyncClient(base_url=APP_BASE_URL, timeout=10, trust_env=False) as client:
            response = await client.request(method, path, **kwargs)
    except httpx.RequestError as error:
        raise ToolError(
            f"Cannot reach UniPlan at {APP_BASE_URL}. Start the API or check its terminal. "
            "A failed write may already have saved; list tasks before retrying a create."
        ) from error
    if response.is_error:
        # Keep API validation/404 details, and never return an error as a successful result.
        try:
            detail = response.json().get("detail", response.text)
        except (ValueError, AttributeError):
            detail = response.text
        raise ToolError(f"UniPlan API returned HTTP {response.status_code}: {json.dumps(detail)}")
    return response.json()


@mcp.tool()
async def list_tasks(
    completed: bool | None = None, course: str | None = None, due_before: str | None = None
) -> list[dict[str, Any]]:
    """List actual saved tasks with IDs. Filters combine; due_before is inclusive YYYY-MM-DD."""
    values = {"completed": completed, "course": course, "due_before": due_before}
    return await api_request(
        "GET", "/tasks", params={k: v for k, v in values.items() if v is not None}
    )


@mcp.tool()
async def create_task(
    title: str, course: str | None = None, due_date: str | None = None
) -> dict[str, Any]:
    """Create an incomplete task and return its saved ID. due_date is optional YYYY-MM-DD."""
    return await api_request(
        "POST", "/tasks", json={"title": title, "course": course, "due_date": due_date}
    )


@mcp.tool()
async def update_task(task_id: int, changes: TaskChanges) -> dict[str, Any]:
    """Edit an explicit ID. Supply changed fields only; null clears course/due_date.

    Set completed=false to reopen. Resolve ambiguous titles with the user before calling.
    """
    return await api_request(
        "PATCH", f"/tasks/{task_id}", json=changes.model_dump(exclude_unset=True)
    )


@mcp.tool()
async def complete_task(task_id: int) -> dict[str, Any]:
    """Mark an explicit saved task ID complete. Repeated calls keep it complete."""
    return await api_request("POST", f"/tasks/{task_id}/complete")


if __name__ == "__main__":
    # stdout belongs exclusively to JSON-RPC; standard logging writes to stderr.
    logging.basicConfig(level=logging.WARNING)
    mcp.run(transport="stdio")
