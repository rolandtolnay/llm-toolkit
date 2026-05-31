# Agent Resource Frontmatter Reference (pi ↔ Claude Code)

How we write frontmatter for agent-adjacent resources that may be used by **pi**, **Claude Code**, or both: subagents, skills, and prompt templates.

The important distinction: **pi subagent files are parsed by pi-subagents' line-based parser**, while **pi skills and prompt templates are parsed as YAML** by pi core. Treat them differently.

## Resource sharing rule

| Artifact | How it's shared | Why |
|----------|-----------------|-----|
| **Skills** | **Symlink** `.claude/skills/<name>` → `.agents/skills/<name>` (or `~/.claude/skills` → `~/.pi/agent/skills`) | Skill content is runtime-agnostic markdown. One source of truth. |
| **Subagents** | **Copy** — two real files with adapted frontmatter | Frontmatter fields and value formats differ per runtime, so they can't be symlinked. |
| **Prompt templates** | pi-only markdown under `~/.pi/agent/prompts/` or project `.pi/prompts/` | Claude Code does not use pi prompt-template frontmatter. |

Locations:
- pi subagents: `~/.pi/agent/agents/<name>.md` (user) or `<project>/.agents/agents/<name>.md` / `<project>/.pi/agents/<name>.md` (project)
- Claude Code subagents: `~/.claude/agents/<name>.md` (user) or `<project>/.claude/agents/<name>.md` (project)
- pi skills: `~/.pi/agent/skills/<name>/SKILL.md` or `<project>/.pi/skills/<name>/SKILL.md`
- pi prompt templates: `~/.pi/agent/prompts/<name>.md` or `<project>/.pi/prompts/<name>.md`

## Parser rule

| Resource | Parser | Practical rule |
|----------|--------|----------------|
| pi subagent frontmatter | line-based `key: value` parser in pi-subagents | Keep values one-line. Lists such as `skills` must be inline comma-separated. |
| Claude Code subagent frontmatter | YAML | Use normal YAML lists where Claude expects them. |
| pi skill frontmatter | YAML | Quote or block-scalar any prose containing YAML metacharacters. |
| pi prompt-template frontmatter | YAML | Quote `argument-hint` values, especially bracket-style hints. |

## YAML quoting rule for skills and prompt templates

Because skills and prompt templates use YAML frontmatter, prose is not always safe as an unquoted scalar.

Quote or use a block scalar when a value contains YAML syntax such as:

- `: ` inside a sentence, e.g. `codebase: bottom line first`
- bracket-style hints, e.g. `[topic, or leave blank]`
- flow mappings, e.g. `[optional: files]`
- leading `{`, `[`, `&`, `*`, `!`, `|`, `>`, `@`, or backtick-like syntax that YAML may reinterpret

Correct:

```yaml
---
description: >-
  Explain a code change plainly for an engineer who knows software but not this codebase: bottom line first, then each improvement as before/after with why it matters.
argument-hint: "[optional: commit, PR, branch, or files]"
---
```

Incorrect:

```yaml
---
description: Explain a code change plainly for an engineer who knows software but not this codebase: bottom line first.
argument-hint: [optional: commit, PR, branch, or files]
---
```

Why it fails: `codebase: bottom line` is parsed as nested mapping syntax, and `[optional: ...]` is parsed as a flow collection/mapping instead of a display string. Even bracket values without `:` parse as arrays, not strings; pi prompt templates expect `argumentHint?: string`.

## Subagent field mapping

| Concern | pi | Claude Code |
|---------|----|-----|
| Tools | lowercase: `read, write, edit, bash, grep, find, ls` | Capitalized: `Read, Write, Edit, Bash, Grep, Glob` |
| Model tier | `model: openai-codex/gpt-5.5` + `thinking: high\|xhigh` | `model: opus\|sonnet\|haiku` (optionally `effort: high\|xhigh\|max`) |
| Preloaded skills | `skills: a, b, c` (inline, comma-separated) | `skills:` YAML block list |
| System prompt | `systemPromptMode: replace` | (no equivalent — body always replaces) |
| Context inheritance | `inheritProjectContext`, `inheritSkills`, `defaultContext: fresh\|fork` | (no equivalent) |
| Display/UX | — | `color`, `permissionMode`, `maxTurns`, etc. |

