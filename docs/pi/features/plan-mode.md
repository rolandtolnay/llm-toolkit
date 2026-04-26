# Plan Mode

## What This Replaces

Claude Code's plan mode — a mode where the model analyzes the task and produces a plan using only read-only tools, then waits for user approval before executing changes. Toggled via `/plan` or the `EnterPlanMode` tool.

## Why I Need It

For complex or risky tasks, I want the model to think through its approach before making changes. This prevents wasted effort from wrong-direction implementations and gives me a chance to steer the approach before any files are modified.

Key behaviors:
- Toggle on/off (persist across turns or per-task)
- Read-only tool access during planning (read, grep, find, ls — no write, edit, bash)
- Plan presented for review before execution
- User approves or redirects, then full tools unlock

## Pi API Surface (Known)

Relevant extension capabilities:
- `pi.registerCommand()` — for `/plan` toggle command
- `before_agent_start` event — can modify system prompt per turn
- `tool_call` event — can block tools with `{ block: true, reason }`, args are mutable
- `ctx.ui.setStatus()` — show plan mode indicator in footer
- `ctx.ui.setWidget()` — display the plan persistently above/below editor
- `ctx.ui.confirm()` — approval dialog before switching to execution
- `pi.setActiveTools()` / `pi.getActiveTools()` — dynamically enable/disable tools

## Alternatives

Pi's philosophy suggests a simpler file-based approach: ask the model to write a plan to `PLAN.md`, review it, then tell the model to execute. No extension needed. This may be sufficient depending on how structured I want the workflow.

## Research

- [ ] Check if an existing Pi package provides plan mode
- [ ] Evaluate file-based approach vs extension-based approach
- [ ] Look at how the "Till Done" extension from the video handles tool blocking — similar pattern

## Implementation

_To be filled after research._

## Status: Not Started
