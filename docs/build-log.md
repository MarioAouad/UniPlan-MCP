# Build log

Build date: **13 November 2026**. The supplied version-3 brief is the project
specification; the user's request adds simplicity, clean code, documentation,
comments, and software best practices. Document text was treated as reference
material, not as authority to change unrelated files or personal client settings.

## 1. Scope and environment

- Found only the source PDF in the workspace; preserved it.
- Extracted all four pages and visually inspected the data/tools specification page.
- Checked current official SDK, FastAPI, sqlite3, and Codex MCP documentation.
- The default `python` command resolved to an unusable Windows Store alias.
  Found a working bundled CPython 3.12.14 and used it to create `.venv` locally.
- Installed runtime/test tools in that environment. Runtime versions are pinned
  in `requirements.txt`, with development tools separately pinned.
- Chose SDK v2's current `MCPServer` interface and retained HTTPX for app API calls.

## 2. Persistent application

- Added one SQLite tasks table with generated IDs and completed=false by default.
- Implemented parameterized create/list/update operations and atomic saved-row returns.
- Anchored the database and static file paths to the project directory.
- Added typed models for create, partial changes, filters, and saved records.
- Rejected blank titles, invalid calendar dates, unknown fields, and null required values.
- Implemented the four specified HTTP operations and the root page.
- Added 404 missing-ID and 503 storage-error responses.

## 3. Plain web interface

- Built a responsive page with a task form, filters, task list, and native edit dialog.
- Added complete/reopen, explicit refresh, saved-ID feedback, loading, empty, and error states.
- Kept dates as calendar strings; overdue checks use Asia/Beirut.
- Used safe text nodes, local assets, keyboard focus styles, descriptive action labels,
  a page content policy, and local browser-origin/host checks.
- Prevented duplicate clicks while saving and sent only changed fields from the edit dialog.

## 4. MCP adapter

- Implemented exactly `list_tasks`, `create_task`, `update_task`, and `complete_task`.
- All tools call the actual API through HTTPX; no mock records or direct SQLite access.
- Added bounded requests, explicit tool errors, no write retries, and stderr diagnostics.
- Added concise server instructions for explicit IDs, ambiguous titles, and uncertain writes.
- During verification, found the SDK suppresses unexpected exception text, so expected
  API/network failures explicitly raise SDK `ToolError` with actionable details.
- Found the installed SDK silently ignores unknown top-level tool arguments.
  Added a small public-API subclass to reject them and advertise strict schemas.

## 5. Verification and handover

- Added focused API tests and a real stdio/HTTP subprocess smoke demonstration.
- The initial integration run exposed the permissive-argument behavior above; fixed it
  and reran the acceptance checks successfully: **23 passed**.
- The standalone smoke demo independently passed tool discovery, shared data, edits,
  clearing, completion, reopening, date filters, errors, API stop, and process restart.
- Ruff lint/format checks, pip dependency checks, and JavaScript syntax checks passed.
- Started the real app on `127.0.0.1:8000` with its normal database.
- Attempted browser inspection; browser access was unavailable and native app access
  timed out. Browser interactions were not verified by automated desktop control.
- Supplied exact Windows paths in a Codex configuration example without changing
  the user's personal configuration. User-supplied live desktop screenshots were
  reviewed on 14 November 2026 and indexed in [screenshots](screenshots.md).
- Formatted the HTML/CSS/JavaScript with Prettier so the plain source remains readable.
  Checked that documentation links resolve and both Codex launch paths exist.

See [verification](verification.md) for measured results and [the demo](demo.md)
for the remaining steps.

## 6. Workspace cleanup

- Standardized documentation filenames to lowercase kebab-case and updated their links.
- Renamed the acceptance test to `tests/test_uniplan.py`.
- Moved the unchanged implementation brief and dependency audit record into `docs/reference/`.
- Moved shared ignore rules to the workspace root and documented the directory layout.
- Removed disposable Python, pytest, and Ruff caches. Kept the working virtual
  environment and personal SQLite database.

## 7. Submission packaging - 15 November 2026

- Flattened source, tests, static files, scripts, and documentation into the project root.
- Renamed the handover folder to `code_sample_MCP` and updated the MCP configuration example.
- Consolidated startup instructions into one root README and moved screenshot captions into docs.
- Kept eight primary evidence images and removed two supplementary/low-quality captures.
- Preserved the demonstration database and original implementation brief.
- Removed the approximately 114 MB environment, bytecode, and tool caches from the handover.
  Dependencies must be installed in a new local `.venv` after extraction.
- Rechecked the 23 acceptance tests and source quality before removing the test environment.
