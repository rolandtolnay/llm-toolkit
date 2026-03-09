# Frontmatter Reference

Complete reference for SKILL.md YAML frontmatter fields.

## Minimal Format

```yaml
---
name: my-skill
description: What it does. Use when trigger conditions.
---

Skill instructions here...
```

## All Fields

| Field | Required | Description |
|---|---|---|
| `name` | No (uses dir name) | kebab-case, max 64 chars |
| `description` | Recommended | What + when + triggers (max 1024 chars) |
| `argument-hint` | No | Hint for autocomplete, e.g. `[issue-number]` |
| `disable-model-invocation` | No | `true` = only user can invoke via `/name` |
| `user-invocable` | No | `false` = hide from `/` menu, only Claude invokes |
| `allowed-tools` | No | Tools allowed without asking permission |
| `model` | No | Model to use when skill is active |
| `context` | No | `fork` = run in a subagent |
| `agent` | No | Subagent type when `context: fork` is set |
| `hooks` | No | Hooks scoped to skill lifecycle |

## Name Rules

- kebab-case only: lowercase letters, numbers, hyphens
- Max 64 characters
- Should match directory name
- No "claude" or "anthropic" (reserved)

## Description Rules

- Max 1024 characters
- No XML angle brackets `<` `>` (security: frontmatter appears in system prompt)
- No first/second person ("I", "you")
- Include both what and when

## String Substitutions

| Variable | Description |
|---|---|
| `$ARGUMENTS` | All arguments passed when invoking |
| `$ARGUMENTS[N]` | Specific argument by 0-based index |
| `$N` | Shorthand for `$ARGUMENTS[N]` |
| `${CLAUDE_SESSION_ID}` | Current session ID |

Example:
```yaml
---
name: fix-issue
description: Fix a GitHub issue by number
---
Fix GitHub issue $ARGUMENTS following our coding standards.
```
Running `/fix-issue 123` replaces `$ARGUMENTS` with `123`.

## Dynamic Context

The `` !`command` `` syntax runs shell commands before Claude sees the prompt. Output replaces the placeholder.

Example:
```yaml
---
name: pr-summary
description: Summarize changes in a pull request
---
PR diff: !`gh pr diff`
Changed files: !`gh pr diff --name-only`

Summarize this pull request.
```

Commands execute at skill load time — Claude only sees the final rendered output.

## Invocation Control Matrix

| Setting | You invoke | Claude invokes | When loaded |
|---|---|---|---|
| (default) | Yes | Yes | Description always in context |
| `disable-model-invocation: true` | Yes | No | Not in context until invoked |
| `user-invocable: false` | No | Yes | Description always in context |

## Security Notes

- No XML angle brackets in frontmatter — it appears in the system prompt and could inject instructions
- No reserved words ("claude", "anthropic") in names
- Frontmatter uses safe YAML parsing — no code execution

## Pitfall: Dynamic Context in Skill Examples

When writing skills that teach about other skills, `` !`command` `` and `@file` references in examples will execute during skill loading unless escaped. Wrap examples in fenced code blocks to prevent execution.
