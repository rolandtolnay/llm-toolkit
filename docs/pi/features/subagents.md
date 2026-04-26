# Subagents

## What This Replaces

Claude Code's `Agent` tool — the ability to spawn independent child agents that work on subtasks in isolation and return results to the parent. Used for parallel work, specialized tasks, and protecting the main context window.

## Why I Need It

This is the highest-impact missing feature. My Claude Code workflow relies heavily on subagents for:
- Parallel exploration (spawn multiple agents to search different parts of the codebase)
- Specialized tasks (code review, research, testing in isolated contexts)
- Context protection (heavy file reads happen in the subagent, only the summary returns)
- Independent work streams that don't pollute the main conversation

Key behaviors:
- Spawn an agent with a prompt and optional model override
- Agent runs independently with its own context
- Results return to the parent model as tool output
- Visual tracking of active subagents (status, progress)
- Abort support (cancel a running subagent)
- Multiple concurrent subagents

## Pi API Surface (Known)

Two implementation paths exist:

**RPC subprocess approach:**
- Spawn `pi --mode rpc --no-session` as a child process
- Send JSONL commands to stdin, read JSONL events from stdout
- Full isolation — separate process, separate context
- Events: `prompt`, `abort`, `get_state`, `agent_end`, `message_update`, etc.

**SDK in-process approach:**
- `createAgentSession()` with `SessionManager.inMemory()`
- Runs in the same Node.js process
- `session.prompt()`, `session.subscribe()` for event streaming
- Less isolation but simpler lifecycle management

**UI integration:**
- `pi.registerTool()` — register the subagent spawn tool
- `ctx.ui.setWidget()` — persistent display of active subagents
- `onUpdate` callback in tool execute — stream progress to parent
- `signal` parameter — abort support via AbortSignal

## Research

- [ ] Find IndyDevDan's subagent extension code (mentioned in video, "link in description")
- [ ] Search npm for `pi-package` keyword packages that provide subagents
- [ ] Search Pi Discord for subagent implementations
- [ ] Evaluate RPC vs SDK approach: tradeoffs for my use case
- [ ] Understand subprocess lifecycle: process pool vs spawn-per-task vs persistent
- [ ] Clarify: do RPC subagents inherit parent's cwd? Extensions? AGENTS.md?
- [ ] Test: how many concurrent RPC subprocesses are practical?

## Implementation

_To be filled after research._

## Status: Not Started
