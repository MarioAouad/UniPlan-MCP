# Verification guide

Run these commands from the repository root after creating `.venv` and installing `requirements-dev.txt`:

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m scripts.smoke_mcp
~~~

If Node.js is installed, JavaScript syntax can also be checked with:

~~~powershell
node --check static/app.js
~~~

## Automated coverage

`tests/test_uniplan.py` checks API creation and filtering, trimmed fields, sparse updates, clearing optional fields, real dates, rejected fields and values, missing IDs, completion and reopening, SQLite persistence, static file serving, and local origin/host checks.

The integration check runs `scripts/smoke_mcp.py`. It starts a real temporary HTTP API and MCP stdio subprocess, discovers all four tools, verifies shared data and validation errors, and restarts the API to check persistence. The tests and script use isolated temporary databases rather than the root `tasks.db`.

A record created by the smoke script through HTTP proves the API path. It does not prove that a browser or an assistant conversation was manually exercised.

## Manual demonstration

Follow [the demonstration guide](demo.md) to verify the web page and a connected assistant together. Check task creation, filters, editing, clearing optional fields, completion, reopening, persistence, and visible failure messages. Also inspect keyboard navigation and narrow window layouts.

## Dependencies and evidence

Runtime versions are pinned in `requirements.txt`; test and lint tools are pinned in `requirements-dev.txt`. Transitive dependencies are resolved during installation.

This public repository does not include screenshots, a screenshot index, the original assignment brief, or the full installed-environment audit. It makes no claim that those artifacts can be opened here. Historical slide, image, and browser-check counts are not acceptance criteria for this code sample.
