---
name: new-project
description: Interview the user about a new greenfield project and synthesize PROJECT.md — a durable context artifact that future autonomous runs (goals, loops) read to resolve edge cases and unknowns without user input. Use when starting a new project from scratch, or re-run to update an existing PROJECT.md.
disable-model-invocation: true
---

# New Project

Interview the user about what they want to build, then synthesize `PROJECT.md` at the project root.

PROJECT.md is written for a future reader who isn't the user: an LLM partway through an autonomous run that hits a fork the prompt doesn't cover. That reader resolves the fork from this document — who the product is for, what it must never compromise, what's explicitly out — instead of interrupting the user or guessing. Every section earns its place by letting that reader make the call the user would have made.

The interview is where the value is created; the synthesis afterward is mechanical. A vague PROJECT.md forces every future run to guess, and the cost compounds — invest the effort in the conversation.

## Mode

If `PROJECT.md` already exists, this is an update: read it, summarize the current context in a couple of sentences, and ask freeform what changed. Run the same conversation focused on the delta, and preserve sections the update doesn't touch.

Otherwise open freeform — "What do you want to build?" — and let them dump their mental model before you add any structure.

## How to interview

You are a thinking partner, not an interviewer. The user usually has a fuzzy idea; the job is to sharpen it — questions that make them think "oh, I hadn't considered that," not a form to fill in. Follow the thread of whatever carried energy in their answer rather than walking a checklist.

**Never ask what a future run can derive.** The interview's scarce resource is information that exists only in the user's head: their motivation, taste, priorities, non-goals, and personal constraints. Competitive landscape, typical user flows, stack choices, sensible defaults — a capable model derives these at execution time with fresher context than this interview has. Spend the entire question budget on the asymmetry.

**Derive before asking.** After their opening dump, infer the business context and present it for reaction: "Sounds like this is for [audience] dealing with [problem], and your approach is different because [X]. Right?" People articulate by reacting, not generating — a concrete guess to correct beats an open question.

**Challenge vagueness.** "Good," "simple," "users," "fast" — don't let these through unexamined. Ground fuzzy answers in the concrete: "Walk me through a session — you open the app, then what?" "Give me an example."

**Spend the question budget where clarity is lowest.** Clarity is non-uniform: the audience may be crystal clear while differentiation is mush. Confirm the clear parts and move on; probe the fuzzy ones. Low-clarity signals: broad categories ("developers", "small businesses"), vague benefits ("makes things easier"), "nothing else does this," hedging ("I think", "maybe").

**Offer options when they help.** For vague answers, the question tool with 2–4 concrete interpretations beats an open follow-up — "Fast how?" → sub-second response / handles large datasets / quick to build / let me explain. Always include the escape hatch. Stay freeform when the user needs room to think.

### The four highest-leverage questions

If you only get four answers, get these:

1. **"What does done look like?"** — without observable outcomes, every future run guesses at scope.
2. **"What's the core interaction?"** — the one thing the user does that makes the product valuable; anchors what gets built first.
3. **"What already exists / what can't change?"** — constraints prevent planning in a vacuum.
4. **"Imagine this is wildly successful in a year — what does that look like?"** — reveals what actually matters (commercial viability, reliability, personal satisfaction) and weights every other section.

### Ask grounding questions, not template-shaped ones

| Section | Don't ask | Ask instead |
|---------|-----------|-------------|
| Who It's For | "Who is your target audience?" | "Who would be your first 10 users — real people you'd tell tomorrow?" |
| Core Problem | "What problem does this solve?" | "What triggered you to want to build this? What's broken today?" |
| How It's Different | "What's your USP?" | "What are people using today instead? What's wrong with it?" |
| Core Value | "What's most important?" | "If only ONE thing worked perfectly and everything else was mediocre, what would it be?" |
| Key User Flows | "What are the key flows?" | "Walk me through a session. You open the app — then what?" |
| Success | "How do you define success?" | "Imagine this is wildly successful in a year. What does that look like?" |

### Extract judgment with forced tradeoffs

Late in the interview, once the idea is clear, run two or three forced-tradeoff rounds with the question tool. These fill Default Judgments — the section future runs lean on hardest — and passive listening won't reliably surface them. Pick tradeoffs this product will actually face; for example:

- "Shipping speed vs. polish — when they conflict in v1, which wins?"
- "Simple and opinionated vs. flexible and configurable?"
- "When a v1 corner must be cut, what goes first?"
- "Torn between the daily power user and the occasional visitor — who do you optimize for?"

Each answer becomes one bias line in Default Judgments, in the user's words.

### Decision rules

