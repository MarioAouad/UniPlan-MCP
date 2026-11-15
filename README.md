# UniPlan - local task app with MCP

UniPlan is a small university task app built with Python, FastAPI, SQLite,
and a plain HTML/CSS/JavaScript page. ChatGPT desktop or another compatible
local assistant can manage the same saved tasks through four MCP tools.
No API key, frontend build, Docker, or cloud deployment is required.

## Project layout

```text
code_sample_MCP/
|-- README.md                   Main setup and usage guide
|-- app.py                      FastAPI routes and page serving
|-- database.py                 SQLite storage
|-- models.py                   Shared validation models
|-- mcp_server.py               Four local MCP tools
|-- requirements.txt            Runtime dependencies
|-- requirements-dev.txt        Optional test and lint tools
|-- pyproject.toml              Test and formatting settings
|-- tasks.db                    Preserved demonstration data
|-- static/                     Web page, styles, and browser logic
|-- tests/                      API and MCP integration checks
|-- scripts/                    Standalone protocol smoke check
|-- screenshots/                Eight selected demonstration images
`-- docs/                       Architecture, API, demo, and verification
```

## Install and start

Use Python 3.11+ with SQLite 3.35+; Python 3.12 was verified.
After extracting the ZIP, open PowerShell **inside `code_sample_MCP`**:

```powershell
# Create an environment locally; it is intentionally excluded from the handover.
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Start the app and keep this terminal open.
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

If `py` is unavailable, replace `py -3.12` with the path to an installed Python
3.12 interpreter. Virtual-environment activation is optional; the commands above
call its interpreter directly.

Open **<http://127.0.0.1:8000>**. Add/edit tasks, complete or reopen them, and use
the filters. Click **Refresh** after an assistant changes data. Stop the server
with `Ctrl+C`; tasks remain saved in the root `tasks.db` file.

The existing demonstration database is preserved. New tasks receive new IDs;
the screenshots are historical evidence, not a live view of the current data.
The API reference is at <http://127.0.0.1:8000/docs>.

## Connect ChatGPT desktop or Codex

The connector uses **STDIO**, and the app API must already be running.
Recreate `.venv` first. Because the project was moved, update any existing
UniPlan MCP entry to the new paths rather than adding a duplicate.

In a supported ChatGPT desktop client, open **Settings > MCP servers** and edit
or add `uniplan`. Use:

| Setting | Value |
| --- | --- |
| Type | STDIO |
| Command | Absolute path to `code_sample_MCP\.venv\Scripts\python.exe` |
| Argument | Absolute path to `code_sample_MCP\mcp_server.py`, as one argument |
| Environment | `APP_BASE_URL=http://127.0.0.1:8000` |

Save and restart the connection. No OAuth login is required for this local server.
The [configuration example](docs/codex-config.example.toml) contains the updated
paths for the original laptop. If you extract elsewhere, replace those paths.

Alternatively, register the connector through the Codex CLI from the project root:

```powershell
$projectPath = (Get-Location).Path
codex mcp add uniplan --env APP_BASE_URL=http://127.0.0.1:8000 -- "$projectPath\.venv\Scripts\python.exe" "$projectPath\mcp_server.py"
codex mcp list
```

Restart your client after configuration. See [official MCP setup](https://learn.chatgpt.com/docs/extend/mcp)
for supported local clients and settings. Hosted ChatGPT web connections require
a remote MCP/plugin setup; this project supplies a local stdio connector.

## Ask the assistant

> Use UniPlan's list_tasks tool to show my saved tasks and their IDs.

> Use UniPlan to create "Prepare EAI presentation", course EAI, due on 2026-11-20.

> Use UniPlan to change task ID 1's deadline to 2026-11-22.

> Use UniPlan to mark task ID 1 complete.

Replace example IDs with actual saved IDs. Use `update_task` with
`completed=false` to reopen a task. The four tools are `list_tasks`,
`create_task`, `update_task`, and `complete_task`.

## Verify the project

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pip check

# Real stdio/HTTP demonstration with isolated temporary data.
.\.venv\Scripts\python.exe -m scripts.smoke_mcp
```

Tests and the smoke check never use your root `tasks.db`. They start a temporary
API, call the real MCP subprocess, verify shared data and errors, and restart the
API to check persistence.

## Documentation

| Document | Contents |
| --- | --- |
| [Architecture](docs/architecture.md) | Diagram, module responsibilities, decisions, and boundaries |
| [API contract](docs/api.md) | Task fields, routes, filters, validation, and environment variables |
| [Demonstration](docs/demo.md) | Repeatable assistant/web workflow and troubleshooting |
| [Verification](docs/verification.md) | Automated results and screenshot evidence limits |
| [Screenshot index](docs/screenshots.md) | Captions and demonstration order for the eight images |
| [Build log](docs/build-log.md) | Implementation and packaging history |
| [Original brief](docs/reference/implementation-brief.pdf) | Supplied project specification |

## Keep the handover small

The ZIP excludes `.venv`, caches, logs, and build output. Install dependencies
after extraction. If you zip the folder again after running it, exclude those
generated files; `.gitignore` documents their names but Windows ZIP does not
automatically apply ignore rules. Keep the app bound to `127.0.0.1`: this is a
single-user local prototype without authentication.
