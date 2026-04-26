# Claude Code to Pi: Onboarding Guide

This guide covers how to get productive in Pi, organized by dependency order — what you need first.

**Confidence levels:**
- **Verified** — Directly documented in Pi's official docs
- **Inferred** — Logical from the API surface, but no reference implementation seen
- **Needs validation** — Likely works but needs hands-on testing

---

## Table of Contents

1. [Installation & First Run](#1-installation--first-run)
2. [Context Files (AGENTS.md)](#2-context-files-agentsmd)
3. [Settings](#3-settings)
4. [Skills (Porting Claude Code Skills)](#4-skills)
5. [Prompt Templates (Porting Slash Commands)](#5-prompt-templates)
6. [Extensions Overview](#6-extensions-overview)
7. [Hooks via Extensions](#7-hooks-via-extensions)
8. [Features to Build](#8-features-to-build)
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

| Location | Scope |
|----------|-------|
| `~/.pi/agent/AGENTS.md` | Global (all projects) |
| Parent directories (walking up from cwd) | Inherited |
| Current directory `./AGENTS.md` | Project |

### Migration Steps

1. **Global instructions**: Copy `~/.claude/CLAUDE.md` to `~/.pi/agent/AGENTS.md`
2. **Project instructions**: Either rename `CLAUDE.md` to `AGENTS.md` or keep both — Pi reads `CLAUDE.md` as fallback
3. **Content adjustments**: If your CLAUDE.md references Claude-specific features (hooks config, permissions, etc.), strip those for the Pi version

### System Prompt Override

For deeper customization beyond AGENTS.md:

| File | Effect |
|------|--------|
| `.pi/SYSTEM.md` | **Replaces** the default 200-token system prompt entirely |
| `.pi/APPEND_SYSTEM.md` | **Appends** to the default system prompt |
| `~/.pi/agent/SYSTEM.md` | Global system prompt override |
| `~/.pi/agent/APPEND_SYSTEM.md` | Global system prompt append |

This is more powerful than Claude Code — you can fully replace the system prompt, not just add context.

### Disable Context Files

```bash
pi --no-context-files    # or -nc
```

---

## 3. Settings

**Confidence: Verified**

### File Locations

| Location | Scope |
|----------|-------|
| `~/.pi/agent/settings.json` | Global |
| `.pi/settings.json` | Project (overrides global via nested merge) |

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

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Max 64 chars. Lowercase a-z, 0-9, hyphens. Must match directory name. |
| `description` | Yes | Max 1024 chars. Determines when the agent auto-loads it. |
| `license` | No | License reference |
| `compatibility` | No | Environment requirements |
| `disable-model-invocation` | No | When `true`, only manual `/skill:name` works |
| `allowed-tools` | No | Pre-approved tools (experimental) |

### Discovery Locations

| Location | Notes |
|----------|-------|
| `~/.pi/agent/skills/` | Global |
| `~/.agents/skills/` | Global (Agent Skills standard path) |
| `.pi/skills/` | Project |
| `.agents/skills/` (cwd + ancestors) | Project + parent dirs |
| Pi packages | Via `pi install` |

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
<!-- ~/.pi/agent/prompts/review.md -->
---
description: Review code for bugs, security, and performance
argument-hint: "<file-or-area>"
---
Review this code for bugs, security issues, and performance problems.
Focus on: $1
Additional context: ${@:2}
```

### Argument Syntax

| Syntax | Meaning |
|--------|---------|
| `$1`, `$2`, ... | Positional arguments |
| `$@` or `$ARGUMENTS` | All arguments joined |
| `${@:N}` | Arguments from Nth position |
| `${@:N:L}` | L arguments starting at N |

### Discovery Locations

| Location | Notes |
|----------|-------|
| `~/.pi/agent/prompts/` | Global |
| `.pi/prompts/` | Project |
| Pi packages | Via `pi install` |

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

| Location | Notes |
|----------|-------|
| `~/.pi/agent/extensions/*.ts` | Global |
| `~/.pi/agent/extensions/*/index.ts` | Global (directory-based) |
| `.pi/extensions/*.ts` | Project |
| `.pi/extensions/*/index.ts` | Project (directory-based) |

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

| Method | Purpose |
|--------|---------|
| `pi.on(event, handler)` | Subscribe to lifecycle events |
| `pi.registerTool(def)` | Register LLM-callable tools |
| `pi.registerCommand(name, opts)` | Register `/commands` |
| `pi.registerShortcut(key, opts)` | Register keyboard shortcuts |
| `pi.sendMessage(msg)` | Inject messages into session |
| `pi.appendEntry(type, data)` | Persist extension state |
| `pi.registerMessageRenderer(type, renderer)` | Custom message display |
| `pi.registerProvider(name, config)` | Register model providers |
| `pi.getActiveTools() / setActiveTools()` | Manage tool activation |
| `pi.events` | Shared bus for inter-extension communication |

### Hot Reload

Use `/reload` to reload extensions without restarting. Emits `session_shutdown` for old instance, reloads, emits `session_start(reason: "reload")`.

---

## 7. Hooks via Extensions

**Confidence: Verified**

Pi's hook system is implemented through extension events. It's **more granular** than Claude Code's hooks but requires TypeScript instead of shell scripts.

### All Available Events

#### Session Lifecycle
| Event | When | Can Block? |
|-------|------|------------|
| `session_start` | Session starts/loads/reloads | No |
| `session_shutdown` | Before teardown | No |
| `session_before_switch` | Before `/new` or `/resume` | Yes |
| `session_before_fork` | Before `/fork` or `/clone` | Yes |
| `session_before_compact` | Before compaction | Can provide custom summary |
| `session_compact` | On compaction | No |
| `resources_discover` | After session_start | Can contribute resource paths |

#### Agent Lifecycle
| Event | When | Can Block? |
|-------|------|------------|
| `before_agent_start` | After user submits, before LLM | Can inject messages, modify system prompt |
| `agent_start` | Once per user prompt | No |
| `agent_end` | After LLM finishes | No |
| `turn_start` | Each LLM response + tool call cycle | No |
| `turn_end` | After tools executed | No |

#### Tool Execution
| Event | When | Can Block? |
|-------|------|------------|
| `tool_execution_start` | Before tool runs | No |
| `tool_execution_update` | During execution (streaming) | No |
| `tool_execution_end` | After execution | No |
| `tool_call` | After start, before execute | **Yes — can block** with `{ block: true, reason }`. Args are mutable. |
| `tool_result` | After execute, before message | Can modify result (middleware chain) |

#### Messages
| Event | When | Can Block? |
|-------|------|------------|
| `message_start` | Message lifecycle start | No |
| `message_update` | Streaming updates | No |
| `message_end` | Message lifecycle end | No |

#### User Input
| Event | When | Can Block? |
|-------|------|------------|
| `input` | After command check, before expansion | Can transform or handle |
| `user_bash` | On `!` or `!!` commands | Can intercept |

#### Provider
| Event | When | Can Block? |
|-------|------|------------|
| `before_provider_request` | Before HTTP request | Can replace payload |
| `after_provider_response` | After HTTP response | No |
| `model_select` | On model change | No |

#### Context
| Event | When | Can Block? |
|-------|------|------------|
| `context` | Before each LLM call | Can filter/modify messages (non-destructive) |

### Example: Blocking Dangerous Commands (like Claude Code's PreToolUse hook)

```typescript
export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName === "bash") {
      const cmd = event.input?.command || "";
      const dangerous = ["rm -rf", "sudo", "DROP TABLE"];
      if (dangerous.some(d => cmd.includes(d))) {
        const ok = await ctx.ui.confirm(
          "Dangerous Command",
          `Allow: ${cmd}?`
        );
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

| Claude Code Hook | Pi Equivalent |
|-----------------|---------------|
| `PreToolUse` | `tool_call` event (can block, mutate args) |
| `PostToolUse` | `tool_result` event (can modify result) |
| `Notification` | `agent_end` event |
| `Stop` | `agent_end` event |
| `SubagentStop` | No direct equivalent (subagents are custom) |

**Key difference**: Claude Code hooks are shell scripts in `settings.json`. Pi hooks are TypeScript in extension files. More powerful, but requires writing TypeScript.

---

## 8. Features to Build

These are Claude Code capabilities that Pi doesn't include — you build them as extensions (or find existing packages). Each has a dedicated research/implementation brief.

| Feature | Description | Brief |
|---------|-------------|-------|
| **Ask User Question** | Tool for the model to pause and ask the user a question mid-task | [features/ask-user-question.md](features/ask-user-question.md) |
| **Plan Mode** | Read-only planning phase before execution, with user approval | [features/plan-mode.md](features/plan-mode.md) |
| **Subagents** | Spawn independent child agents for parallel/specialized work | [features/subagents.md](features/subagents.md) |
| **Web Search** | Search the web and fetch pages during a task | [features/web-search.md](features/web-search.md) |

**Approach for each:** Research whether an existing Pi package or community extension already provides it. If not, build a custom extension. See [OUTSTANDING.md](OUTSTANDING.md) for open research questions.

---

## 9. Pi-Native Features to Adopt

These are capabilities Pi offers that **don't have Claude Code equivalents**. Worth learning rather than trying to replicate your CC workflow.

### Session Branching & Tree (`/tree`)

Navigate your entire session history as a tree. Select any previous point and continue from there. All branches preserved in a single file. **This replaces the need for git-based checkpointing** in many cases.

- `Escape` twice — opens `/tree`
- Search by typing, fold/unfold branches
- Filter modes: default, no-tools, user-only, labeled-only, all
- Label entries as bookmarks with `Shift+L`

### Model Cycling (Ctrl+P)

Rapidly switch between models mid-conversation. Configure which models to cycle through:

```json
{ "enabledModels": ["gpt-5.5", "claude-sonnet*", "gemini-3-flash"] }
```

Use `Shift+Tab` to cycle thinking levels without switching models.

### Message Queue (Steering vs Follow-up)

More nuanced than Claude Code:
- **Enter** while agent works: queue a **steering** message (delivered after current tool calls finish, before next LLM call)
- **Alt+Enter**: queue a **follow-up** (delivered only after agent finishes all work)
- **Escape**: abort and restore queued messages
- **Alt+Up**: retrieve queued messages back to editor

### Extension Stacking

Compose capabilities via CLI flags:
```bash
pi -e ./ext/footer.ts -e ./ext/subagents.ts -e ./ext/damage-control.ts
```

Build extensions in isolation, stack the ones you need for each task.

### Widget System

Persistent UI above or below the editor. Use for:
- Active task display
- Subagent status
- Custom context display
- Tool counters

### RPC Mode

Full programmatic control via JSONL protocol. Build tools that orchestrate Pi instances from other languages or processes.

### File References (@)

Type `@` in the editor to fuzzy-search project files and include them in your message. More integrated than Claude Code's file references.

---

## 10. Feature Matrix

| Claude Code Feature | Pi Equivalent | Effort | Status |
|---|---|---|---|
| CLAUDE.md | AGENTS.md (+ CLAUDE.md fallback) | None | Native |
| Skills | Skills (Agent Skills standard) | Low | Native |
| Slash commands | Prompt templates | Low | Native |
| Hooks (shell-based) | Extension events (TypeScript) | Medium | Native (richer) |
| Permission system | YOLO default; build via extensions | Medium | Build it |
| AskUserQuestion | `ctx.ui.input/select/confirm` | Medium | Build it |
| Plan mode | Extension or file-based | Medium | Build it |
| Subagents (Agent tool) | RPC subprocess or SDK | High | Build it |
| WebSearch | Skill or extension | Medium | Build it |
| TodoWrite/TaskCreate | Extension or PLAN.md file | Medium | Build it |
| MCP servers | Not supported; use skills/extensions | Varies | Not available |
| Multi-agent teams | Extension with RPC orchestration | High | Build it |
| Status line | Footer customization (richer) | Low | Native |
| Background agents | Not built in; use tmux | Low | Workaround |
| Git checkpointing | Extension or session branching | Low | Partial native |

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

| Key | Action |
|-----|--------|
| `Ctrl+C` | Clear editor |
| `Ctrl+C` twice | Quit |
| `Escape` | Cancel/abort |
| `Escape` twice | Open `/tree` |
| `Ctrl+L` | Model selector |
| `Ctrl+P` | Cycle models |
| `Shift+Tab` | Cycle thinking level |
| `Ctrl+O` | Collapse/expand tool output |
| `Ctrl+T` | Collapse/expand thinking |
| `Alt+Enter` | Queue follow-up message |
| `@` | File reference fuzzy search |
| `!command` | Run bash, send output to LLM |
| `!!command` | Run bash, don't send to LLM |

### Essential Commands

| Command | Description |
|---------|-------------|
| `/model` | Switch models |
| `/settings` | Settings UI |
| `/tree` | Session tree navigator |
| `/compact` | Manual compaction |
| `/new` | New session |
| `/resume` | Browse sessions |
| `/fork` | Fork from previous message |
| `/export` | Export to HTML |
| `/reload` | Reload extensions/skills/prompts |
| `/skill:name` | Load a skill |
