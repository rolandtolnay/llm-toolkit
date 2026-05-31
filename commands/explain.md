---
description: Explain the current issue, options, or behavior so I can make a confident decision
argument-hint: [topic or leave blank for current context]
---

Explain $ARGUMENTS (or the current discussion topic if no arguments provided) so the user can make a confident, informed decision.

Investigate before explaining. Read relevant code, check git history, trace dependencies — gather what's needed first.

<confusion_shapes>

Detect which shape of confusion is active from conversation context. There may be more than one.

1. **"What is happening and why?"** — User sees behavior but can't trace the cause. They need a cause chain, not a code dump.
2. **"Which option should I pick?"** — User faces alternatives but can't evaluate trade-offs. They need consequences of each option, not implementation details.
3. **"Is this important?"** — User can't gauge severity. They need impact assessment: what breaks if ignored, what's the blast radius.
4. **"How does this piece fit?"** — User lacks architectural or business context. They need the system map: what connects to what, why this component exists, what depends on it.

</confusion_shapes>

## Explanation shape

Lead with a plain-language summary a product manager could follow: what's happening, why it matters, and — if a decision is needed — which option you'd recommend and why.

Anchor to concepts the user already knows when an honest parallel exists. When no parallel fits, say so and explain the concept on its own terms. A misleading analogy is worse than none.

Include only the specifics that change the decision — the relevant snippet, the config that matters, the concrete trade-off. Stop there.

Confirm the user has enough context to proceed before moving on.

<success_criteria>

- User can articulate what the issue is and why it matters
- If options were presented, user understands the concrete consequences of each
- Explanation anchors to concepts the user already holds, without forcing false parallels
- Only implementation details that change the decision are included
- User confirms they have enough context before moving on

</success_criteria>
