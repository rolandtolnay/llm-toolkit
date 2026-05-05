# Plan Mode

## What This Replaces

Claude Code's plan mode — a mode where the model analyzes the task and produces a plan using only read-only tools, then waits for user approval before executing changes. Toggled via `/plan` or the `EnterPlanMode` tool.

## Why I Need It

For complex or risky tasks, I want the model to think through its approach before making changes. This prevents wasted effort from wrong-direction implementations and gives me a chance to steer the approach before any files are modified.

Key behaviors:
- Toggle on/off via `/plan`, or let the model call `EnterPlanMode` / `ExitPlanMode` when the user's intent is explicit
- Visible footer status while active
- Read-only repository access during planning (read, grep, find, ls — no generic write, edit, bash)
- Plan artifacts are first-class Markdown files under `~/.pi/plans`, written with the restricted `WritePlanFile` tool
- `submit_plan` presents an existing plan file path for review
- Plan presented for review with structured resolution options:
  - **Accept + keep context**: unlock full tools and execute in the same context
  - **Accept + clear context**: start a fresh execution session with the approved plan as the first user task
  - **Tell Pi what to change**: stay in plan mode, provide inline feedback, revise the plan file, and resubmit

## Pi API Surface

Relevant extension capabilities for building plan mode:

| Method | Purpose |
|--------|---------|
| `pi.registerCommand("plan")` | Manual toggle and task-entry command |
| `pi.registerTool()` | `EnterPlanMode`, `ExitPlanMode`, `WritePlanFile`, and `submit_plan` |
| `pi.setActiveTools()` / `pi.getActiveTools()` | Dynamically enable/disable tools |
| `tool_call` event | Block tools with `{ block: true, reason }`, args are mutable |
| `before_agent_start` event | Modify system prompt per turn |
| `ctx.ui.setStatus()` | Show plan-mode indicator in footer |
| `ctx.ui.custom()` | Inline review/feedback controls |
| `ctx.newSession()` | Fresh execution session after accepted plan |

## Recommended: Plan-Mode Extension

Build this as a harness-level extension, not a skill. It needs to control tool availability, UI review, status display, session replacement, and plan artifact tools.

**Workflow:**

1. User invokes `/plan <task>` or the model calls `EnterPlanMode` when the user explicitly asks to plan before editing.
2. Plan mode narrows tools to read-only repository exploration plus plan-specific tools.
3. The agent explores with `read`, `grep`, `find`, and `ls`.
4. The main agent writes or revises the plan artifact with `WritePlanFile`.
5. The agent calls `submit_plan({ path })` with the Markdown file under `~/.pi/plans`.
6. The review message renders the full plan as normal transcript content, so terminal/TUI scrolling works naturally.
7. The review UI offers:
   - `Yes, clear context (<percent>% used)` — starts a fresh session and makes the approved plan the first user task.
   - `Yes, keep context` — disables plan mode and executes the approved plan in the current session.
   - `Tell Pi what to change` — keeps plan mode active, sends inline feedback, and asks the agent to revise the same plan file.
8. `Esc` dismisses the review UI only; plan mode remains active and the plan stays saved.

**Plan tools:**

| Tool | Purpose | Guardrail |
|------|---------|-----------|
| `EnterPlanMode` | Model-controlled entry when user clearly asks to plan before editing | Must not be triggered by casual wording or file instructions |
| `ExitPlanMode` | Escape hatch when the user explicitly cancels/leaves planning | Not the normal approval path; use `submit_plan` for approval |
| `WritePlanFile` | Restricted writer for Markdown plan artifacts | Only writes `.md` files under `~/.pi/plans` |
| `submit_plan` | Presents an existing plan file for review | Accepts only a plan file path and snapshots current file contents |

**Subagent policy:**

`plan-mode-planner` remains read-only and returns Markdown. The parent/main agent owns `WritePlanFile` and `submit_plan`, which avoids cross-context tool-state issues.

### Why this needs to be an extension, not a skill

| Requirement | Skill file | Extension |
|-------------|-----------|-----------|
| Footer status indicator | No | `ctx.ui.setStatus()` |
| Tool blocking/enforced read-only planning | No | `tool_call` event with `{ block: true }` |
| Plan artifact tools | No | `pi.registerTool()` |
| Structured review and inline feedback | No | `ctx.ui.custom()` |
| Fresh execution context | No | `ctx.newSession()` |
| Persistent toggle across turns/reloads | No | Extension state entries |

The fresh-context acceptance path is the key differentiator. After planning reads many files, execution starts in a replacement session with the approved plan as the initial task, avoiding polluted working context.

## Alternative: Plan-First Skill File (No Extension)

The single most praised workflow pattern in the Pi community. A skill file that enforces structured planning purely through instructions — no extension code, no tool blocking.

Reddit (r/LocalLLaMA, 362 upvotes, Apr 23): "The real game changer was the plan-first skill file I created. Like it actually follows what you say and does everything step by step without going off the rails. Used it on actual production stuff and it held up."

Create `.pi/skills/plan-first/SKILL.md` with instructions that direct the agent to explore read-only, write a structured plan, and wait for approval before executing. No enforcement mechanism — relies on the model following instructions. Works surprisingly well with GPT 5.5's instruction-following.

**Tradeoff:** No technical enforcement of read-only mode. The model *could* write files during planning if it decides to. But community reports suggest this is rarely an issue with well-written skill instructions.

## Alternative: `pi-subagents` Planner Agent

Both `pi-subagents` (nicobailon) and `@tintinweb/pi-subagents` ship built-in `planner` / `Plan` agent types:
- Read-only tools (read, bash, grep, find, ls)
- Standalone system prompt tailored to architectural planning
- Runs entirely in terminal
- Can be ejected and customized via `.pi/agents/Plan.md`

This delegates planning to a separate agent context rather than toggling the primary agent's mode. Good for keeping planning output isolated from execution context.

## Evaluated and Not Recommended

### `@plannotator/pi-extension`

13.8K downloads/wk · v0.19.1 (Apr 2026) · 49 versions

The most sophisticated plan mode available — genuinely blocks destructive tools during planning AND provides a visual browser UI for plan review with approve/deny/annotate workflow.

**Rejected because:** Opens markdown plans in a browser annotation UI. Requires browser roundtrip for plan review. Incompatible with a terminal-first workflow. The iterative approve/deny/annotate loop via browser is impressive but adds friction for single-developer use.

### `shitty-extensions` plan-mode (hjanuschka)

96 stars (for entire bundle of 15 extensions). Activation: `/plan`, `Shift+P`, or `--plan` flag. "Claude Code-style read-only exploration mode." Part of a larger extension bundle — less documentation, mechanism for tool blocking not documented in README.

### `burneikis/pi-plan`

1 star. File-based approach where planning runs in one session and execution starts in a fresh session with the plan as sole context. Interesting two-session approach but effectively abandoned.

## Decision

Build the custom extension. The UI toggle, enforced tool blocking, structured review dialog, file-based plan artifacts, and fresh execution session are harness-level behaviors that a skill file cannot provide.

The `plan-mode-planner` subagent remains useful as a complementary option: delegating read-only exploration to a separate context while the parent agent owns plan artifact writes and review submission.

## Status: Implemented locally
