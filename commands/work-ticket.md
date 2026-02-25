---
description: Work on an existing Linear ticket — fetch, explore, clarify, plan, implement, commit, and close
argument-hint: "<ticket-id>"
---

<objective>
End-to-end workflow for implementing a Linear ticket. Gathers all context needed for planning (ticket details, codebase exploration, requirement clarification), then writes a self-contained plan that includes implementation, commit, and ticket state update.

Usage: `/work-ticket MIN-42`
</objective>

<context>
Ticket ID: $ARGUMENTS

Fetch ticket details:
```bash
uv run ~/.claude/skills/linear/scripts/linear.py get $ARGUMENTS```
</context>

<process>

<step name="fetch_ticket">
Parse the ticket JSON response. Extract:
- **Title** and **description** (the core requirements)
- **Priority** and **estimate** (scope signal)
- **State** (confirm it's not already done)
- **Comments** (may contain clarifications)
- **Parent issue** (if sub-issue, fetch parent for broader context)
- **Relations** (blocking/blocked-by tickets)

If the ticket has comments, fetch them:
```bash
uv run ~/.claude/skills/linear/scripts/linear.py get $ARGUMENTS -c```

Present a brief summary of the ticket to the user.

If the ticket state is not already "In Progress", move it:
```bash
uv run ~/.claude/skills/linear/scripts/linear.py state $ARGUMENTS "In Progress"
```
</step>

<step name="load_skills">
Scan the skill list in your system message for skills matching the ticket's technology or domain. Invoke each match via the Skill tool before proceeding — skills contain conventions and patterns that change what you look for during exploration.

- One clear match → invoke it directly
- Multiple candidates → use AskUserQuestion to let the user choose
- No match → proceed without
</step>

<step name="explore_codebase">
Do not proceed to planning until the codebase is deeply understood.

Launch parallel Explore agents to understand the areas the ticket touches. Base search terms on ticket title, description, and any file/component names mentioned.

**Scope-adaptive agent count:**
- **1 agent** — Focused ticket with named files/components (bug fix, small feature in a known area)
- **2-3 agents** — Ticket touching multiple areas or unfamiliar domain

Search focuses (select based on scope):
1. **Architecture search** — Find files, modules, and patterns related to the ticket's domain
2. **Convention search** — Find existing patterns for the type of change described (e.g., how similar features are implemented)
3. **Dependency search** — Find code that depends on or is depended upon by the target area

After agents return, read the key files yourself — do not rely solely on agent summaries.
</step>

<step name="present_and_clarify">
**Do NOT proceed to planning until you have 95% confidence that you know what to build.**

Externalize your understanding so the user reacts to concrete proposals instead of answering open-ended questions. Tickets are written by humans for humans and almost always underspecify — Claude knows code, user knows intent.

**Briefing — requirements focus:**
- What the ticket requires (your interpretation of acceptance criteria)
- Your assumptions about expected behavior, scope boundaries, and edge cases — each marked with confidence: **high** / **medium** / **low** to focus user attention on uncertain areas
- Conflicts or gaps between ticket description and existing code

**AskUserQuestion — cross the information asymmetry boundary:**
- Q1 (always): "Are these assumptions correct?" with options:
  - Looks right
  - Some corrections (let me clarify)
  - Let me reframe what's needed
- Additional questions (conditional): Only when ticket + exploration surfaced genuine behavioral ambiguity the user must resolve. Frame with codebase context discovered during exploration.

**What NOT to ask** (Claude determines these from exploration):
- Technical patterns to follow
- Error handling strategy
- Implementation details the user can't meaningfully influence
- Only ask about: user intent, expected behavior, scope boundaries

**On corrections:** Absorb user feedback. Do not re-present the full briefing — proceed with updated understanding.
</step>

<step name="design_solution">
**Do NOT enter plan mode yet.** Present the solution design:

1. **Current situation** — What exists in the codebase today: relevant patterns, current behavior, key files.
2. **Problem** — What needs to change and why, grounded in ticket requirements and clarified assumptions.
3. **Proposed approach** — Present the dominant approach with rationale. Only present alternatives when there is genuine ambiguity — do not manufacture options for the sake of choice.

This is a collaboration checkpoint — wait for user input. The user may confirm, challenge assumptions, or run their own analysis. Engage fully; proceed to planning only when the user explicitly signals readiness.
</step>

<step name="plan">
Enter plan mode if not already in it.

Include the ticket ID ($ARGUMENTS) in the plan title for traceability.

**The plan MUST include these final steps after all implementation steps (always present, always last):**

1. **Verify changes** — present a summary of all changes made
2. **Commit** — ask the user to confirm changes are ready, then invoke `/commit-commands:commit`. The commit message MUST include `[$ARGUMENTS]` (e.g., `[MIN-44]`).
3. **Comment on ticket with solution summary** — after the commit succeeds, invoke the `linear` skill with args: `Add a comment to $ARGUMENTS summarizing the solution: what approach was chosen, what files were changed, and any notable decisions. Then attach the commit to the ticket.`
4. **Mark ticket as Done** — this is a SEPARATE step. Invoke the `linear` skill with args: `Mark $ARGUMENTS as done`. Always confirm the state change succeeded.

Do NOT combine steps 3 and 4 into a single skill invocation — they are separate actions.
</step>

</process>

<success_criteria>
- Ticket marked as Done (explicitly verified, not assumed)
- Solution summary comment left on ticket
- Commit message includes `[$ARGUMENTS]` for git-Linear traceability
- Requirements validated via assumptions-first briefing
- Solution approach confirmed by user through collaborative design step before entering plan mode
</success_criteria>
