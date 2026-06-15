---
name: write-loop
description: Turn a ticket, file, or idea into a loop prompt through codebase exploration, relentless grilling, and a loop-guide-grounded synthesis you can paste after /goal.
disable-model-invocation: true
---

Take an input — a ticket ID, a file path, or a description of an idea — and produce a **loop prompt** grounded in shared understanding between you and the user.

A loop is not a task description. It's a prompt the user hands to an autonomous run (e.g. a `/goal` command) and walks away from: it defines what "done" means, how the run checks its own work, and how far it can go alone. Your job is to design that machine with the user, then render it.

This skill is grounded in [loop-guide.md](./loop-guide.md), bundled alongside it. Read that guide before the synthesis steps — it carries the loop template, the writing principles, and the paste-ready instruction lines this skill draws on. References below to "the loop-guide" mean that file, relative to this skill's directory.

The final artifact is a markdown loop prompt saved to `etc/loop/<slug>.md` in the project root, where `<slug>` is a 3-5 word dash-separated name representing the work. The file's body is the prompt itself — content the user copies verbatim into an agent harness (Claude Code, Codex) after `/goal`. Write it for that downstream run, not as a document about the work.

## Decode the input

If no input is provided, ask: "What loop are we building? Give me a ticket ID, file path, or describe the idea."

Otherwise, determine what you're working with:

1. **Ticket ID** (matches `[A-Z]{2,4}-\d+`) — fetch the ticket's full implementation context: description, comments, parent, and related/blocking tickets.
2. **File path** — read the file and use its contents as the starting context.
3. **Free text** — take the message as-is.

Once decoded, share your complete understanding of what this work is about. Present it fully — the user needs enough context to catch misinterpretations or incorrect assumptions before you proceed.

## Orient in the codebase

Do a lightweight exploration pass to ground yourself before the conversation begins. Spin up explore sub-agents scaled to the input — one when the work is localized, more when it spans distinct areas (separate subsystems, unrelated features). Search for:

1. CONTEXT.md and any ADRs relevant to this area
2. Existing code that matches the domain of the work
3. Adjacent features that might be affected or inform the design
4. Whatever the run will use as a self-check — existing tests, type/lint/build commands, real input data — since the loop's metric will lean on it

This is orientation, not diagnosis. Get enough to ask grounded questions — the deeper design happens during grilling.

## Grill

Read `~/.pi/agent/skills/grill-with-docs/SKILL.md` and follow it. References within that skill (like `CONTEXT-FORMAT.md` and `ADR-FORMAT.md`) are relative to its directory at `~/.pi/agent/skills/grill-with-docs/`.

Frame: the goal of this grilling session is to reach enough shared understanding to design a sound loop — meaning you can name its three ingredients with confidence. Walk down every branch of the decision tree. Update CONTEXT.md and offer ADRs inline as decisions crystallize — that behavior is intentional and important.

A loop is only as good as these three, so drive the grilling toward them:

- **Objective** — what "done well" looks like in one sentence, stated as an outcome observable from the user's side, not the steps to get there.
- **Metric** — how the *run itself* tells a good pass from a bad one without the user reading every word. This is the hard part and where most loops quietly fail; spend the most grilling here. Push for the strongest option the task allows: self-score against named criteria, real validation (tests / type / lint / build / smoke), independent verification by a fresh context, or a ground-truth oracle with a confidence flag. Combine when you can.
- **Boundary** — what the run does alone versus where it stops for the user, phrased by irreversibility.

If the task repeats, also probe for a **learning wire**: a cheap signal at the end of each pass that should change the next pass, plus somewhere it persists. Name it only if it genuinely exists — don't manufacture one.

When you are confident all branches are resolved, announce that clearly.

## Confirm the loop ingredients

Before writing anything, play back the loop's skeleton and get the user's sign-off:

- The **objective** in one sentence.
- The **metric** — how the run grades its own pass. State it concretely. If you can't make it concrete, say so plainly; that gap is the real work, not a detail to paper over.
- The **boundary** — what runs alone, what stops for the user.
- The **learning wire**, if there is one.
- Whether this is **one loop or a sequence of slices** (see below).

