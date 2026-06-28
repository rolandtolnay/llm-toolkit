---
name: write-loop
description: Turn a rough project idea into a short, outcome-focused /goal prompt for a one-shot autonomous project. Detects what's missing, asks only the high-leverage questions to close the gaps, and assembles a gradeable goal.
disable-model-invocation: true
---

Turn a rough idea into a strong `/goal` — the short prompt a user pastes to kick off an autonomous, one-shot project.

The user hands you a half-formed idea. You find the gaps that would make the run guess badly, ask only the high-leverage questions to close them, and hand back a short, outcome-focused goal.

Why the goal can be short: it is **not** a PRD. The autonomous run it kicks off derives the persona, rubric, and plan on its own, and owns the stack, testing, and deployment. Your only job is to make the *destination* unambiguous so the run can build the road. So describe *what* and *why*; never spend the user's words on *how*.

## 1. Capture the idea

Take the user's message as the raw goal. If they gave nothing, ask once: "What do you want to build? A sentence or two on what it should do and who it's for."

## 2. Find the gaps

Check the idea against the goal fields, in priority order. Mark each **present / vague / missing**.

1. **Outcome** (required) — what the user can do or see when it works, stated as a result, not a feature list. The run grades against this, so it must be concrete.
2. **Who & when** — the person and the moment of use. A few words is plenty; the loop expands it into a persona.
3. **Success signal** — how you'd know it's good. This becomes the rubric.
4. **Design kit + target device** — which kit under the design-systems dir, and mobile / tablet / desktop / responsive.
5. **Guardrails** — what *not* to build or touch. The cheapest defense against scope drift.
6. **Hard constraints** — only if real: a required integration, specific data, a must-have feature.

## 3. Ask only the high-leverage gaps

Ask the fewest questions that turn a vague idea into a gradeable goal. Sometimes that's one; sometimes a few. If the idea already covers outcome + success + scope, ask nothing and go straight to assembly.

- **Batch them.** Ask everything you need in one round, not a drip.
- **Lead with outcome and success signal.** If the outcome is vague, that is question one — nothing else matters until the destination is clear.
- **Offer a default with every question** so the user can accept fast (e.g. "responsive, or mobile-first?"). Defaults mirror the loop's infer-and-state habit.
- **Don't ask what the run already handles.** Never ask about stack, architecture, testing, deployment, or fine persona detail — the autonomous run owns those. Don't ask the user to write a rubric; you derive the success signal *with* them.
- **Infer over interrogate.** If a field is reasonably inferable from the idea, infer it and state the assumption instead of asking. Skip low-leverage fields.

## 4. Assemble the goal

Render a short goal with this skeleton. Keep it outcome-first and within a tight character budget — every extra word competes for compliance.

```text
/goal Build <thing> so <persona> can <outcome> when <moment of use>.
Success: <1-2 observable signals that it works well>.
Use <kit> on <mobile | tablet | desktop | responsive>.
Don't <guardrails>.
```

- Cut anything about *how* to build it.
- Drop vague quality words ("modern", "beautiful", "great UX") — let the success signal carry quality.
- Include hard constraints only when they exist; omit empty fields rather than padding.

## 5. Deliver

Present the finished goal in a code block, ready to paste after `/goal`. Save a copy to `etc/loop/<slug>.md` (a 3-5 word dash-separated slug; create the directory if needed) so it's reusable.

Then run a fast self-check and fix in place:

- Could a stranger tell whether the result met the goal? If not, the success signal is too weak.
- Is there anything about *how* to build it? Cut it.
- Is it short enough to live within a goal's character budget?

## Success criteria

- Gaps identified against the goal fields before any question is asked.
- Only high-leverage, batched questions asked — none about stack, testing, deployment, or persona detail.
- Final goal is short, outcome-focused, and gradeable, following the skeleton above.
- Saved to `etc/loop/<slug>.md` and presented ready to paste.
