# Repeatable demonstration

## Automated protocol demonstration

From the cloned or extracted repository root, after installing dependencies, run:

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke_mcp
```

This uses temporary data and its own HTTP port. It starts the real MCP subprocess,
discovers all four tools, changes actual SQLite data through HTTP, stops/restarts
the API, and verifies the results. A passing run prints evidence as JSON.
It is a protocol smoke test, **not proof of an observed assistant conversation**.

## Live assistant and web demonstration

First follow the [root README](../README.md) connection steps and start the API.
Use your connected ChatGPT desktop client or local Codex client.
Use a disposable demo title so you can distinguish it from coursework.

1. Open <http://127.0.0.1:8000>. Add **Review EAI integration notes** with course **EAI**.
   Record its saved ID from the success message/list.
2. Ask the assistant: **"Use UniPlan to list my EAI tasks. Show their IDs."**
   Verify it calls `list_tasks` and returns the same ID/title.
3. Ask: **"Use UniPlan to create a task titled 'Prepare MCP demo', course EAI,
   due on 2026-11-20. Return its saved ID."**
4. Click **Refresh** in the page. Verify that saved ID, date, and title appear.
5. Ask: **"Change task ID N's due date to 2026-11-22, then mark task ID N complete."**
   Replace N with the returned ID. Verify `update_task` and `complete_task` calls.
6. Refresh the page. Confirm the new deadline and completed status.
7. Use **Edit** in the page to clear the course and reopen that task. Save.
   Ask the assistant to list incomplete tasks; verify the same ID is reopened with a null course.
8. Stop the API with `Ctrl+C`, then start it with the same startup command.
   Refresh and ask the assistant to list tasks again. Saved data must remain.

Use explicit IDs. If multiple tasks share a title, the assistant should list them
and clarify the ID before updating. A filtered list may hide a task after a
status/course change; **Clear** filters to see all saved tasks.

## Failure demonstration

- Ask for a task with due date `2026-02-30`: expect a validation tool error, with no new task.
- Update an ID known not to exist: expect an HTTP 404 tool error.
- Stop the API and ask the assistant to list tasks: expect an actionable connection tool error.
  The assistant must not claim it changed data successfully.
- After an uncertain write, restart/refresh/list before creating again; a lost response
  does not prove that the database write failed.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Python opens the Store or fails | Call `.venv\Scripts\python.exe` directly; recreate the environment with a real Python install if needed. |
| Port 8000 is already in use | Stop the old UniPlan terminal, or run on 8001 and update `APP_BASE_URL` in the MCP configuration. |
| MCP server is missing | Check absolute paths, restart Codex, and inspect `/mcp` or `codex mcp list`. |
| MCP script waits without output | Normal when started by hand: stdio awaits protocol requests from a client. |
| MCP cannot reach the API | Start uvicorn first; verify the base URL/port and local terminal errors. |
| Task seems missing | Clear filters, click Refresh, and check that `UNIPLAN_DB_PATH` matches the intended database. |
| Database unavailable | Check file permissions, free disk space, and whether another program holds the file locked. |
| Date rejected | Use a real calendar date in exactly YYYY-MM-DD. |
| Unknown field rejected | Use only title, course, due_date, completed inside an update changes object. |

No API key is needed. The MCP connector and the application communicate locally.
