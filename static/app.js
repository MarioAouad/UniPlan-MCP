/* The API is the source of truth. This page keeps no task data in localStorage. */
"use strict";

const createForm = document.querySelector("#create-form");
const filterForm = document.querySelector("#filter-form");
const taskList = document.querySelector("#task-list");
const editDialog = document.querySelector("#edit-dialog");
const editForm = document.querySelector("#edit-form");
let editingId = null;
let editingOriginal = null;
let listVersion = 0;

/** Read a calendar day in Beirut, independent of this browser's local timezone. */
function beirutDay(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Beirut",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const part = (name) => parts.find((item) => item.type === name).value;
  return `${part("year")}-${part("month")}-${part("day")}`;
}

/** Render a date without parsing YYYY-MM-DD as midnight in another timezone. */
function friendlyDate(value) {
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(0);
  date.setUTCFullYear(year, month - 1, day);
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

/** Announce one message. User content is assigned as text, never interpreted as HTML. */
function message(selector, text = "") {
  const element = document.querySelector(selector);
  element.textContent = text;
  element.hidden = !text;
}

/** Make one HTTP call; uncertain writes are never automatically retried. */
async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
      signal: AbortSignal.timeout(12000),
    });
  } catch {
    throw new Error(
      "Cannot reach UniPlan. Check the app terminal. A write may have saved; refresh before adding it again.",
    );
  }
  const body = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail
          .map((item) => `${item.loc.join(".")}: ${item.msg}`)
          .join("; ")
      : body.detail || `Request failed (${response.status}).`;
    throw new Error(detail);
  }
  return body;
}

/** Build a reusable text node; this prevents titles/course labels from injecting markup. */
function textElement(tag, className, text) {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = text;
  return element;
}

/** Open an editor with the exact saved ID rather than trying to match task titles. */
function openEditor(task) {
  editingId = task.id;
  editingOriginal = { ...task };
  editForm.elements.title.value = task.title;
  editForm.elements.course.value = task.course || "";
  editForm.elements.due_date.value = task.due_date || "";
  editForm.elements.completed.checked = task.completed;
  document.querySelector("#edit-id").textContent = `Saved task #${task.id}`;
  message("#edit-error");
  editDialog.showModal();
}

/** Change completion only after a click, then reload the actual saved state. */
async function toggleTask(task, button) {
  button.disabled = true;
  message("#error");
  try {
    const saved = task.completed
      ? await request(`/tasks/${task.id}`, {
          method: "PATCH",
          body: JSON.stringify({ completed: false }),
        })
      : await request(`/tasks/${task.id}/complete`, { method: "POST" });
    message(
      "#notice",
      `Task #${saved.id} ${saved.completed ? "completed. A small win!" : "reopened."}`,
    );
    await loadTasks();
  } catch (error) {
    message("#error", error.message);
  } finally {
    button.disabled = false;
  }
}

/** Render a task using semantic elements and accessible action names. */
function taskRow(task) {
  const row = textElement(
    "article",
    `task-row${task.completed ? " is-complete" : ""}`,
    "",
  );
  row.dataset.taskId = task.id;
  const toggle = textElement("button", "toggle", task.completed ? "✓" : "");
  toggle.type = "button";
  toggle.setAttribute(
    "aria-label",
    `${task.completed ? "Reopen" : "Complete"} task #${task.id}: ${task.title}`,
  );
  toggle.setAttribute("aria-pressed", String(task.completed));
  toggle.addEventListener("click", () => toggleTask(task, toggle));
  const content = textElement("div", "task-content", "");
  content.append(textElement("h3", "task-title", task.title));
  const meta = textElement("div", "task-meta", "");
  meta.append(textElement("span", "", `#${task.id}`));
  if (task.course) meta.append(textElement("span", "course-tag", task.course));
  const overdue =
    !task.completed && task.due_date && task.due_date < beirutDay();
  meta.append(
    textElement(
      "span",
      overdue ? "overdue" : "",
      task.due_date
        ? `${overdue ? "Overdue · " : "Due "}${friendlyDate(task.due_date)}`
        : "No due date",
    ),
  );
  meta.append(textElement("span", "", task.completed ? "Completed" : "To do"));
  content.append(meta);
  const edit = textElement("button", "quiet", "Edit ↗");
  edit.type = "button";
  edit.setAttribute("aria-label", `Edit task #${task.id}: ${task.title}`);
  edit.addEventListener("click", () => openEditor(task));
  row.append(toggle, content, edit);
  return row;
}