Drop fields the other runtime doesn't understand. pi tolerates unknown keys in subagent files, but keep its frontmatter clean.

## The subagent gotcha that will silently break you

**pi subagent frontmatter is line-based, not YAML** (`pi-subagents/src/agents/frontmatter.ts`). Each `key: value` line becomes a raw string; indented `- item` lines do **not** parse. So a multi-skill value must be **inline comma-separated** on the pi side:

```yaml
# pi — correct
skills: next-best-practices, vercel-react

# pi — silently gives the agent zero skills
skills:
  - next-best-practices
```

pi reads `skill` or `skills` and splits it on commas. Claude Code uses real YAML, so its copy **must** use the block list. Same field name, opposite required format.

## Skill injection

Both runtimes inject the **full skill body** (frontmatter stripped) into the subagent's context at startup — pi via `skill:`/`skills:`, Claude Code via `skills:`. A subagent can name the skill as its authoritative rubric and assume it's present; it does not need to read the skill file from disk. Claude Code subagents can also invoke unlisted skills via the `Skill` tool if it's in `tools`, but preloading is preferred for a fixed rubric.

## Naming

- **Global/shared reviewers** are prefixed on the Claude side: pi `general-reviewer` ↔ Claude `pi-general-reviewer`. The project's `.agents/.code-review.json` references the names as the runtime that reads it expects.
- **Project-local agents** keep the **same name** in both files (e.g. `ms-next-code-quality`), so config referencing them needs no per-runtime variant.

## Worked example

`ms-next-code-quality` (first-things-first) — identical body, two frontmatters:

```yaml
# .agents/agents/ms-next-code-quality.md (pi)
tools: read, write, edit, bash, grep, find, ls
model: openai-codex/gpt-5.5
thinking: high
systemPromptMode: replace
inheritProjectContext: true
inheritSkills: false
skills: next-best-practices, vercel-react-best-practices, vercel-composition-patterns
defaultContext: fresh
```

```yaml
# .claude/agents/ms-next-code-quality.md (Claude Code)
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
color: cyan
skills:
  - next-best-practices
  - vercel-react-best-practices
  - vercel-composition-patterns
```

Reference pair using injected rubric: `~/.pi/agent/agents/nuclear-reviewer.md` (`skill: thermo-nuclear-code-quality-review`) ↔ `~/.claude/agents/pi-nuclear-reviewer.md` (`skills: [thermo-nuclear-code-quality-review]`).

## Checklist for a new dual-runtime subagent

1. Write the body once. Decide which skills it preloads.
2. Write the pi file: lowercase tools, `openai-codex/gpt-5.5` + `thinking`, pi context fields, **inline** `skills`.
3. Write the Claude file (a real copy, not a symlink): Capitalized tools, `opus`/`sonnet`/`haiku`, **YAML-block** `skills`.
4. Symlink any new skills into `.claude/skills/` (and `~/.claude/skills/` for user-scoped).
5. Verify the bodies are identical and every referenced skill resolves in both runtimes.

## Checklist for pi skills and prompt templates

1. Treat frontmatter as YAML, not plain text.
2. Quote bracket-style `argument-hint` values: `"[topic or leave blank]"`.
3. Use `description: >-` for long prose descriptions, especially if they contain `: `.
4. Parse-check changed frontmatter before reloading pi.

**Maintenance:** dual-runtime subagent files are copies. Body edits must be mirrored by hand. Skills don't have this cost when symlinked, but their YAML frontmatter still must be valid for both runtimes that read it.
