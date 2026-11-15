# Verification record

Initial verification: **13 November 2026**. Root-folder handover verification:
**15 November 2026**. Environment: Windows, CPython **3.12.14**, SQLite **3.53.1**.

## Actual results

| Check | Observed result |
| --- | --- |
| `python -m pytest -q` | **23 passed**; includes a real MCP stdio subprocess and real HTTP API subprocess |
| `python -m scripts.smoke_mcp` | Passed; discovered exactly four tools; two temporary tasks survived API process restart |
| `python -m ruff check .` | All checks passed |
| `python -m ruff format --check .` | All Python files formatted |
| `python -m pip check` | No broken requirements |
| `node --check static/app.js` | JavaScript syntax passed |
| Prettier HTML/CSS/JS formatting | Source formatted consistently; no frontend build dependency added |
| Documentation/config checks | Local documentation links resolve; TOML points to the new project root; recreate `.venv` after extraction |
| Normal uvicorn startup | Started successfully on `127.0.0.1:8000` |
| Browser task-list rendering | Reviewed user-supplied task-list screenshots; automated browser click-through was unavailable |
| Live assistant evidence | Reviewed ChatGPT desktop screenshots of actual Create task and List tasks results, matching app task ID 1 |

The installed local CLI reported `codex-cli 0.167.0-alpha.4.1` during the initial
build. User-supplied desktop evidence was reviewed on 14 November 2026; see the
[screenshot index](screenshots.md). Renaming the project requires updating the
existing MCP launch paths before reconnecting.

## What the tests prove

- Persistent creation with generated IDs, trimming, correct defaults, and valid leap dates.
- Partial update preservation, explicit clearing, empty-update behavior, completion idempotence,
  reopening, and persistence across both a new API instance and a real process restart.
- Combined exact course/completed/date filters, inclusive cutoff, and undated exclusion.
- Parameterized SQL handling of SQL-like course input.
- Rejection of malformed dates, empty/null titles, unexpected fields, invalid booleans,
  and updates that clear required fields; rejected writes leave saved data unchanged.
- HTTP 404 for missing IDs, 422 for invalid queries, local static/API serving,
  and rejection of cross-origin browser writes/untrusted hostnames.
- Database location independence from the launch directory.
- Real MCP initialization/discovery and calls for all four tools against live HTTP storage.
- Data visibility in both directions, correct tool errors for invalid dates, unknown IDs,
  unknown fields, and an unavailable API.

The automated 'web-created' smoke record is created through the browser's HTTP
route using an HTTP client. It proves the common API path, not browser interaction.
All automated data is temporary; the normal personal database is not used by tests.

## Tested dependencies

| Dependency | Version |
| --- | --- |
| FastAPI | 0.162.5 |
| Uvicorn | 0.54.0 |
| HTTPX | 0.28.1 |
| Official MCP SDK | 2.3.0 |
| Pydantic | 2.14.3 |
| Starlette (transitive) | 1.10.0 |
| pytest (development) | 9.2.0 |
| Ruff (development) | 0.17.5 |

Direct dependencies are pinned. Transitive dependencies are resolved by pip;
[tested-environment.txt](reference/tested-environment.txt) records every installed version from the verified Windows
environment. It is an audit record, not a cross-platform requirements file.

## Remaining manual acceptance

- Open the page at desktop and narrow/mobile widths; check legibility and horizontal overflow.
- Create a task, use each filter, edit/clear fields, complete, and reopen through the page.
- Check empty states, keyboard navigation, modal Escape/Cancel, and visible failure feedback.
- Repeat [the demo](demo.md) after extracting and updating the MCP paths if a new
  live presentation is needed. Existing desktop evidence is in the screenshot index.

The protocol test does not itself establish visual or live assistant acceptance.
Screenshot evidence is separate and limited to what the images visibly show.
