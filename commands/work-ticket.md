---
description: Work on an existing Linear ticket — diagnose, design, execute
argument-hint: "<ticket-id>"
---

<objective>
End-to-end workflow for implementing a Linear ticket. Three decision checkpoints
where the engineer's judgment matters most — diagnosis, design, verification — with
the LLM handling information gathering and execution between them.

Usage: `/work-ticket MIN-42`
</objective>

<context>
Ticket ID: $ARGUMENTS

Fetch ticket details:
```bash
uv run ~/.claude/skills/linear/scripts/linear.py get $ARGUMENTS```
</context>

<process>

<!-- PHASE 1: ORIENT — Gather context, no engineer input needed -->

<step name="fetch_ticket">
Parse the ticket JSON response. Extract:
- **Title** and **description** (the problem statement)
- **Priority** and **estimate** (urgency/scope signal)
- **State** (confirm it's not already done)
- **Comments** (often contain clarifications or reproduction steps)
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
Present the ticket summary, then announce the workflow:

> **$ARGUMENTS: [ticket title]**
> [1-2 sentence summary]
>
> Here's how we'll work through this:
> 1. **Diagnose** — I'll explore the codebase and present my understanding of
>    the root cause. You confirm I've got it right.
> 2. **Design** — I'll search for precedent and present solution approaches
>    on a spectrum. You pick the direction.
> 3. **Execute** — I'll implement and present changes mapped back to the
>    diagnosis for your review before committing.
>
> Starting exploration now.

Do not wait for confirmation — proceed immediately.
</step>

<step name="load_skills">
Scan the skill list for skills matching the ticket's technology or domain.
Invoke each match via the Skill tool before proceeding.

- One clear match → invoke directly
- Multiple candidates → use AskUserQuestion to let the user choose
- No match → proceed without
</step>

<!-- PHASE 2: DIAGNOSE — Root cause analysis + engineer validation -->

<step name="explore_codebase">
Launch parallel Explore agents to understand the problem area. Frame searches
around the ticket's symptoms and domain.

**Scope-adaptive agent count:**
- **1 agent** — Focused ticket with named files/components
- **2-3 agents** — Multiple areas or unfamiliar domain

**Search focuses (diagnostic lens):**
1. **Symptom trace** — Find the code paths that produce the reported behavior.
   Trace from user-facing symptoms inward.
2. **Root cause search** — Follow the symptom trace deeper. Look for the
   underlying reason, not just where it manifests.
3. **Context scan** — What depends on this area? What conventions exist here?
   Note existing patterns and reusable code for the Design phase.

After agents return, read the key files yourself — do not rely solely on
agent summaries.
</step>

<step name="present_diagnosis">
**CHECKPOINT 1 — Highest-leverage decision point. Do not rush past it.**

Present a structured diagnosis:

> **Diagnosis**
>
> **What's happening:** [Current behavior from the user's perspective]
>
> **Root cause:** [The underlying technical reason, with evidence.
> Reference specific files and lines.]
>
> **Symptom vs. cause:** [If the ticket description focuses on symptoms,
> explicitly distinguish: "The ticket reports X, but the actual cause is Y."
> If the ticket correctly identifies the cause, state that.]
>
> **Desired outcome:** [What "fixed" looks like from the user's perspective]
>
> **Scope boundary:** [What we ARE fixing vs. what we're NOT touching, and why]

Then ask:

> Does this diagnosis match your understanding? Specifically — am I targeting
> the root cause, or is there something deeper I'm missing?

**On correction:** Absorb feedback. If the diagnosis changes significantly,
do a targeted follow-up exploration before proceeding. Do not re-present the
full diagnosis — acknowledge the correction and move forward.
</step>

<!-- PHASE 3: DESIGN — Precedent + constraints + solution spectrum -->

<step name="search_precedent">
Before proposing solutions, search for how similar problems have been solved.

Use AskUserQuestion to ask the engineer where to look:

> Before I propose solutions — have you seen a similar problem before?
> Where should I look for precedent?
>
> 1. **This project** — I'll search git history for related changes
> 2. **Another project** — tell me which one and I'll explore it
> 3. **Past conversations** — I'll search session history for relevant discussions
> 4. **Skip** — move straight to solution design
> 5. **Your call** — I'll do a quick best-effort search without over-investing

Based on the response:
- **This project:** Search git log and codebase for related patterns
  (`git log --all --oneline --grep="<keyword>"`, targeted Grep searches)
- **Another project:** Explore the named project's relevant areas using
  Explore agents
- **Past conversations:** Invoke `/session-search` with a description of
  the problem type
- **Skip:** Proceed immediately to design constraints
- **Your call:** Quick git log search in current project only. Limit to
  2-3 queries, stop regardless of results. Do not over-invest.

Present findings briefly as context for the design step — this is not its
own checkpoint.
</step>

<step name="present_design_context">
Present the constraints the engineer needs to evaluate solutions against.
This context is presented BEFORE proposals so the engineer reads it with
a design lens, not as post-hoc validation.

> **Design context**
>
> **Existing patterns:** [How similar functionality is implemented in this
> codebase. Reference specific files.]
>
> **Reusable code:** [Existing utilities, components, or abstractions the
> solution should leverage. Skip if nothing relevant.]
>
> **Hard constraints:** [API contracts, data formats, backwards compatibility]
>
> **Soft constraints:** [Team conventions, UX patterns, architectural preferences]
>
> **Precedent:** [What the search found, if anything.
> "No relevant precedent found" is a valid answer.]
</step>

<step name="propose_solutions">
**CHECKPOINT 2 — Engineer chooses direction.**

Scale proposals to actual decision space:

**One obvious approach** (bug fix, clear-cut feature): Present the single
approach with a brief note on why alternatives don't apply. Verify it
resolves the root cause and fits the constraints above.

**Genuine design latitude** (multiple valid paths): Present on a spectrum:

> **Solution spectrum**
>
> **Quick fix:** [What changes, where. Speed gain vs. what you give up.
> Resolves root cause: yes/partially/no. Fits existing patterns: yes/no.]
>
> **Pragmatic:** [What changes, where. Balances speed and quality.
> How it leverages existing patterns and reusable code.]
>
> **Scalable:** [What changes, where. Long-term quality gain vs.
> what it costs now. Where it departs from existing patterns, and why.]

Not every ticket warrants all three points on the spectrum. Use judgment —
a trivial bug fix needs one approach; a feature with real design latitude
needs the full spectrum.

> Which approach fits best? You can also combine elements or propose
> something different.
>
> To evaluate through a specific lens: `/consider:opportunity-cost`,
> `/consider:second-order`, `/consider:via-negativa`

Wait for user input. The user may pick, combine, challenge, or redirect.
Engage fully — proceed only when they explicitly signal readiness.
</step>

<!-- PHASE 4: EXECUTE — Plan, implement, verify, finalize -->

<step name="plan_and_implement">
Enter plan mode if not already in it.

> **Executing** the agreed approach.

Include the ticket ID ($ARGUMENTS) in the plan title for traceability.

The plan MUST include a final verification step before the commit step.
</step>

<step name="verify_and_finalize">
**CHECKPOINT 3 — Engineer approves before commit.**

After implementation, present verification mapped back to the diagnosis:

> **Verification**
>
> | Change | Addresses |
> |--------|-----------|
> | [file: what changed] | [which part of the root cause this resolves] |
> | ... | ... |
>
> **Root cause resolved:** [Confirm the diagnosed root cause is addressed,
> not just symptoms patched]

Then ask:

> Changes are ready. Want me to commit and close the ticket?

On approval, invoke `/finalize-ticket $ARGUMENTS`.
</step>

</process>

<success_criteria>
- Root cause explicitly diagnosed and confirmed by engineer before solution design
- Precedent search attempted (or explicitly skipped by engineer)
- Solutions evaluated against codebase conventions presented as design constraints
- Changes verified against root cause diagnosis before commit
- Ticket finalized via /finalize-ticket (committed, commented, attached, marked done)
</success_criteria>
