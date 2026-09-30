---
name: boy-scout
description: Re-read the flow this session built or fixed for cheap, worthwhile fixes and behavior that would surprise a user or developer. Use before concluding a task, when something still feels worth fixing.
disable-model-invocation: true
---

Take a second look at the work this session built or fixed and leave it a little better than you found it. The flow is that work followed end to end through the paths it actually runs on, or whatever the invocation names. Right now you know this code better than anyone will again for a long time: the paths, the decisions behind them, and the corners that iteration touched. A fix that costs minutes now costs an investigation later. The pass works by switching roles: read the flow as its first caller or user would, not as its author, and treat anything that would surprise them as a candidate.

Invoking this skill asks for the pass, not for findings. "Nothing worth changing" is a complete answer, and padding the report with cosmetic findings is the failure. Do the pass yourself rather than delegating it; a fresh reviewer lacks the context that makes it cheap. The report goes to the user, who picks what to apply, so write it so they can decide without reopening the code.

## Gate

A finding earns a place only when both hold:

- **Cheap** — contained to the flow, no new abstraction, no redesign.
- **Worth it** — a real user or developer is likely to hit it, and it costs them when they do. A rare glitch that self-heals fails the gate; a common path that blocks, loses work, or misleads passes it.

Decisions settled earlier in the session stay settled unless new evidence shows they are wrong. Problems outside the flow get one line at most, pointing at the skill that handles them: ripple-check when the same pattern repeats elsewhere, improve-codebase-architecture when the fix is structural.

## Pass

The first pass tends to miss:

- **Unhappy paths** — what happens when the flow is cancelled, fails partway, or is retried.
- **Silent failure** — a fallback or an unknown that gets reported as success.
- **Drift** — two places encoding the same knowledge differently, including docs versus behavior.
- **Leftovers from iterating** — dead paths, vestigial parameters, names that describe an earlier version.

Reproduce a suspected bug when a quick script or test can; otherwise mark it `[inference]`. Stop when you have read the flow end to end as its user would and can either name the findings or say why none earn a change.

## Report

Lead with the verdict: how many findings are worth doing now, or that none are. Then number each finding with where it lives, what happens and whom it surprises, the evidence (reproduced output or `[inference]`), and the cheap fix with its regression risk. Close with one line on what you examined and deliberately left alone, and why, then your recommendation.

Make no changes until the user picks, unless the invocation asked you to apply them; then implement the picked items.