Do *not* produce a module breakdown or a step list — a loop is outcome-first, and a checklist would drag it back toward the shape the loop-guide warns against. Confirm the skeleton, not the path.

### One loop, or a sequence of slices

Default to a single loop. When the grilling reveals the work is too large for one autonomous run, propose slicing it into a numbered sequence — each slice independently runnable, leaving something working, with its own `Done when`. Confirm the split with the user before writing. Save slices as `etc/loop/<slug>-1-<slice>.md`, `etc/loop/<slug>-2-<slice>.md`, and so on.

## Write the loop

Render the loop using the template below. The run executes in the same project, so reference `CONTEXT.md` and the relevant ADRs by path and use their canonical vocabulary; inline into `Constraints` only the genuinely locked trade-offs that must not be re-litigated. Keep it tight — every line competes with the others for compliance, so cut anything that doesn't change behavior.

```markdown
# <Project> — <one-line outcome>

## Why
One short paragraph, first person: the problem the user actually has, and what
this is the engine for. Intent lets the run connect the task to the right context.

## What I want (from my side)          ← the OBJECTIVE
Bullets describing the experience the user gets, not the implementation.
Each bullet observable from outside the system.

## It should get smarter the more I use it   (only if it's a loop that learns)
Name the feedback wire: the signal each pass produces, how it changes the next
pass, and where it persists.

## Constraints / Locked decisions
Only constraints that must not be re-litigated: language, key services, a hard
rule, the load-bearing ADR decisions. Reference CONTEXT.md / docs/adr/ by path.
Lock as little as possible — every locked line is a path the run can't optimize.

## How to work                          ← the BOUNDARY + working style
Pull the load-bearing lines from the loop-guide's "Paste-ready instruction lines"
that this loop actually needs — autonomy, boundary, act-don't-over-plan, simplest
thing, ground progress claims, self-verification. Use the ones it needs, not all.

## Done when                            ← the METRIC satisfied
An observable end state, not a step count. The metric satisfied.
```

Apply the loop-guide's writing principles as you render: outcome-first not steps; decision rules over needless absolutes (reserve ALWAYS/NEVER for true invariants — safety, hard rules, required output fields); ground in real data not fixtures; delegate bulky repetitive work to subagents with a budget. Pull the exact wording for the `How to work` lines from the loop-guide's "Paste-ready instruction lines" section so the boundary, autonomy, and grounding language is load-bearing and neutral.

Save the rendered prompt to `etc/loop/<slug>.md` (or the numbered slice files). Create the `etc/loop/` directory if it doesn't exist.

## Self-audit the written loop

After the file is written, run a separate verification pass against what's on disk — re-read the saved file and audit it against the loop-guide's checklist:

1. **Objective** — one sentence, observable from the user's side?
2. **Metric** — can the run tell a good pass from a bad one without the user reading every word? Is the chosen method (self-score / validation / independent verification / ground-truth oracle) actually written into the prompt?
3. **Boundary** — clear what runs alone and what stops to check in, phrased by irreversibility?
4. **Learning wire** — if the task repeats, is the compounding signal named with somewhere to persist?
5. **Outcome-first** — results not steps; no needless absolutes? (The grilling tends to surface implementation detail that creeps back in as a checklist — strip it.)
6. **Grounded** — will the run tune against real data and audit claims against real results?
7. **Tight** — is every line earning its place?

Weight the metric and outcome-first checks most heavily — those are the loop-guide's named failure points. Fix anything that fails directly in the file, then announce the file path.

## Success criteria

- Input fully decoded and understanding shared with the user before exploration
- Orientation pass covers domain docs, relevant code, adjacent features, and the run's available self-check signals
- All decision branches resolved during grilling, with CONTEXT.md/ADRs updated inline
- Loop ingredients (objective, metric, boundary, learning wire) confirmed with the user before writing
- Loop saved to `etc/loop/<slug>.md` as a paste-ready prompt, following the loop-guide template
- Written file self-audited against the loop-guide checklist and fixed in place
