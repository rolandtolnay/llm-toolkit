---
description: Work on an existing Linear ticket — fetch, explore, clarify, plan, implement, commit, and close
argument-hint: "<ticket-id>"
---

<objective>
End-to-end workflow for implementing a Linear ticket. Progresses through four distinct phases — Orient, Understand, Solve, Execute — each with a clear purpose and decision point. The user always knows what phase they're in and what comes next.

Usage: `/work-ticket MIN-42`
</objective>

<context>
Ticket ID: $ARGUMENTS

Fetch ticket details:
```bash
uv run ~/.claude/skills/linear/scripts/linear.py get $ARGUMENTS```
</context>

<process>

<!-- PHASE 1: ORIENT — Gather context and set expectations -->

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

If the ticket state is not already "In Progress", move it:
```bash
uv run ~/.claude/skills/linear/scripts/linear.py state $ARGUMENTS "In Progress"
```
</step>

<step name="announce_workflow">
Present the ticket summary, then announce the workflow phases so the user knows what to expect:

> **$ARGUMENTS: [ticket title]**
> [1-2 sentence summary of the ticket]
>
> Here's how we'll work through this:
> 1. **Understand** — I'll explore the codebase and make sure I fully understand the requirements. I'll check in with you on anything I'm unsure about.
> 2. **Solve** — I'll break down the problem and propose solution approaches for you to choose from.
> 3. **Execute** — Once we've agreed on an approach, I'll plan, implement, commit, and close the ticket.
>
> Starting with exploration now.

This is informational — do not wait for confirmation. Proceed immediately.
</step>

<step name="load_skills">
Scan the skill list in your system message for skills matching the ticket's technology or domain. Invoke each match via the Skill tool before proceeding — skills contain conventions and patterns that change what you look for during exploration.

- One clear match -> invoke it directly
- Multiple candidates -> use AskUserQuestion to let the user choose
- No match -> proceed without
</step>

<!-- PHASE 2: UNDERSTAND — Deep codebase knowledge + validated requirements -->

<step name="explore_codebase">
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

<step name="validate_requirements">
**Do NOT proceed to the Solve phase until you have 95% confidence that you know what to build.**

Tickets are written by humans for humans and almost always underspecify. Claude knows code, user knows intent. This step closes the information asymmetry gap.

**Present your understanding:**

> **Phase 2: Understand** — Here's what I found and what I think needs to happen.

- What the ticket requires (your interpretation of acceptance criteria)
- High-confidence assumptions — state these as facts, not questions. Example: "The new field should follow the existing pattern in `UserProfile`."
- Conflicts or gaps between ticket description and existing code

**Resolve gaps actively:**

For each medium or low-confidence assumption, ask a **separate, focused AskUserQuestion**. Do not bundle multiple gaps into one question — each gap is its own decision.

Frame each question with the codebase context you discovered during exploration so the user has what they need to answer. Example:
> "The ticket says 'add validation' but doesn't specify behavior on failure. The existing `OrderValidator` returns error messages inline. Should this new validation follow the same pattern, or did you have something different in mind?"

**What NOT to ask** (Claude determines these from exploration):
- Technical patterns to follow
- Error handling strategy
- Implementation details the user can't meaningfully influence
- Only ask about: user intent, expected behavior, scope boundaries

**If no gaps exist** (all assumptions are high-confidence), present your understanding and ask a single confirmation:
> "I'm confident I understand the requirements. [1-2 sentence summary]. Does this match your expectations, or should I adjust anything before I move to proposing solutions?"

**On corrections:** Absorb user feedback. Do not re-present the full understanding — proceed with updated context.
</step>

<!-- PHASE 3: SOLVE — First-principles decomposition + solution options -->

<step name="decompose_problem">
**Do NOT enter plan mode yet.** Before proposing solutions, decompose the problem to its fundamentals.

> **Phase 3: Solve** — Now that requirements are clear, here's my analysis and proposed approaches.

**First-principles decomposition:**

1. **Irreducible requirements** — What must be true regardless of implementation approach? Strip away conventions and list as bullet points.

2. **Current situation** — What exists in the codebase today: relevant patterns, current behavior, key files. Note which existing patterns are load-bearing (must follow) vs. conventional (could depart from).

3. **Constraints** — Hard constraints (API contracts, data formats, backwards compatibility) vs. soft constraints (existing conventions, team preferences).
</step>

<step name="propose_solutions">
**Scale the number of proposals to actual decision space:**

- **One obvious approach** (bug fix, clear-cut feature): Present the single approach with a brief note on why alternatives were dismissed. Still frame it against the irreducible requirements to confirm coverage.

- **Genuine design latitude** (multiple valid paths): Present **2-3 approaches**, each structured as:
  - **Approach name** — one-line summary
  - **How it works** — concrete description of what changes where
  - **Tradeoffs** — what you gain and what you give up, evaluated against the irreducible requirements
  - **Convention vs. departure** — note where this follows existing patterns and where it breaks new ground, with rationale for departures

**For each approach, verify:** Does it satisfy every irreducible requirement? If not, flag the gap explicitly.

**After presenting approaches:**

> If you'd like to evaluate these through a specific lens, you can use a mental framework — for example `/consider:opportunity-cost`, `/consider:second-order`, or `/consider:via-negativa`.

Then ask the user to choose:
> Which approach would you like to go with? You can also propose a different direction entirely.

**This is a collaboration checkpoint** — wait for user input. The user may pick an approach, combine elements from multiple proposals, challenge the decomposition, or propose something entirely different. Engage fully; proceed to planning only when the user explicitly signals readiness.
</step>

<!-- PHASE 4: EXECUTE — Plan, implement, commit, close -->

<step name="plan">
Enter plan mode if not already in it.

> **Phase 4: Execute** — Implementing the agreed approach.

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
- Requirements validated through active gap resolution before solution design
- Solution approach selected by user from first-principles-grounded proposals
</success_criteria>
