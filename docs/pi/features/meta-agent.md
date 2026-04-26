# Meta-Agent: Pi Extension Builder

## What This Is

A meta-agent ("Pi Pi") that helps you build new Pi extensions, themes, skills, agents, and prompts. It delegates research to domain-specific expert agents in parallel, synthesizes findings, and writes complete implementations.

This is a post-migration investment — build it after the core setup is working. It's what lets you extend and customize Pi efficiently going forward.

## Reference Implementation

IndyDevDan's `pi-vs-claude-code` repo (cloned at `etc/pi-advanced/pi-vs-claude-code/`). Key files:

| File | Purpose |
|------|---------|
| `extensions/pi-pi.ts` (634 lines) | Core extension: `query_experts` tool, grid dashboard widget, expert lifecycle |
| `.pi/agents/pi-pi/pi-orchestrator.md` | Primary agent prompt: research → build workflow |
| `.pi/agents/pi-pi/<name>-expert.md` | One agent definition per domain expert |
| `.pi/agents/teams.yaml` | Team composition (which experts to include) |

## Architecture

### Two-phase workflow

1. **Research (parallel):** Orchestrator calls `query_experts` with an array of `{expert, question}` pairs. All experts spawn as concurrent `pi` subprocesses (`--no-session --no-extensions --mode json`). Each expert has read-only tools and domain-specific knowledge.
2. **Build (sequential):** Orchestrator synthesizes expert findings and writes actual files using write/edit/bash tools. Experts cannot modify files — only the orchestrator can.

### Domain experts

| Expert | Domain | Pi docs reference |
|--------|--------|-------------------|
| `ext-expert` | Extensions — registerTool(), events, TypeBox, custom rendering | `extensions.md` |
| `theme-expert` | Themes — 51 color tokens, JSON format, hot reload | `themes.md` |
| `skill-expert` | SKILL.md format, frontmatter, directory structure | `skills.md` |
| `config-expert` | Settings, providers, models, packages, keybindings | `settings.md`, `providers.md`, `models.md` |
| `tui-expert` | TUI components, widgets, overlays, keyboard input | `tui.md` |
| `prompt-expert` | Prompt templates, argument syntax | `prompt-templates.md` |
| `agent-expert` | Agent definitions, teams.yaml, orchestration patterns | (convention-based) |

### Dashboard widget

Live grid showing each expert's status (idle/researching/done/error), current question, elapsed time, and query count. Renders as colored cards in a configurable grid layout.

## Adaptation Notes

### Use local docs instead of firecrawl

The reference implementation has each expert fetch fresh docs from GitHub via firecrawl/curl on every query:

```bash
firecrawl scrape https://raw.githubusercontent.com/.../extensions.md -f markdown -o /tmp/pi-ext-docs.md
```

This is unnecessary overhead. We already have the latest Pi docs locally at `etc/pi-docs/docs/`. Adapt each expert's "First Action" to read from the local path instead:

```
Read etc/pi-docs/docs/extensions.md for the latest Pi extensions reference.
```

Pros: instant (no network), no firecrawl dependency, works offline.
Cons: docs could go stale — run a periodic `git pull` on the pi-mono docs or re-download when Pi updates. Pi releases are infrequent enough (~weekly) that this is fine.

### Simplifications for our setup

- **Fewer experts initially:** Start with `ext-expert`, `theme-expert`, and `skill-expert` — the three you'll use most. Add others as needed.
- **Use pi-subagents instead of custom subprocess spawning:** The reference implementation rolls its own subprocess management (634 lines). If `pi-subagents` (nicobailon) supports parallel mode with result collection, use that instead of reimplementing the subprocess orchestration.
- **Combine config/prompt/agent experts into one:** These are simple enough that a single "conventions-expert" with access to all three doc files would suffice.

### What the orchestrator needs

The orchestrator agent definition should specify:
- Full read/write/edit/bash tools (it writes the actual code)
- Access to `query_experts` tool (registered by the extension)
- System prompt that enforces: research first, then build, no stubs
- File location conventions for where to write extensions, themes, skills, etc.

## What It Can Build

- **Extensions** (.ts) — custom tools, event hooks, commands, UI components
- **Themes** (.json) — color schemes with all 51 tokens
- **Skills** (SKILL.md directories) — capability packages with scripts and references
- **Prompt templates** (.md) — reusable prompts with argument syntax
- **Agent definitions** (.md) — agent personas with YAML frontmatter
- **Settings** (settings.json) — configuration files

## Status: Researched — Build After Core Migration