- Never accept "everyone" as an audience — narrow to who needs it *most*. A broad audience signals fuzzy thinking, not universal appeal.
- "Nothing else does this" is almost always wrong — probe alternatives, including manual workarounds and spreadsheets.
- Don't ask about tech stack before understanding the idea, and never ask about the user's technical skill — an LLM builds this.

## When you have enough

You're done when you could brief a stranger on all six: what it is, why it needs to exist, who it's for (specific enough to find 10 of them), what makes it different from alternatives, the 2–3 core interactions, and what success looks like. If they volunteer more, capture it.

**Then dry-run the artifact before offering the gate.** Simulate 3–5 concrete forks a future autonomous run would plausibly hit for *this* product — the awkward, specific kind ("does signup require email verification?", "what happens to unsaved work when sync fails offline?", "free tier limit?"). For each, check: could a stranger LLM resolve it from what you've gathered, the way this user would? Any fork that fails means one more targeted question or a stronger Default Judgments entry — the dry-run, not the section list, is the real completeness test.

When the dry-run passes, offer the gate with the question tool — "Create PROJECT.md" / "Keep exploring" — and loop until they choose to create. If they keep exploring, ask what they want to add or probe the remaining gaps.

## Write PROJECT.md

Synthesize everything gathered into `PROJECT.md`, in the user's own words and framing where possible. Concrete beats polished; no marketing language.

**Write for value density, not completeness.** This document is injected into every future run's working context, where it competes with the actual work for tokens. Capture every decision-relevant fact; cut anything a capable model would already assume (generic best practices, obvious flow details, boilerplate rationale). Target roughly a page and a half — if it's longer, the cuts should come from the derivable, not from the user's judgment.

```markdown
# [Project Name]

> **For future runs:** when you hit a decision this document doesn't answer, decide in favor of Core Value for the people in Who It's For, within Constraints — then record the call in Key Decisions.

## What This Is
[2-3 sentences. Product identity in plain language.]

## Core Value
[One sentence: the ONE thing that cannot fail. Everything else can be mediocre; this can't. Drives every tradeoff.]

## Who It's For
[Specific enough to find 10 of these people. Their context: what they do today, what tools they use, what frustrates them.]

## Core Problem
[The pain or desire that makes this necessary, and why existing alternatives don't suffice. One sentence forces precision.]

## How It's Different
[2-3 concrete differentiators against what people use today instead — including manual workarounds.]
- [Differentiator]

## Key User Flows
[The 2-3 core interactions, one verb-driven line each.]
- [Log workout → view history → track progress]

## Out of Scope
- [Exclusion] — [why; the reason is what stops it creeping back in]

## Constraints
- **[Type]**: [What] — [Why]

[Tech stack, timeline, budget, dependencies, compatibility — only real ones, each with its reason.]

## Default Judgments
[Biases the user revealed, for resolving unknowns without them. e.g. "prefer dead-simple over configurable", "polish the core flow before adding surface area", "when torn, optimize for the daily user over the occasional one".]

## Technical Context
[Stack choices and integrations if discussed. Omit the section if none.]

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| [Choice made during the interview] | [Why] | — Pending |

---
*Last updated: [date] — [initialization / what changed]*
```

Section notes beyond what the placeholders say:

- **Default Judgments** is the section that lets future runs handle unknown unknowns — listen for taste and priorities throughout the interview (what they dismissed, what they lingered on) and distill them here as decision biases, not features.
- **Key Decisions** starts seeded with choices made during this conversation; future runs append theirs. Outcomes update later: ✓ good / ⚠️ revisit / — pending.
- In update mode, refresh the footer and log significant context changes as Key Decisions rather than silently rewriting history.

## Finish

Initialize a git repo if this directory isn't one, and commit PROJECT.md:

```
docs: initialize [project-name]

[One-liner from Core Value]
```

Close with where things stand — the project one-liner and the natural next step. If the repository does not yet have the goal-run foundation, recommend `bootstrap-goal-project` before drafting the first autonomous goal with `write-loop`. If the foundation already exists, go directly to `write-loop`.

The document only works if runs are routed to it. Give the user the line to include in every goal or loop prompt, ready to copy:

> Consult PROJECT.md for any product decision not covered here; record calls you make in its Key Decisions table.

## Success criteria

- The dry-run passed: 3–5 simulated forks specific to this product, each resolvable from PROJECT.md alone the way this user would resolve them.
- Question budget went to user-private information — nothing was asked that a future run could derive itself.
- Audience, problem, and differentiation were derived and confirmed with the user, not accepted at first-pass vagueness.
- Default Judgments holds explicit tradeoff answers in the user's words, not inferred filler; Out of Scope and Constraints entries all carry reasons.
- PROJECT.md is roughly a page and a half of decision-relevant content, committed to git, and the user has the copy-paste line that routes future runs to it.
