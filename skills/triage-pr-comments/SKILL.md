---
name: triage-pr-comments
description: >
  Triage pull request comments by fetching from GitHub, analyzing each against
  codebase context and domain docs, and deciding fix vs. ignore vs. defer.
  Use when addressing PR feedback, handling code review comments, or following up on reviews.
---

Triage review findings one at a time and produce an analysis the user can judge from. Write for a reader with strong engineering and systems judgment who is not familiar with this codebase's granular implementation details: the analysis must let them understand each finding, imagine its real-world consequence, and approve or challenge your verdict without opening the code themselves.

## Gather

Resolve the findings source. Default: the open PR for the current branch — read `references/github-api-reference.md` first for efficient fetch, reply, and resolve commands and their gotchas. Fetch inline review comments and top-level PR comments; drop reply comments, resolved threads, and bot boilerplate (summaries, poems, checklists). When the user points at a review report or pastes findings instead, work from those and skip the GitHub mechanics.

Gather the context the judgments depend on: the PR body, linked tickets when referenced (fetch via the linear skill, including parent epic and blockers), and the project's domain docs (`CONTEXT.md`, `docs/adr/`) when present.

Present a numbered inventory — number, source, `file:line`, one-line summary — and keep those numbers stable for the rest of the triage. Merge duplicates: one decision per issue.

## Analyze each finding

Give each finding a numbered section anchored to its exact `file:line`, covering three things:

**Context.** A mini walkthrough of the flow or functionality the finding sits in — pseudocode when it makes the flow clearer — with just enough surrounding behavior that the reader can form their own judgment of the finding without knowing the implementation.

**Consequence.** Describe the failure scenario plainly, from the user's perspective: what a real person doing a real task would experience if this fired. Then give your own read on how likely that scenario is and how much it hurts — a common path or a contrived edge case, a self-healing glitch or a blocked flow. Ground likelihood in how the code is actually used — call sites, lifecycle, realistic data volumes — not what could theoretically happen in isolation; bot reviewers often apply generic patterns, so check the framework actually behaves as claimed. For code-health findings (architecture, patterns, test coverage) there is no failure scenario — describe the maintenance cost instead; a finding doesn't need to be a bug to be worth acting on.

**Verdict.** Your judgment and its reasoning, one of:

- **Ignore** — why the finding doesn't warrant action. If it contradicts a recorded ADR, cite the decision rather than re-litigating it.
- **Fix** — restate the change in your own words, with pseudocode when it isn't obvious. When the reviewer's proposed fix is suboptimal, propose the better alternative: a fix that adds complexity disproportionate to the risk, or defends against scenarios that can't occur, makes the code worse.
- **Defer** — why it's valid but belongs in separate work. Tests for code changed in this PR are never deferred — they ship with the code they cover.

Let each analysis take the length its finding deserves — a paragraph or two for most, a few sentences for a nitpick, more when the reasoning chain is genuinely long. Mention scope only when a finding actually falls outside the PR or its ticket's acceptance criteria; most are in scope and saying so is noise.

When likelihood genuinely can't be settled from the code, verify instead of assuming — reproduce it in the running app, or ask the user to check a concrete step — and only then commit to a verdict.

## Report, then align

Present the report and stop. Verdicts are proposals until the user settles them in conversation. Then carry out the settled decisions:

- **Ignored** — reply on the thread with the reasoning, then resolve it.
- **Deferred** — search Linear for an existing ticket covering the issue before creating one; reply with the ticket ID and why it's deferred, then resolve.
- **Fixes** — proceed however the user directs; implementation is not part of the triage report. After a fix lands, reply on its thread with what was done and resolve it.

## Success criteria

- Every unresolved finding numbered, analyzed, and decided — none skipped
- Each analysis readable on its own: context, plain-language consequence with your likelihood/severity judgment, and a reasoned verdict
- The turn ends with the report; no replies, resolutions, tickets, or code changes until decisions are settled in conversation
- Deferred items checked against existing Linear tickets; ignored and deferred threads replied to and resolved once agreed
