# Pi Quickstart (from Claude Code)

Step-by-step migration to Pi with GPT 5.5. Follow in order — each step builds on the previous.

---

## Step 1: Install Pi + Codex CLI

```bash
npm install -g @mariozechner/pi-coding-agent
npm install -g @openai/codex               # for web search delegation
```

## Step 2: Authenticate

```bash
# Pi — OpenAI API key
export OPENAI_API_KEY=sk-...

# Codex — ChatGPT subscription (for web search)
codex login
```

## Step 3: Global Settings

```bash
mkdir -p ~/.pi/agent
```

Create `~/.pi/agent/settings.json`:

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
  "enabledModels": ["gpt-5.5", "gpt-5.5-mini", "claude-sonnet*", "gemini-3*"]
}
```

## Step 4: AGENTS.md (replaces CLAUDE.md)

Create `~/.pi/agent/AGENTS.md`:

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

Per-project: Pi reads `AGENTS.md` from cwd and parent dirs (like CLAUDE.md). It also reads `CLAUDE.md` as fallback — existing project files work without renaming.

## Step 5: Install Permission Gate (MANDATORY)

Pi runs in YOLO mode by default — no permission prompts. Agents have deleted entire projects.

```bash
pi install npm:pi-permission-gate
```

## Step 6: Install Extensions

```bash
pi install npm:pi-subagents        # subagents (Agent tool equivalent)
pi install npm:pi-ask-user         # AskUserQuestion equivalent
pi install npm:pi-todo-md          # TodoWrite/TaskCreate equivalent
```

## Step 7: Build Web Search Extension

Create `~/.pi/agent/extensions/codex-search.ts`:

```typescript
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
        { timeout: 30000, encoding: "utf-8" }
      );
      return { content: [{ type: "text", text: result }], details: {} };
    },
  });
}
```

Uses your ChatGPT subscription — no separate API keys. ~3-8s per search. If you hit quota limits later, swap to Brave Search MCP via `.mcp.json`.

## Step 8: Port Skills

Claude Code skills → Pi skills. The format is nearly identical:

```
# Claude Code                    # Pi
commands/my-skill.md        →    .pi/skills/my-skill/SKILL.md
~/.claude/commands/foo.md   →    ~/.pi/agent/skills/foo/SKILL.md
```

For each skill:
1. Create directory: `.pi/skills/<name>/`
2. Move content to `SKILL.md` inside it
3. Add frontmatter: `name` (must match dir) + `description`
4. Strip Claude-specific tool refs (`Agent`, `TodoWrite` → use `pi-subagents`, `pi-todo-md` tools instead)

Invoke with `/skill:name` or let the model auto-load when task matches the description.

## Step 9: Port Slash Commands

Simple prompt-only commands become prompt templates:

```
# Claude Code                              # Pi
commands/review.md                    →    .pi/prompts/review.md
~/.claude/commands/quick-check.md     →    ~/.pi/agent/prompts/quick-check.md
```

Add frontmatter and use `$1`, `$@` for arguments:

```markdown
---
description: Review code for bugs and security
argument-hint: "<file-or-area>"
---
Review this code for bugs, security issues, and performance.
Focus on: $1
```

Invoke with `/review src/auth.ts`.

## Step 10: First Run

```bash
cd your-project
pi
```

Verify everything loaded:
- Permission gate should prompt on first write/bash
- Type `/` and tab — your skills and prompts should appear
- Ask it to search something — `web_search` tool should invoke Codex
- Ask it to create a todo — `todo_md` tool should create TODO.md

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+P` | Cycle models |
| `Shift+Tab` | Cycle thinking level |
| `Ctrl+L` | Model selector |
| `@` | File reference (fuzzy search) |
| `Enter` (while agent works) | Queue steering message |
| `Alt+Enter` | Queue follow-up message |
| `Escape` | Abort |
| `Escape` × 2 | Session tree (`/tree`) |
| `Ctrl+O` | Collapse/expand tool output |
| `!command` | Run bash, send output to LLM |

## Essential Commands

| Command | Description |
|---------|-------------|
| `/model` | Switch model |
| `/plan` | Toggle plan mode (if you build the extension) |
| `/tree` | Session tree navigator |
| `/compact` | Manual compaction |
| `/new` | New session |
| `/resume` | Browse sessions |
| `/fork` | Fork from previous message |
| `/reload` | Reload extensions/skills/prompts |
| `/skill:name` | Load a skill |

## What's NOT Ported (and What to Do)

| Claude Code Feature | Pi Status |
|---|---|
| Hooks (shell scripts) | Rewrite as extension events (TypeScript). `tool_call` event = `PreToolUse`, `tool_result` = `PostToolUse`. |
| Plan mode | Build ~80 line extension or use plan-first skill file. See [onboarding.md §8](onboarding.md#8-features-to-install). |
| Background agents | Use tmux or `pi-subagents` async mode. |
| MCP servers | Pi has native MCP support via `.mcp.json`. |
| Memory system | No equivalent. Use AGENTS.md or mental-models pattern for persistent context. |
| Git checkpointing | Use session branching (`/fork`, `/tree`) + normal git. |

## Directory Structure Reference

```
~/.pi/agent/
├── settings.json              # Global settings
├── AGENTS.md                  # Global context (= CLAUDE.md)
├── extensions/                # Global extensions
│   └── codex-search.ts        # Web search (Step 7)
├── skills/                    # Global skills (ported from ~/.claude/commands/)
├── prompts/                   # Global prompt templates
└── mcp.json                   # MCP server config (if using MCP)

<project>/
├── .pi/
│   ├── settings.json          # Project overrides
│   ├── AGENTS.md              # Project context
│   ├── extensions/            # Project extensions
│   ├── skills/                # Project skills
│   └── prompts/               # Project prompts
├── AGENTS.md                  # Also discovered (root-level)
└── CLAUDE.md                  # Fallback — still read by Pi
```

## Further Reading

- [Full onboarding guide](onboarding.md) — detailed reference for all sections
- [Extension deep audit](../../Documents/Research/2026-04-26-pi-migration-outstanding/05-extension-deep-audit.md) — why these extensions were chosen
- [GPT 5.5 prompting research](../../Documents/Research/2026-04-26-pi-migration-outstanding/01-prompt-engineering-gpt55.md) — behavioral differences from Claude
