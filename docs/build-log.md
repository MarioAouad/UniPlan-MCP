# Implementation summary

This document describes the implementation present in the public repository.

## Application and storage

- FastAPI exposes list, create, partial update, and completion routes.
- Pydantic models validate task fields, filters, real calendar dates, and sparse updates.
- SQLite stores task IDs, titles, courses, due dates, and completion state.
- Database and static file paths resolve relative to the project directory.
- SQL values are parameterized, connections are short-lived, and updates return saved rows.

## Web page

- Plain HTML, CSS, and JavaScript provide task creation, filtering, editing, completion, and reopening.
- The page calls the API and refreshes explicitly.
- Task text is rendered as text rather than injected HTML.
- The API checks hostnames and browser write origins and applies a content policy to the page.
- Overdue dates are evaluated using Asia/Beirut.

## MCP adapter

- Four stdio tools adapt MCP requests to the same HTTP API.
- The connector does not open SQLite directly.
- Strict argument checks and the shared validation models reject unknown fields.
- HTTP and connection failures become tool errors; writes are not automatically retried.

## Verification and distribution

- API tests and the protocol smoke script use temporary data.
- The smoke workflow checks real MCP/HTTP communication and persistence across an API restart.
- Lint, format, and test settings are included in `pyproject.toml`.
- The root README explains installation, local startup, and MCP client configuration.
- The public code sample includes demonstration task data but excludes environments, caches, presentations, screenshots, assignment PDFs, and dependency audit exports.

See [architecture](architecture.md), [verification](verification.md), and [the demonstration](demo.md) for the current repository workflow.
