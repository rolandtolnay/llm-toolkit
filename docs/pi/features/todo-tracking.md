# TODO / Task Tracking

## What This Replaces

Claude Code's `TodoWrite` and `TaskCreate` tools — in-session task tracking with status updates, used by the agent to plan and track work items during multi-step operations.

## Why I Need It

Pi ships only 4 core tools (read, write, edit, bash). There's no built-in task tracking. Without it, agents lose track of multi-step work across compaction boundaries and have no structured way to communicate progress.

## Pi API Surface

Extensions register tools via `pi.registerTool()`. A TODO extension registers a tool the LLM can invoke to create, update, and list tasks. The extension controls persistence (file, session state, or branch replay) and can inject task context into agent turns via the `before_agent_start` event.

## Recommended: `pi-todo-md` (file-based)

712 downloads/wk · v0.4.0 (Apr 2026) · MIT · 0 dependencies

Manages a repo-local `TODO.md` file via a structured `todo_md` tool. Best fit for a terminal-first workflow migrating from Claude Code.

**Key features:**
- Stable task IDs with hidden HTML comments
- Named sections for organizing tasks
- Subtasks, priority levels, notes per task
- Reordering, bulk add, rename, focus mode
- Interactive `/todos [section]` browser
- Injects compact active-task summary into agent turns (survives compaction)
- Finds nearest `TODO.md` or creates at git root

**Why this over alternatives:** The file-based approach is more durable than in-memory state. A TODO.md in the repo root is inspectable, diffable, and survives session crashes. The context injection feature ensures the agent stays aligned with current tasks even across compaction. The TODO.md is also shareable and version-controllable.

**Install:**

```bash
pi install npm:pi-todo-md
```

## Alternative: `@juicesharp/rpiv-todo` (in-memory + overlay)

3,597 downloads/wk · v0.12.7 (Apr 2026) · MIT · 0 dependencies

"Claude-Code-parity todo tool + persistent overlay widget." Closer to Claude Code's TodoWrite UX with an overlay widget above the editor.

**Key features:**
- 4-state task machine: pending, in_progress, completed, deleted
- `blockedBy` dependency tracking with cycle detection
- TodoOverlay widget above editor
- `/todos` slash command
- Tasks persist via branch replay, survive compaction
- Auto-rendering overlay with 12-line collapse threshold

**Tradeoffs vs pi-todo-md:**

| Feature | pi-todo-md | @juicesharp/rpiv-todo |
|---------|------------|----------------------|
| Downloads/wk | 712 | 3,597 |
| Persistence | Real file on disk (TODO.md) | Branch replay (session-scoped) |
| Shareable | Yes (TODO.md in repo) | No |
| Task states | Checkbox + focus mode | 4-state machine |
| Dependencies | None | Cycle detection with blockedBy |
| Sections | Yes (named sections) | No |
| Subtasks | Yes | No |
| Priority | Yes | No |
| Context injection | Yes (active tasks per turn) | No |
| UI | `/todos` interactive browser | Overlay widget |

rpiv-todo has higher adoption and closer Claude Code parity. pi-todo-md has richer task features and file-based durability. For a power-user terminal workflow, pi-todo-md is the better fit.

## Other Options Evaluated

| Package | Downloads/wk | Notes |
|---------|-------------|-------|
| `@ryan_nookpi/pi-extension-todo-write` | 482 | Minimal, early version (v0.1.4) |
| `@artale/pi-todo` | 46 | Persistent with priorities/tags/due dates, low adoption |
| `@hyperprior/pi-todo` | 26 | "Branch-safe", stale (v0.1.0, 2 months old) |
| oh-my-pi TodoWrite | N/A | Built into the oh-my-pi fork, not installable separately |

## Decision

Install `pi-todo-md` for file-based TODO tracking with context injection. If you prefer Claude Code's overlay UX, use `@juicesharp/rpiv-todo` instead.

## Status: Researched — Install on Day 1
