# Claude Code to Pi: Onboarding Guide

This guide covers how to get productive in Pi, organized by dependency order — what you need first.

**Confidence levels:**

- **Verified** — Directly documented in Pi's official docs or confirmed via primary sources
- **Inferred** — Logical from the API surface, but no reference implementation seen
- **Needs validation** — Likely works but needs hands-on testing

**Status:** All outstanding research questions resolved (2026-04-26). See [OUTSTANDING.md](OUTSTANDING.md). Community packages confirmed for all missing features. GPT 5.5 prompting guidance integrated. Next step: hands-on installation and validation.

---

## Table of Contents

1. [Installation & First Run](#1-installation--first-run)
2. [Context Files (AGENTS.md)](#2-context-files-agentsmd)
3. [Settings](#3-settings)
4. [Skills (Porting Claude Code Skills)](#4-skills)
5. [Prompt Templates (Porting Slash Commands)](#5-prompt-templates)
6. [Extensions Overview](#6-extensions-overview)
7. [Hooks via Extensions](#7-hooks-via-extensions)
8. [Features to Install](#8-features-to-install)
9. [Pi-Native Features to Adopt](#9-pi-native-features-to-adopt)
10. [Feature Matrix](#10-feature-matrix)
11. [Quick Reference](#11-quick-reference)

---

## 1. Installation & First Run

**Confidence: Verified**

```bash
npm install -g @mariozechner/pi-coding-agent
```

### Authentication

Two options:

```bash
# Option A: API key (works with any provider)
export OPENAI_API_KEY=sk-...
pi --provider openai --model gpt-5.5

# Option B: Subscription login
pi
/login  # Select provider, OAuth flow
```

### Model Selection

```bash
# Direct model specification
pi --model openai/gpt-5.5

# With thinking level
pi --model openai/gpt-5.5:high

# Switch mid-session
/model                    # Opens selector
Ctrl+L                    # Same thing
Ctrl+P / Shift+Ctrl+P    # Cycle through scoped models
```

### Key Differences from Claude Code on First Run

- **No permission prompts** — Pi runs in YOLO mode. Full system access by default.
- **4 built-in tools** — `read`, `write`, `edit`, `bash` (plus `grep`, `find`, `ls`). Claude Code has more.
- **200-token system prompt** — Minimal. The model drives behavior, not the harness.
- **No safety modes** — No plan mode, no permission tiers. Build what you need.

---

## 2. Context Files (AGENTS.md)

**Confidence: Verified**

Pi loads `AGENTS.md` at startup from multiple locations, identical to how Claude Code loads `CLAUDE.md`. Pi also supports `CLAUDE.md` as a fallback.

### Locations (loaded in order, concatenated)

| Location                                 | Scope                 |
| ---------------------------------------- | --------------------- |
| `~/.pi/agent/AGENTS.md`                  | Global (all projects) |
| Parent directories (walking up from cwd) | Inherited             |
| Current directory `./AGENTS.md`          | Project               |

### Migration Steps

1. **Global instructions**: Copy `~/.claude/CLAUDE.md` to `~/.pi/agent/AGENTS.md`
2. **Project instructions**: Either rename `CLAUDE.md` to `AGENTS.md` or keep both — Pi reads `CLAUDE.md` as fallback
3. **Content adjustments**: If your CLAUDE.md references Claude-specific features (hooks config, permissions, etc.), strip those for the Pi version

### GPT 5.5 AGENTS.md Template

GPT 5.5 is actively harmed by Claude Code-style process-heavy prompts. OpenAI's official guidance: "start with the smallest prompt that preserves the product contract." Pi's ~200-token default is a strength — keep AGENTS.md to ~400 tokens covering only true invariants and outcome standards.

Key GPT 5.5 behavioral differences:

- **Outcome-first, not process-heavy** — define what you want, not step-by-step how to get there
- **MUST/NEVER only for true invariants** — git safety, factual accuracy. For judgment calls, use "prefer" / "suggest"
- **Contradictory instructions degrade GPT 5.5 significantly** — worse than in Claude models. Remove ambiguities.
- **Start reasoning effort at `medium`** — GPT 5.5 reasons more efficiently; escalate only when needed

Recommended global `~/.pi/agent/AGENTS.md`:

```markdown
# Conventions

## Identity

Senior engineer. High agency, principled judgment. Proceed without asking when the next step is low-risk and intent is clear.

## Outcome Standards

- Correctness first, brevity second
- No emojis, filler, or ceremony
- Verify all directly affected artifacts (callsites, tests, docs) before yielding
- Do not present partial work as complete — mark [blocked] if stuck
- Do not fabricate outputs that were not observed

## Tool Use

- Use `rg` for text search, `rg --files` for file discovery
- Search before you read — do not read files hoping to find the right thing
- Resolve prerequisites before acting
- Do not stop at the first plausible answer if another tool call would reduce uncertainty

## Git Safety

- NEVER revert changes you did not make unless explicitly requested
- NEVER use `git reset --hard`, `git checkout --`, `git clean -fd`
- Do not amend commits unless explicitly requested
- Only commit files YOU changed in THIS session using specific file paths

## Presentation

- Be concise. Lead with what changed and why, then context
- Reference file paths, do not dump file contents
- Use numbered lists for multiple options so user can respond with a number
```

Sources: [OpenAI GPT-5.5 Prompt Guidance](https://developers.openai.com/api/docs/guides/prompt-guidance), [Codex CLI system prompt](https://github.com/openai/codex/blob/main/codex-rs/core/gpt-5.2-codex_prompt.md), [oh-my-pi system prompt](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/src/prompts/system/system-prompt.md)

### System Prompt Override

For deeper customization beyond AGENTS.md:

| File                           | Effect                                                    |
| ------------------------------ | --------------------------------------------------------- |
| `.pi/SYSTEM.md`                | **Replaces** the default 200-token system prompt entirely |
| `.pi/APPEND_SYSTEM.md`         | **Appends** to the default system prompt                  |
| `~/.pi/agent/SYSTEM.md`        | Global system prompt override                             |
| `~/.pi/agent/APPEND_SYSTEM.md` | Global system prompt append                               |

**Recommendation: Use AGENTS.md, not SYSTEM.md.** Pi's default prompt is already minimal (~200 tokens) — there's nothing to remove. It dynamically injects tool listings that you'd have to replicate manually in a SYSTEM.md. Mario Zechner's own usage (pi-mono repo) uses AGENTS.md. Reserve SYSTEM.md only for fundamentally different agent identity (non-coding tasks, RFC 2119-style normative frameworks like oh-my-pi).

### Disable Context Files

```bash
pi --no-context-files    # or -nc
```

---

## 3. Settings

**Confidence: Verified**

### File Locations

| Location                    | Scope                                       |
| --------------------------- | ------------------------------------------- |
| `~/.pi/agent/settings.json` | Global                                      |
| `.pi/settings.json`         | Project (overrides global via nested merge) |

### Essential Settings for Migration

```json
{
  "defaultProvider": "openai",
  "defaultModel": "gpt-5.5",
  "defaultThinkingLevel": "high",
  "theme": "dark",
  "compaction": {
    "enabled": true,
    "reserveTokens": 16384,
    "keepRecentTokens": 20000
  },
  "retry": {
    "enabled": true,
    "maxRetries": 3,
    "baseDelayMs": 2000
  },
  "enableSkillCommands": true,
  "enabledModels": ["gpt-5.5", "gpt-5.5-mini", "claude-*"]
}
```

### Model Cycling

The `enabledModels` array controls what Ctrl+P cycles through. Supports glob patterns:

```json
{
  "enabledModels": ["gpt-5.5*", "claude-sonnet*", "gemini-3*"]
}
```

### Auto-Compaction

Enabled by default. When approaching the context limit:

1. Older messages get summarized
2. Recent messages (controlled by `keepRecentTokens`) stay untouched
3. Full history remains in the JSONL session file — use `/tree` to revisit

Manual: `/compact` or `/compact <custom instructions>`

---

## 4. Skills

**Confidence: Verified**

Pi skills follow the [Agent Skills standard](https://agentskills.io). They are **purely prompt-based** — a directory with a `SKILL.md` file and optional supporting files.

### File Structure

```
my-skill/
├── SKILL.md              # Required: frontmatter + instructions
├── scripts/              # Helper scripts the skill references
│   └── process.sh
├── references/           # Detailed docs loaded on-demand
│   └── api-reference.md
└── assets/
    └── template.json
```

### SKILL.md Format

```markdown
---
name: my-skill
description: Does X when the user asks about Y. Use when Z.
---

# My Skill

## Steps

1. Do this
2. Then that

## Reference

See [API docs](references/api-reference.md) for details.
```

### Frontmatter Fields

| Field                      | Required | Description                                                           |
| -------------------------- | -------- | --------------------------------------------------------------------- |
| `name`                     | Yes      | Max 64 chars. Lowercase a-z, 0-9, hyphens. Must match directory name. |
| `description`              | Yes      | Max 1024 chars. Determines when the agent auto-loads it.              |
| `license`                  | No       | License reference                                                     |
| `compatibility`            | No       | Environment requirements                                              |
| `disable-model-invocation` | No       | When `true`, only manual `/skill:name` works                          |
| `allowed-tools`            | No       | Pre-approved tools (experimental)                                     |

### Discovery Locations

| Location                            | Notes                               |
| ----------------------------------- | ----------------------------------- |
| `~/.pi/agent/skills/`               | Global                              |
| `~/.agents/skills/`                 | Global (Agent Skills standard path) |
| `.pi/skills/`                       | Project                             |
| `.agents/skills/` (cwd + ancestors) | Project + parent dirs               |
| Pi packages                         | Via `pi install`                    |

### Invocation

```bash
/skill:my-skill              # Manual load
/skill:my-skill some args    # With arguments (appended as "User: some args")
```

Skills are also listed in the system prompt at startup (name + description only). The model can auto-load the full SKILL.md via `read` when a task matches.

### Porting Claude Code Skills

Claude Code skills (in `commands/` or `skills/`) are already Markdown-based. To port:

1. Create a directory matching the skill name: `.pi/skills/my-skill/`
2. Move the skill content to `SKILL.md` inside that directory
3. Add the required frontmatter (`name`, `description`)
4. Move any referenced scripts/files into the skill directory
5. Update any Claude-specific tool references (e.g., `Agent`, `TodoWrite` don't exist in Pi)

### Key Difference from Claude Code Skills

- Pi skills are **directory-based** (SKILL.md inside a named directory), not standalone `.md` files
- Pi skills use **progressive disclosure** — only descriptions are in the system prompt; full content loads on-demand
- Pi skills **cannot register tools** — they educate the model via instructions. For tool registration, use extensions.

---

## 5. Prompt Templates

**Confidence: Verified**

Prompt templates are Pi's equivalent of simple Claude Code slash commands — reusable prompts as Markdown files.

### File Format

```markdown
## <!-- ~/.pi/agent/prompts/review.md -->

description: Review code for bugs, security, and performance
argument-hint: "<file-or-area>"

---

Review this code for bugs, security issues, and performance problems.
Focus on: $1
Additional context: ${@:2}
```

### Argument Syntax

| Syntax               | Meaning                     |
| -------------------- | --------------------------- |
| `$1`, `$2`, ...      | Positional arguments        |
| `$@` or `$ARGUMENTS` | All arguments joined        |
| `${@:N}`             | Arguments from Nth position |
| `${@:N:L}`           | L arguments starting at N   |

### Discovery Locations

| Location               | Notes            |
| ---------------------- | ---------------- |
| `~/.pi/agent/prompts/` | Global           |
| `.pi/prompts/`         | Project          |
| Pi packages            | Via `pi install` |

Discovery is **non-recursive** — templates must be directly in the prompts directory.

### Invocation

Type `/` then the filename (minus `.md`):

```
/review src/auth.ts          # Expands review.md with $1 = "src/auth.ts"
/component Button "onClick"  # Multiple arguments
```

### Porting Claude Code Slash Commands

Simple Claude Code commands that are just prompt text can become prompt templates directly. Commands that rely on Claude Code features (Agent tool, hooks, etc.) need to become skills or extensions instead.

---

## 6. Extensions Overview

**Confidence: Verified**

Extensions are TypeScript modules — the core building block for everything Pi doesn't include out of the box. This is how you build subagents, plan mode, ask-user-question, and hooks.

### Minimal Extension

```typescript
// .pi/extensions/my-extension.ts
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // Register tools, commands, event handlers, UI components
  pi.on("session_start", (_event, ctx) => {
    ctx.ui.notify("Extension loaded!", "info");
  });
}
```

### Discovery Locations

| Location                            | Notes                     |
| ----------------------------------- | ------------------------- |
| `~/.pi/agent/extensions/*.ts`       | Global                    |
| `~/.pi/agent/extensions/*/index.ts` | Global (directory-based)  |
| `.pi/extensions/*.ts`               | Project                   |
| `.pi/extensions/*/index.ts`         | Project (directory-based) |

### Loading & Stacking

Extensions are loaded via jiti (TypeScript on the fly, no compilation needed). Stack multiple via CLI:

```bash
pi -e ./ext/footer.ts -e ./ext/subagents.ts -e ./ext/theme-cycler.ts
```

Or configure in `settings.json`:

```json
{
  "extensions": ["./extensions/my-ext.ts", "./extensions/"]
}
```

Extensions compose — event handlers run in load order, tools/commands register independently.

### Core API Surface

| Method                                       | Purpose                                      |
| -------------------------------------------- | -------------------------------------------- |
| `pi.on(event, handler)`                      | Subscribe to lifecycle events                |
| `pi.registerTool(def)`                       | Register LLM-callable tools                  |
| `pi.registerCommand(name, opts)`             | Register `/commands`                         |
| `pi.registerShortcut(key, opts)`             | Register keyboard shortcuts                  |
| `pi.sendMessage(msg)`                        | Inject messages into session                 |
| `pi.appendEntry(type, data)`                 | Persist extension state                      |
| `pi.registerMessageRenderer(type, renderer)` | Custom message display                       |
| `pi.registerProvider(name, config)`          | Register model providers                     |
| `pi.getActiveTools() / setActiveTools()`     | Manage tool activation                       |
| `pi.events`                                  | Shared bus for inter-extension communication |

### Hot Reload

Use `/reload` to reload extensions without restarting. Emits `session_shutdown` for old instance, reloads, emits `session_start(reason: "reload")`.

---

## 7. Hooks via Extensions

**Confidence: Verified**

Pi's hook system is implemented through extension events. It's **more granular** than Claude Code's hooks but requires TypeScript instead of shell scripts.

### All Available Events

#### Session Lifecycle

| Event                    | When                         | Can Block?                    |
| ------------------------ | ---------------------------- | ----------------------------- |
| `session_start`          | Session starts/loads/reloads | No                            |
| `session_shutdown`       | Before teardown              | No                            |
| `session_before_switch`  | Before `/new` or `/resume`   | Yes                           |
| `session_before_fork`    | Before `/fork` or `/clone`   | Yes                           |
| `session_before_compact` | Before compaction            | Can provide custom summary    |
| `session_compact`        | On compaction                | No                            |
| `resources_discover`     | After session_start          | Can contribute resource paths |

#### Agent Lifecycle

| Event                | When                                | Can Block?                                |
| -------------------- | ----------------------------------- | ----------------------------------------- |
| `before_agent_start` | After user submits, before LLM      | Can inject messages, modify system prompt |
| `agent_start`        | Once per user prompt                | No                                        |
| `agent_end`          | After LLM finishes                  | No                                        |
| `turn_start`         | Each LLM response + tool call cycle | No                                        |
| `turn_end`           | After tools executed                | No                                        |

#### Tool Execution

| Event                   | When                          | Can Block?                                                            |
| ----------------------- | ----------------------------- | --------------------------------------------------------------------- |
| `tool_execution_start`  | Before tool runs              | No                                                                    |
| `tool_execution_update` | During execution (streaming)  | No                                                                    |
| `tool_execution_end`    | After execution               | No                                                                    |
| `tool_call`             | After start, before execute   | **Yes — can block** with `{ block: true, reason }`. Args are mutable. |
| `tool_result`           | After execute, before message | Can modify result (middleware chain)                                  |

#### Messages

| Event            | When                    | Can Block? |
| ---------------- | ----------------------- | ---------- |
| `message_start`  | Message lifecycle start | No         |
| `message_update` | Streaming updates       | No         |
| `message_end`    | Message lifecycle end   | No         |

#### User Input

| Event       | When                                  | Can Block?              |
| ----------- | ------------------------------------- | ----------------------- |
| `input`     | After command check, before expansion | Can transform or handle |
| `user_bash` | On `!` or `!!` commands               | Can intercept           |

#### Provider

| Event                     | When                | Can Block?          |
| ------------------------- | ------------------- | ------------------- |
| `before_provider_request` | Before HTTP request | Can replace payload |
| `after_provider_response` | After HTTP response | No                  |
| `model_select`            | On model change     | No                  |

#### Context

| Event     | When                 | Can Block?                                   |
| --------- | -------------------- | -------------------------------------------- |
| `context` | Before each LLM call | Can filter/modify messages (non-destructive) |

### Example: Blocking Dangerous Commands (like Claude Code's PreToolUse hook)

```typescript
export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName === "bash") {
      const cmd = event.input?.command || "";
      const dangerous = ["rm -rf", "sudo", "DROP TABLE"];
      if (dangerous.some((d) => cmd.includes(d))) {
        const ok = await ctx.ui.confirm("Dangerous Command", `Allow: ${cmd}?`);
        if (!ok) return { block: true, reason: "Blocked by damage control" };
      }
    }
  });
}
```

### Example: Injecting Context Before Each LLM Call

```typescript
export default function (pi: ExtensionAPI) {
  pi.on("before_agent_start", async (event, ctx) => {
    event.systemPrompt += "\n\nAlways explain your reasoning before acting.";
  });
}
```

### Porting Claude Code Hooks

| Claude Code Hook | Pi Equivalent                               |
| ---------------- | ------------------------------------------- |
| `PreToolUse`     | `tool_call` event (can block, mutate args)  |
| `PostToolUse`    | `tool_result` event (can modify result)     |
| `Notification`   | `agent_end` event                           |
| `Stop`           | `agent_end` event                           |
| `SubagentStop`   | No direct equivalent (subagents are custom) |

**Key difference**: Claude Code hooks are shell scripts in `settings.json`. Pi hooks are TypeScript in extension files. More powerful, but requires writing TypeScript.

---

## 8. Features to Install

**Confidence: Verified** (packages confirmed via npm and GitHub; runtime behavior needs validation)

All five Claude Code features missing from Pi have mature, actively-maintained community packages or straightforward custom builds. Install what exists — build only what's simple enough to be better custom.

```bash
pi install npm:pi-subagents
pi install npm:pi-ask-user
pi install npm:pi-todo-md
# Web search: build custom Codex delegation extension (~15 lines) — see below
# Plan mode: build custom extension (~80 lines) — see below
```

### Subagents — `pi-subagents` (nicobailon)

964 stars · 38K downloads/wk · v0.18.1 (Apr 2026) · [GitHub](https://github.com/nicobailon/pi-subagents)

Agents are markdown files with YAML frontmatter stored in `.pi/agents/`. Three execution modes:

- **Single** — one agent, one task
- **Chain** — sequential steps with `{task}`, `{previous}`, `{chain_dir}` template variables
- **Parallel** — concurrent with optional git worktree isolation

Slash commands: `/run`, `/chain`, `/parallel` with tab-completion. Agents Manager overlay: `Ctrl+Shift+A`. Forked context mode branches the parent's current session state. Default 4 concurrent agents, configurable.

**Alternative:** `pi-subagent` (mjakl, 36 stars) — intentionally minimal single-file spawner with spawn/fork context modes. Good if you want the smallest possible surface area.

### Plan Mode — Build Custom (~80 lines)

Pi's API surface makes this straightforward to build as a small custom extension. The core components:

- `pi.registerCommand("plan")` — toggle command
- `pi.setActiveTools()` / `pi.getActiveTools()` — restrict to read-only tools (`read`, `grep`, `find`, `ls`) during planning
- `tool_call` event — block `write`, `edit`, `bash` with `{ block: true, reason }`
- `ctx.ui.setStatus()` — show "PLAN MODE" indicator in footer
- `ctx.ui.confirm()` — approval dialog before switching to execution

Workflow: `/plan` toggles on → agent explores read-only and produces a plan → user reviews → approves via confirm dialog → full tools unlock.

```typescript
// .pi/extensions/plan-mode.ts
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  let planMode = false;
  const readOnlyTools = ["read", "grep", "find", "ls"];

  pi.registerCommand("plan", {
    description: "Toggle plan mode (read-only exploration)",
    async execute(_args, ctx) {
      planMode = !planMode;
      if (planMode) {
        ctx.ui.setStatus("plan-mode", "PLAN MODE");
        pi.sendMessage({
          role: "user",
          content:
            "You are now in plan mode. Explore the codebase using read-only tools only. Write your plan, then I will approve before execution.",
        });
      } else {
        ctx.ui.setStatus("plan-mode", "");
      }
    },
  });

  pi.on("tool_call", async (event, ctx) => {
    if (!planMode) return;
    if (!readOnlyTools.includes(event.toolName)) {
      return {
        block: true,
        reason:
          "Plan mode active — read-only tools only. Write your plan first.",
      };
    }
  });
}
```

This is a starting skeleton — extend with `ctx.ui.confirm()` for plan approval and `ctx.ui.setWidget()` to display the plan persistently.

**Fallback:** File-based PLAN.md approach — instruct via AGENTS.md to write a plan first and wait for approval. No extension needed, but no enforcement.

### Ask User Question — `pi-ask-user` (edlsh)

44 stars · v0.6.1 (Apr 2026) · [GitHub](https://github.com/edlsh/pi-ask-user)

Registers an `ask_user` tool with: searchable single/multi-select, optional freeform responses, timeout for auto-dismiss, split-pane details preview on wide terminals. Bundled `ask-user` skill for decision-gating in high-stakes tasks.

**Alternative:** Build custom (~50 lines). Core pattern: `pi.registerTool()` → call `ctx.ui.select()` → return result. But the existing extension's UX polish (searchable options, overlay mode) would take meaningful effort to replicate.

### Web Search — Codex CLI Delegation (Build Custom ~15 lines)

Delegates web search to Codex CLI's built-in search tool. When authenticated via `codex login` (ChatGPT OAuth), search is included in your subscription quota — no separate API keys or credits needed. Codex uses OpenAI's own web search index (cached mode, default) or live web fetching (`--search` flag).

**Why not `pi-web-access`?** The popular community package (378 stars, 16K dl/wk) has 32 open issues including macOS Keychain popups, Exa MCP timeouts, and provider breakage. Codex delegation is simpler and costs nothing extra.

```typescript
// .pi/extensions/codex-search.ts
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type } from "@sinclair/typebox";
import { execSync } from "child_process";

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "web_search",
    label: "Web Search",
    description: "Search the web using Codex CLI (uses subscription quota)",
    parameters: Type.Object({
      query: Type.String({ description: "Search query" }),
    }),
    async execute(toolCallId, params) {
      const escaped = params.query.replace(/"/g, '\\"');
      const result = execSync(
        `codex exec --search --full-auto "Search the web for: ${escaped}. Return only factual findings with source URLs. Do not write any code."`,
        { timeout: 30000, encoding: "utf-8" },
      );
      return { content: [{ type: "text", text: result }], details: {} };
    },
  });
}
```

**Tradeoffs:** ~3-8s latency per search (full Codex agent loop), consumes subscription tokens. If you hit quota limits, swap to MCP-direct (Brave Search or Perplexity MCP via `.mcp.json`) — Pi has native MCP support so it's just a config change, no extension needed.

**Alternatives:**

- `pi-web-access` (nicobailon, 378 stars) — feature-rich (video, PDF, GitHub cloning) but 32 open issues and macOS pain points
- MCP-direct: Brave Search MCP, Perplexity MCP, or Exa MCP via `.mcp.json` — lowest latency, but requires separate API keys/credits
- `badlogic/pi-skills/brave-search` (official, skill-only, requires Brave API key)

### TODO Tracking — `pi-todo-md`

712 downloads/wk · v0.4.0 (Apr 2026) · [npm](https://www.npmjs.com/package/pi-todo-md)

Manages a repo-local `TODO.md` file via a structured `todo_md` tool. File-based approach — tasks are inspectable, diffable, and survive session crashes.

**Key features:**
- Stable task IDs with hidden HTML comments
- Named sections, subtasks, priority levels, notes
- Interactive `/todos [section]` browser
- Injects compact active-task summary into agent turns (survives compaction)
- Finds nearest `TODO.md` or creates at git root

**Alternative:** `@juicesharp/rpiv-todo` (3.6K dl/wk) — closer to Claude Code's TodoWrite UX with overlay widget and 4-state task machine, but tasks are session-scoped (branch replay), not file-based. Higher adoption, less durable persistence. See [features/todo-tracking.md](features/todo-tracking.md) for full comparison.

### Extension Security Note

Extensions are TypeScript code that runs in the agent process. The community warns: "Prompt injections and vibe coded hacks are just one install away." Vet extension source code before installing, especially for packages with low star counts.

---

## 9. Pi-Native Features to Adopt

**Confidence: Verified** (features documented; adoption priorities based on community research)

These are capabilities Pi offers that **don't have Claude Code equivalents**. Ordered by adoption priority based on what real Pi users actually rely on daily.

### Day 1: Permission Gate (MANDATORY)

Pi runs in YOLO mode by default — no permission prompts, full system access. Real incidents of agents deleting entire projects have been reported. Before doing anything else, install a safety extension:

```bash
pi install npm:pi-permission-gate
```

Or use a sandbox solution: Agent Safehouse (macOS `sandbox-exec`), bubblewrap (Linux), or Docker.

### Day 1: Plan-First Skill File

The single most praised workflow pattern in the Pi community. Create a skill file that enforces structured planning before coding:

```
.pi/skills/plan-first/SKILL.md
```

This is separate from the Plannotator extension (§8) — it's a lightweight prompt-based approach. Reddit users report: "It actually follows what you say and does everything step by step without going off the rails."

### Week 1: Model Cycling (Ctrl+P)

Rapidly switch between models mid-conversation. Context carries over between models.

```json
{ "enabledModels": ["gpt-5.5", "claude-sonnet*", "gemini-3-flash"] }
```

Use `Shift+Tab` to cycle thinking levels without switching models. Power users run local models (Qwen3.6 35B) for cheap tasks and switch to GPT 5.5 / Claude for complex work.

### Week 1: Message Queue (Steering vs Follow-up)

More nuanced than Claude Code:

- **Enter** while agent works: queue a **steering** message (delivered after current tool calls finish, before next LLM call)
- **Alt+Enter**: queue a **follow-up** (delivered only after agent finishes all work)
- **Escape**: abort and restore queued messages
- **Alt+Up**: retrieve queued messages back to editor

### Week 1: File References (@)

Type `@` in the editor to fuzzy-search project files and include them in your message. More integrated than Claude Code's file references.

### Week 2-4: Session Branching & Tree (`/tree`)

Navigate your entire session history as a tree. Select any previous point and continue from there. All branches preserved in a single file. Useful for recovery from agent mistakes — `/fork` backtracks without losing successful earlier context.

- `Escape` twice — opens `/tree`
- Search by typing, fold/unfold branches
- Filter modes: default, no-tools, user-only, labeled-only, all
- Label entries as bookmarks with `Shift+L`

**Note:** Complementary to git, not a replacement. Session branching manages conversation state; git manages code artifacts. Reddit and blog discussions conspicuously don't mention branching in daily workflow — it's valuable for specific recovery scenarios.

### Week 2-4: Extension Stacking

Compose capabilities via CLI flags:

```bash
pi -e ./ext/footer.ts -e ./ext/subagents.ts -e ./ext/damage-control.ts
```

Start with 1-2 extensions. Common first stack: permission-gate + one workflow extension. Add complexity only as needed.

### Later: Widget System

Persistent UI above or below the editor. Becomes useful once you have subagents running — the `pi-subagents` extension uses widgets for real-time agent status display.

### Later: RPC Mode

Full programmatic control via JSONL protocol (14 commands, 12 event types). For embedding Pi in other applications or non-Node.js integrations, not daily interactive use.

### Later: Custom Compaction

Extensions can intercept `session_before_compact` to replace default summarization. Mario Zechner himself says "all compaction implementations are not good" — auto-compaction suffices for now.

### Later: Meta-Agent for Building Extensions

A "Pi Pi" meta-agent that delegates research to domain-specific expert agents (extensions, themes, skills, TUI, config) in parallel, synthesizes findings, and writes complete implementations. This is how you efficiently extend Pi going forward — instead of manually reading docs for each extension you build, the meta-agent queries the right experts and produces working code.

Reference implementation: IndyDevDan's `pi-vs-claude-code` repo (634-line extension). Adaptation notes: use local Pi docs (`etc/pi-docs/docs/`) instead of firecrawl fetches, start with 3 experts (ext/theme/skill), and consider using `pi-subagents` for the subprocess orchestration. See [features/meta-agent.md](features/meta-agent.md) for full architecture and porting strategy.

### Later: Mental Models / Per-Agent Context

Persistent files where each agent stores accumulated knowledge across sessions. An advanced multi-agent pattern from IndyDevDan's content — not relevant for solo developers. Revisit when running agent teams.

---

## 10. Feature Matrix

| Claude Code Feature    | Pi Equivalent                        | Effort | Status                  |
| ---------------------- | ------------------------------------ | ------ | ----------------------- |
| CLAUDE.md              | AGENTS.md (+ CLAUDE.md fallback)     | None   | Native                  |
| Skills                 | Skills (Agent Skills standard)       | Low    | Native                  |
| Slash commands         | Prompt templates                     | Low    | Native                  |
| Hooks (shell-based)    | Extension events (TypeScript)        | Medium | Native (richer)         |
| Permission system      | YOLO default; `pi-permission-gate`   | Low    | **Install**             |
| AskUserQuestion        | `pi-ask-user` (edlsh)                | Low    | **Install**             |
| Plan mode              | Custom extension (~80 lines)         | Low    | **Build**               |
| Subagents (Agent tool) | `pi-subagents` (nicobailon)          | Low    | **Install**             |
| WebSearch              | Codex CLI delegation (~15 lines)     | Low    | **Build**               |
| TodoWrite/TaskCreate   | `pi-todo-md` (file-based)            | Low    | **Install**             |
| MCP servers            | Not supported; use skills/extensions | Varies | Not available           |
| Multi-agent teams      | `pi-subagents` chains/parallel       | Medium | **Install** + configure |
| Status line            | Footer customization (richer)        | Low    | Native                  |
| Background agents      | Not built in; use tmux               | Low    | Workaround              |
| Git checkpointing      | Extension or session branching       | Low    | Partial native          |

---

## 11. Quick Reference

### Directory Structure

```
~/.pi/agent/
├── settings.json          # Global settings
├── AGENTS.md              # Global context (= CLAUDE.md)
├── SYSTEM.md              # System prompt override (optional)
├── APPEND_SYSTEM.md       # System prompt append (optional)
├── keybindings.json       # Custom keybindings
├── models.json            # Custom providers/models
├── sessions/              # Session files (auto-managed)
├── extensions/            # Global extensions
├── skills/                # Global skills
├── prompts/               # Global prompt templates
└── themes/                # Custom themes

.pi/                       # Project-level (same structure minus sessions)
├── settings.json
├── AGENTS.md
├── extensions/
├── skills/
├── prompts/
└── themes/
```

### Essential Keyboard Shortcuts

| Key            | Action                       |
| -------------- | ---------------------------- |
| `Ctrl+C`       | Clear editor                 |
| `Ctrl+C` twice | Quit                         |
| `Escape`       | Cancel/abort                 |
| `Escape` twice | Open `/tree`                 |
| `Ctrl+L`       | Model selector               |
| `Ctrl+P`       | Cycle models                 |
| `Shift+Tab`    | Cycle thinking level         |
| `Ctrl+O`       | Collapse/expand tool output  |
| `Ctrl+T`       | Collapse/expand thinking     |
| `Alt+Enter`    | Queue follow-up message      |
| `@`            | File reference fuzzy search  |
| `!command`     | Run bash, send output to LLM |
| `!!command`    | Run bash, don't send to LLM  |

### Essential Commands

| Command       | Description                      |
| ------------- | -------------------------------- |
| `/model`      | Switch models                    |
| `/settings`   | Settings UI                      |
| `/tree`       | Session tree navigator           |
| `/compact`    | Manual compaction                |
| `/new`        | New session                      |
| `/resume`     | Browse sessions                  |
| `/fork`       | Fork from previous message       |
| `/export`     | Export to HTML                   |
| `/reload`     | Reload extensions/skills/prompts |
| `/skill:name` | Load a skill                     |
