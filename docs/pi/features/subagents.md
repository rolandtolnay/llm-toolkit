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

## Pi API Surface

Two implementation paths exist in Pi's extension API:

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

## Recommended: `pi-subagents` (nicobailon)

964 stars · 38K downloads/wk · v0.18.1 (Apr 2026) · [GitHub](https://github.com/nicobailon/pi-subagents)

The ecosystem standard. Agents are markdown files with YAML frontmatter stored in `.pi/agents/`.

**Three execution modes:**
- **Single** — one agent, one task
- **Chain** — sequential steps with `{task}`, `{previous}`, `{chain_dir}` template variables
- **Parallel** — concurrent with optional git worktree isolation

**Key features:**
- Slash commands: `/run`, `/chain`, `/parallel` with tab-completion
- Agents Manager overlay: `Ctrl+Shift+A`
- 9 builtin agents: scout, planner, worker, reviewer, context-builder, researcher, delegate, oracle, oracle-executor
- Chain files (`.chain.md`) for defining multi-step pipelines
- Forked context mode: branches the parent's current session state
- Model fallback chains
- Configurable output truncation (default 200KB, 5000 lines)
- Default 4 concurrent agents, configurable

**Known issues:**
- Bug #55: Custom agent with same name as builtin causes duplication
- Bug #72: `result.model` always shows requested model, not actual model used
- Bug #51: Async subagent fails silently with relative cwd
- Bug #64: Screen flicker when more agents visible than fit terminal

**Install:**

```bash
pi install npm:pi-subagents
```

## Alternative: `@tintinweb/pi-subagents`

197 stars · ~4.2K downloads/wk · v0.6.1 (Apr 2026) · [GitHub](https://github.com/tintinweb/pi-subagents)

Explicitly targets Claude Code parity. Growing fast, interesting differentiators.

**Key differentiators over nicobailon:**

| Feature | nicobailon (964 stars) | tintinweb (197 stars) |
|---------|----------------------|----------------------|
| Claude Code parity | Partial | Explicit goal — uses `Agent`, `get_subagent_result`, `steer_subagent` tool names |
| Memory persistence | Not mentioned | 3-scope system (project, local, user) |
| Live widget UI | Basic | Animated spinners, token counts, colored status icons |
| Conversation viewer | Not mentioned | Live overlay for watching agent sessions |
| Mid-run steering | Not mentioned | Inject messages into running agents |
| Event bus / RPC | intercomBridge | Native event bus (`subagents:rpc:spawn`, `subagents:rpc:stop`) |
| Skill preloading | Not mentioned | `.pi/skills/` injection |
| Tool denylist | Not mentioned | Per-agent tool denylists |
| Agent count | 9 builtins | 3 builtins (simpler) |
| Chain execution | `.chain.md` files | Not mentioned |

**Watch this one.** At 1/9th the adoption it's riskier today, but the persistent agent memory and Claude Code parity features may make it the better option as it matures.

## Alternative: `pi-subagent` (mjakl)

36 stars · Intentionally minimal single-file spawner with spawn/fork context modes. "Intentionally trimmed features from other implementations to keep the surface area small and predictable." Max depth: 3 with cycle guards. Good if you want the smallest possible surface area.

## Other Options Evaluated

| Package | Downloads/wk | Notes |
|---------|-------------|-------|
| `taskplane` | 18K | Queue-based AI agent orchestration, more opinionated |
| `pi-btw` | 5.7K | Parallel side conversations via `/btw`, lightweight |
| `@a5c-ai/babysitter-pi` | 26K | Orchestration package, less documentation |
| oh-my-pi (can1357) | N/A | Full fork of pi-mono with subagents baked in, not installable as extension |

## Decision

Install `pi-subagents` (nicobailon). Clear ecosystem winner by adoption, maintenance, and feature completeness. Watch `@tintinweb/pi-subagents` for features like persistent memory and Claude Code parity that may be worth switching to later.

## Status: Researched — Install on Day 1
