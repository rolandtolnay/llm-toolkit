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

Run in parallel:
1. **Architecture search** — Find files, modules, and patterns related to the ticket's domain
2. **Convention search** — Find existing patterns for the type of change described (e.g., how similar features are implemented)
3. **Dependency search** — Find code that depends on or is depended upon by the target area

After agents return, read the key files yourself — do not rely solely on agent summaries.
</step>

<step name="clarify_requirements">
**Do NOT proceed to planning until you have 95% confidence that you know what to build.**

Contrast ticket requirements against codebase findings. Actively look for:
- Ambiguous acceptance criteria
- Missing technical details (which API, which component, which pattern to follow)
- Edge cases not addressed in the ticket
- Conflicts between ticket description and existing code
- Behavioral questions (what happens when X? should Y also change?)
- Scope boundaries (what is explicitly NOT part of this ticket?)

Ask as many rounds of clarifying questions as needed. Do not batch unrelated questions.

Tickets are written by humans for humans and almost always underspecify implementation details. If you believe there are zero gaps, state your full understanding of the requirements and ask the user to confirm before proceeding.
</step>

<step name="design_solution">
**Do NOT enter plan mode yet.** Present to the user:

1. **Current situation** — What exists in the codebase today: relevant patterns, current behavior, key files.
2. **Problem** — What needs to change and why, grounded in ticket requirements and clarified details.
3. **Proposed solutions** — 2-3 approaches with trade-offs for each (effort, risk, maintainability, scope of change). Include restructuring options when the existing code is part of the problem.

Use AskUserQuestion to get the user's direction on which approach to take. Iterate until the user confirms the solution direction.
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
- Solution direction confirmed by user before entering plan mode
- Ticket marked as Done (explicitly verified, not assumed)
- Commit message includes `[$ARGUMENTS]` for git-Linear traceability
- Solution summary comment left on ticket
- Requirement gaps closed via user clarification before planning
</success_criteria>