/** Reload filtered data; discard stale responses if the user applies another filter. */
async function loadTasks() {
  const version = ++listVersion;
  taskList.setAttribute("aria-busy", "true");
  const params = new URLSearchParams();
  for (const [key, value] of new FormData(filterForm)) {
    if (value.trim()) params.set(key, value.trim());
  }
  try {
    const tasks = await request(`/tasks?${params}`);
    if (version !== listVersion) return;
    taskList.replaceChildren(...tasks.map(taskRow));
    document.querySelector("#task-count").textContent = tasks.length;
    document.querySelector("#empty-state").hidden = tasks.length > 0;
    const filtered = params.size > 0;
    document.querySelector("#empty-state h3").textContent = filtered
      ? "No tasks match just yet."
      : "A clear space to begin.";
    document.querySelector("#empty-state p").textContent = filtered
      ? "Try another filter or clear them to see all tasks."
      : "Add your first task above. Small steps count.";
    const remaining = tasks.filter((task) => !task.completed).length;
    document.querySelector("#list-caption").textContent =
      `${tasks.length} ${filtered ? "matching" : "saved"} ${tasks.length === 1 ? "task" : "tasks"} · ${remaining} to do · Latest added first`;
  } catch (error) {
    if (version !== listVersion) return;
    message("#error", error.message);
    document.querySelector("#list-caption").textContent =
      "Could not refresh. Previously shown tasks may be out of date.";
  } finally {
    if (version === listVersion) taskList.setAttribute("aria-busy", "false");
  }
}

/** Convert form blanks into explicit nulls for the two optional fields. */
function formValues(form) {
  return {
    title: form.elements.title.value.trim(),
    course: form.elements.course.value.trim() || null,
    due_date: form.elements.due_date.value || null,
  };
}

/** Disable all form controls while saving to prevent accidental duplicate submissions. */
function setBusy(form, busy) {
  for (const element of form.elements) element.disabled = busy;
}

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = formValues(createForm);
  message("#error");
  message("#notice");
  setBusy(createForm, true);
  try {
    const saved = await request("/tasks", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    createForm.reset();
    message(
      "#notice",
      `Task #${saved.id} saved. ${filterForm.elements.completed.value === "true" ? "Clear the completed filter to see it." : "You're one step closer."}`,
    );
    await loadTasks();
  } catch (error) {
    message("#error", error.message);
  } finally {
    setBusy(createForm, false);
    createForm.elements.title.focus();
  }
});

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = {
    ...formValues(editForm),
    completed: editForm.elements.completed.checked,
  };
  // Send only edited fields, preserving unrelated changes made through MCP meanwhile.
  const changes = Object.fromEntries(
    Object.entries(values).filter(
      ([key, value]) => value !== editingOriginal[key],
    ),
  );
  message("#edit-error");
  setBusy(editForm, true);
  try {
    const saved = await request(`/tasks/${editingId}`, {
      method: "PATCH",
      body: JSON.stringify(changes),
    });
    editDialog.close();
    message("#error");
    message("#notice", `Changes to task #${saved.id} saved.`);
    await loadTasks();
  } catch (error) {
    message("#edit-error", error.message);
  } finally {
    setBusy(editForm, false);
  }
});

// Explicit refresh keeps the prototype simple and makes assistant changes easy to demonstrate.
filterForm.addEventListener("submit", (event) => {
  event.preventDefault();
  message("#error");
  loadTasks();
});
filterForm.addEventListener("reset", () => {
  setTimeout(() => {
    message("#error");
    loadTasks();
  }, 0);
});
document.querySelector("#refresh").addEventListener("click", () => {
  message("#error");
  loadTasks();
});
document
  .querySelector("#cancel-edit")
  .addEventListener("click", () => editDialog.close());
document.querySelector("#today").textContent = new Intl.DateTimeFormat(
  "en-GB",
  {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: "Asia/Beirut",
  },
).format(new Date());
loadTasks();
