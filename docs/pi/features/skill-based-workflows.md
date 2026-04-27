# Skill-Based Workflows: Review, Commit, Explore

## What This Is

Zero-code alternatives to oh-my-pi's built-in `/review`, `omp commit`, and subagent features. Pi's SKILL.md format provides instruction-driven capabilities that load on demand — no TypeScript, no extension code, no additional tools in the system prompt.

These complement (not replace) the TypeScript extensions documented elsewhere. Use skill files when instruction-following is sufficient; build extensions when you need enforcement or tool registration.

## Why Skill Files Over Extensions

| Aspect | Skill file | Extension |
|--------|-----------|-----------|
| Code | Zero — markdown only | TypeScript |
| Prompt cache | Progressive disclosure (loaded on demand) | Always loaded |
| Enforcement | Instruction-based (model can deviate) | Programmatic (tool blocking, result enrichment) |
| Maintenance | Edit a markdown file | Edit + test TypeScript |
| Portability | Works on any agent that reads SKILL.md | Pi-specific API |

The Pi community strongly endorses skill files for workflows like planning and review (Reddit, 362 upvotes). GPT 5.5's instruction-following makes enforcement unnecessary for most cases.

## Skill: Code Review

Create `.pi/skills/review/SKILL.md`:

```markdown
---
name: review
description: Structured code review with priority-based findings
---

# Code Review Skill

Review the specified code changes (branch diff, uncommitted changes, or specific files).

## Process

1. Read all changed files using read/grep/find tools only
2. Analyze each change for issues at these priority levels:
   - **P0 (critical)**: Security vulnerabilities, data loss, authentication bypass
   - **P1 (high)**: Bugs, incorrect logic, race conditions
   - **P2 (medium)**: Performance issues, missing error handling, test gaps
   - **P3 (nit)**: Naming, style, minor improvements
3. Report each finding with: file, line range, priority, description, suggested fix
4. End with a verdict: APPROVE, REQUEST_CHANGES, or COMMENT

## Rules

- Do NOT modify any files
- Use `git diff` via bash to see changes
- Check for OWASP top 10 vulnerabilities
- Flag any hardcoded secrets or credentials
- Consider cross-file impact of changes
```

Invoke with: `/skill:review` or instruct the model to "review my changes using the review skill."

## Skill: AI Commit

Create `.pi/skills/commit/SKILL.md`:

```markdown
---
name: commit
description: Generate conventional commits with intelligent change analysis
---

# Commit Skill

Analyze staged/unstaged changes and create well-structured conventional commits.

## Process

1. Run `git status` and `git diff --stat` to understand scope
2. Run `git diff` (or `git diff --cached` for staged) to read actual changes
3. If changes span multiple concerns, propose splitting into atomic commits
4. For each commit, generate a message following conventional commit format:
   - `feat:` new features
   - `fix:` bug fixes
   - `refactor:` code restructuring
   - `docs:` documentation
   - `test:` test additions/changes
   - `chore:` maintenance tasks
5. Present the proposed commit(s) and wait for user approval
6. Execute `git add` and `git commit` only after approval

## Rules

- Never use `git add -A` or `git add .` — stage specific files
- Never commit .env, credentials, or secret files
- Keep subject line under 72 characters
- Focus the message on WHY, not WHAT (the diff shows what)
- If unsure about scope, ask the user
```

## Skill: Explore

Create `.pi/skills/explore/SKILL.md`:

```markdown
---
name: explore
description: Systematic codebase exploration and documentation
---

# Explore Skill

Systematically explore and document a codebase area.

## Process

1. Start with the directory structure: `find . -type f | head -50` or `ls -la`
2. Identify entry points, config files, and key abstractions
3. Read the most important files (entry point, main config, core types)
4. Map the dependency/import graph for the area of interest
5. Summarize: architecture, key files, data flow, and any concerns

## Rules

- Do NOT modify any files
- Prioritize reading files that are imported by many others
- Note any TODO/FIXME/HACK comments
- Report file sizes — flag anything unusually large
- Keep the summary under 500 words unless asked for detail
```

## When to Use Extensions Instead

Build a TypeScript extension when you need:

- **Tool registration** — AST tools, format-on-write (the model needs new tools)
- **Enforcement** — security hooks (blocking must be programmatic, not advisory)
- **Result enrichment** — format-on-write diagnostics (appending to tool results)
- **Persistent UI** — status indicators, structured dialogs, context management
- **Plan mode** — requires UI toggle, tool blocking, context reset (see [plan-mode.md](plan-mode.md))

## Status: Researched — Create skill files on Day 1
