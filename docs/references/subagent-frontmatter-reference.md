# Subagent Frontmatter Reference (pi ↔ Claude Code)

How we make one subagent run under both the **pi** runtime and **Claude Code**. The body is shared; only the frontmatter is runtime-specific.

## The rule

| Artifact | How it's shared | Why |
|----------|-----------------|-----|
| **Skills** | **Symlink** `.claude/skills/<name>` → `.agents/skills/<name>` (or `~/.claude/skills` → `~/.pi/agent/skills`) | Skill content is runtime-agnostic markdown. One source of truth. |
| **Subagents** | **Copy** — two real files with adapted frontmatter | Frontmatter fields and value formats differ per runtime, so they can't be symlinked. |

Locations:
- pi: `~/.pi/agent/agents/<name>.md` (user) or `<project>/.agents/agents/<name>.md` (project)
- Claude Code: `~/.claude/agents/<name>.md` (user) or `<project>/.claude/agents/<name>.md` (project)

## Field mapping

| Concern | pi | Claude Code |
|---------|----|-----|
| Tools | lowercase: `read, write, edit, bash, grep, find, ls` | Capitalized: `Read, Write, Edit, Bash, Grep, Glob` |
| Model tier | `model: openai-codex/gpt-5.5` + `thinking: high\|xhigh` | `model: opus\|sonnet\|haiku` (optionally `effort: high\|xhigh\|max`) |
| Preloaded skills | `skills: a, b, c` (inline, comma-separated) | `skills:` YAML block list |
| System prompt | `systemPromptMode: replace` | (no equivalent — body always replaces) |
| Context inheritance | `inheritProjectContext`, `inheritSkills`, `defaultContext: fresh\|fork` | (no equivalent) |
| Display/UX | — | `color`, `permissionMode`, `maxTurns`, etc. |

Drop fields the other runtime doesn't understand. pi tolerates unknown keys (stored as inert extras) but keep its frontmatter clean.

## The one gotcha that will silently break you

**pi's frontmatter parser is line-based, not YAML** (`pi-subagents/src/agents/frontmatter.ts`). Each `key: value` line becomes a raw string; indented `- item` lines do **not** parse. So a multi-skill value must be **inline comma-separated** on the pi side:

```yaml
# pi — correct                          # pi — SILENTLY gives the agent ZERO skills
skills: next-best-practices, vercel-react    skills:
                                               - next-best-practices
```

pi reads `skill` or `skills` and `.split(",")` it (`agents.ts`). Claude Code uses real YAML, so its copy **must** use the block list. Same field name, opposite required format.

## Skill injection

Both runtimes inject the **full skill body** (frontmatter stripped) into the subagent's context at startup — pi via `skill:`/`skills:`, Claude Code via `skills:`. A subagent can name the skill as its authoritative rubric and assume it's present; it does not need to read the skill file from disk. (Claude Code subagents can also invoke unlisted skills via the `Skill` tool if it's in `tools`, but preloading is preferred for a fixed rubric.)

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

**Maintenance:** the two agent files are copies. Body edits must be mirrored by hand. Skills don't have this cost (symlinked).
