---
description: Reflect on recent work, extract principles from past conversations, and capture learnings
argument-hint: "[timeframe]"
---

<objective>
Review recent work across commits, conversations, and project artifacts. Extract principles, patterns, and philosophy from user messages in past conversations. Present findings for approval, then write them to a user-chosen destination.

Run when starting a new session to compound learnings from recent work.
</objective>

<context>
Timeframe: $ARGUMENTS (default: "past week" if empty)
Project path: !`pwd`
</context>

<process>

1. **Determine scope.**
   Parse the timeframe from $ARGUMENTS. Default to "past week" if empty.
   Convert to a git-compatible date string (e.g., "7 days ago", "3 days ago", "2 weeks ago").

2. **Gather project signals.**
   Read these files if they exist (skip any that don't):
   - CHANGELOG.md — recent entries within the timeframe only
   - README.md — skim for project identity and purpose
   - CLAUDE.md — project instructions and conventions

   Run `git log --oneline --since="<date>"` and group commits thematically.
   Identify major features, refactors, fixes, and patterns from commit messages.

3. **Search past conversations.**
   Encode the project path for conversation lookup:
   - Take the full project path from `pwd`
   - Replace every `/` with `-`, prefix with `-`
   - Conversations are JSONL files at `~/.claude/projects/[encoded-path]/`
   - Example: `/Users/me/my-project` → `-Users-me-my-project`

   List JSONL files modified within the timeframe using `ls -lt` and filter by date.

   Spawn **parallel Explore subagents** (2-4 agents, split files evenly across them) to search conversation content. Each subagent prompt must include:
   - The specific JSONL file paths to read
   - Instructions to focus on **user messages** (role "human" or "user")
   - Instructions to extract statements about: principles, philosophy, preferences, frustrations with approaches, "aha moments", design rationale, anti-patterns, recurring opinions
   - Signal phrases to look for: "I think we should", "The problem with", "What if we", "I don't want", "The key insight is", "This is important because", "always/never do X", "the right way to"
   - Instructions to return exact quotes with brief context for each finding

   **CRITICAL: Never read JSONL files in main context. Always delegate to subagents.**

4. **Ask where to write.**
   Use AskUserQuestion to ask the user where extracted learnings should be stored. Options:
   - **Auto-memory** — The project's persistent memory directory at `~/.claude/projects/[encoded-path]/memory/`. Best for general session-to-session continuity. Supports MEMORY.md (concise index, under 200 lines) with links to topic-specific files (e.g., `patterns.md`, `preferences.md`).
   - **CLAUDE.md** — The project's `.claude/CLAUDE.md` or root `CLAUDE.md`. Best for principles that should govern every interaction in this project. Append to an appropriate section.
   - **Custom path** — User specifies a file or directory (e.g., a skill's SKILL.md, a `docs/` folder, a reference file). Best when learnings belong to a specific tool, skill, or documentation system.

5. **Read existing content at destination.**
   Read the current content at the chosen destination. Understand what's already captured to avoid duplicates and to match the existing structure and tone.

6. **Synthesize findings.**
   Cross-reference commit themes, conversation insights, and existing content. Identify:
   - **New principles** — user philosophies not yet captured
   - **Evolved principles** — existing entries that need updating based on recent work
   - **Stale entries** — content that contradicts recent decisions
   - **Patterns** — recurring themes across multiple conversations

   Prioritize by signal strength:
   1. Principles stated multiple times across conversations (strongest)
   2. Principles that drove actual implementation changes (validated by commits)
   3. Explicit user preferences ("always X", "never Y")
   4. Single-mention insights that are significant

7. **Present findings.**
   Show a structured summary to the user:

   **Recent Work Overview** — brief thematic summary from commits

   **Candidate Updates** — numbered list, each with:
   - The principle in concise form
   - Supporting evidence (quote + conversation context or commit reference)
   - Tag: `NEW` | `UPDATE` | `STALE`

   Ask the user which findings to capture. They may approve all, select specific items, edit wording, or add their own.

8. **Write approved learnings.**
   After user approval, write to the chosen destination. Adapt to the destination format:

   **Auto-memory**: Update MEMORY.md as a concise index (under 200 lines). Create or update topic files for detailed entries. Link topic files from MEMORY.md. Remove stale entries.

   **CLAUDE.md**: Append principles to an appropriate existing section, or create a new section if none fits. Match the file's existing tone and structure. Keep additions concise — CLAUDE.md is loaded into every conversation.

   **Custom path**: Read the file's existing structure and match it. If it's a SKILL.md, add to the appropriate knowledge domain. If it's a markdown file, match its heading hierarchy, list style, and section patterns. If it's a directory, create or update the most relevant file within it.

</process>

<success_criteria>
- Conversation JSONL files read exclusively via subagents, never in main context
- User chose the write destination before synthesis (existing content informs deduplication)
- All candidate updates presented to user before any writes
- Content written matches the structure and tone of the destination file
- No duplicate entries — existing content checked before writing
</success_criteria>
