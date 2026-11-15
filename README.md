# UniPlan — local task app with MCP

UniPlan is a university task manager built with Python, FastAPI, SQLite, and a plain HTML/CSS/JavaScript page. A local MCP client can list, create, update, and complete the same tasks shown in the browser.

The application and MCP connector run locally. The application needs no API key or frontend build; an assistant client may have its own account requirements.

## Repository contents

~~~text
UniPlan-MCP/
├── app.py                  FastAPI routes and web page serving
├── database.py             SQLite storage
├── models.py               Validation models
├── mcp_server.py           Four MCP tools over stdio
├── static/                 HTML, CSS, and JavaScript
├── tests/test_uniplan.py    API and MCP integration tests
├── scripts/smoke_mcp.py     Isolated protocol demonstration
├── docs/                   Architecture, API, demo, and verification guide
├── tasks.db                Demonstration task data
├── requirements.txt        Pinned runtime dependencies
├── requirements-dev.txt    Test and lint dependencies
└── pyproject.toml          Test and formatting configuration
~~~

This repository contains the code sample. Presentations, screenshots, screenshot indexes, original assignment PDFs, and the full dependency audit report are not included.

## Install and start

Use Python 3.11 or later and SQLite 3.35 or later. The commands below use Python 3.12 on Windows.

Clone the repository, or download and extract it using GitHub's **Code → Download ZIP**. Open PowerShell in the folder containing `app.py`:

~~~powershell
git clone https://github.com/MarioAouad/UniPlan-MCP.git
cd UniPlan-MCP
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
~~~

If you downloaded the ZIP, skip the first two commands and open its extracted project folder. If `py` is unavailable, use a Python 3.11+ interpreter to create the environment. On macOS/Linux, use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe`.

Open <http://127.0.0.1:8000>. The interactive API documentation is at <http://127.0.0.1:8000/docs>. Keep the server running while using the web page or MCP tools.

Tasks persist in `tasks.db`. The included database contains demonstration records; use the IDs returned by the running application. To start with a separate database, set `UNIPLAN_DB_PATH` before launching the API. Relative paths resolve against the project directory.

## Connect an MCP client

Start the API first. In a client supporting local stdio MCP servers, configure:

| Setting | Value |
| --- | --- |
| Transport | stdio |
| Command | Absolute path to `UniPlan-MCP\.venv\Scripts\python.exe` |
| Argument | Absolute path to `UniPlan-MCP\mcp_server.py` |
| Environment | `APP_BASE_URL=http://127.0.0.1:8000` |

Use paths to your own extracted or cloned folder. The [Codex configuration template](docs/codex-config.example.toml) uses placeholders that must be replaced.

For Codex CLI, run this from the project root:

~~~powershell
$projectPath = (Get-Location).Path
codex mcp add uniplan --env APP_BASE_URL=http://127.0.0.1:8000 -- "$projectPath\.venv\Scripts\python.exe" "$projectPath\mcp_server.py"
codex mcp list
~~~

If `uniplan` is already configured, update its existing entry to the current paths. Reconnect the client after changing its configuration. The connector is a local stdio server; it does not provide a hosted HTTP MCP endpoint. See the [official OpenAI MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) for Codex client configuration.

## Try it

1. Create a task in the web page and note its saved ID.
2. Ask your connected assistant: **Use UniPlan's list_tasks tool to show my tasks and their IDs.**
3. Ask it to create a task, then click **Refresh** in the web page.
4. Update or complete a task using its actual saved ID.
5. Use **Edit** in the page, or `update_task` with `completed=false`, to reopen it.

The tools are `list_tasks`, `create_task`, `update_task`, and `complete_task`. There is no delete tool. Filters can hide tasks after their course or completion state changes; clear the filters to see them again.

## Run checks

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m scripts.smoke_mcp
~~~

The tests and smoke script use temporary databases rather than the root demonstration database. The smoke script starts its own API and MCP subprocesses and checks tool discovery, writes, validation errors, and persistence across an API restart. These checks do not replace a manual browser and assistant demonstration.

## Documentation

- [Architecture](docs/architecture.md)
- [API contract and configuration](docs/api.md)
- [Demonstration and troubleshooting](docs/demo.md)
- [Verification guide](docs/verification.md)
- [Implementation summary](docs/build-log.md)

Keep the API bound to `127.0.0.1`. This is a local, single-user prototype without authentication. `.gitignore` excludes environments, caches, logs, and new database files. The included `tasks.db` is already tracked; use a separate database through `UNIPLAN_DB_PATH` to keep personal task changes outside source commits.
