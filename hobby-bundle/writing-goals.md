# Writing a strong `/goal`

How to write the short prompt that kicks off a one-shot hobby project. Pair this with `playbook.md` (the stack and delivery) and `judged-goal-loop.md` (how the run grades itself).

## Why short works

A `/goal` is not a PRD, and it has a character budget. You do not need one, because the loop *is* the spec: it derives a persona, writes a falsifiable rubric, builds, then judges the real running app on UI/UX **and** product effectiveness, iterating until the outcome holds. Your job is to set the destination clearly. The loop finds the road.

So underspecify the *how* and overspecify the *what* and *why*.

## The one rule

**Describe the outcome, not the implementation.** What should be true for the user when this is done? Everything else is support for that sentence.

- Weak: "Build a habit tracker app with React, accounts, and a nice UI."
- Strong: "So I can mark my daily habits done in under five seconds each morning and see my streaks at a glance."

The strong version is gradeable. The weak version makes the loop guess what "nice" means.

## What to include, in priority order

Spend your characters top-down; stop when you run out.

1. **Outcome** — what the user can do or see when it works. Non-negotiable.
2. **Who and when** — a few words on the person and the moment of use. Seeds the persona.
3. **Success signal** — how you'll know it's good. This becomes the rubric.
4. **Design kit + target device** — one line; name the kit and the surface so the loop doesn't guess.
5. **Guardrails** — what *not* to build or touch. Keeps the loop's "outcome-essential additions" from drifting.
6. **Hard constraints** — only if real: a required integration, specific data, a must-have feature.

## What to leave out

The playbook and loop already own these — naming them wastes budget:

- The stack (Next.js + Firebase + Vercel), file layout, libraries, "use TypeScript."
- Testing, deployment, auth wiring, env vars, hosting.
- Vague quality words: "modern," "beautiful," "great UX," "responsive." They aren't falsifiable; let the success signal and the judge carry quality.
- Step-by-step instructions. If you're writing steps, you're writing a PRD.

## Skeleton

```text
/goal Build <thing> so <persona> can <outcome> when <moment of use>.
Success: <1-2 observable signals that it works well>.
Use <kit> on <mobile | tablet | desktop | responsive>.
Don't <guardrails: features or areas to avoid>.
```

## Worked example

```text
/goal Build a habit tracker so I can mark daily habits done in under five
seconds and see my current streaks the moment I open it, half-awake before
coffee on my phone. Success: today's habits show first, one tap marks done,
streaks are obvious without scrolling. Use the calm-paper-kit on mobile.
Don't add social features, reminders, or analytics.
```

Short, outcome-focused, gradeable — and the loop fills in persona detail, architecture, tests, and deploy on its own.

## Quick check before you send

- Could a stranger tell whether the result met the goal? (If not, add a success signal.)
- Is anything in there about *how* to build it? (If so, cut it.)
- Did you name what to avoid? (One guardrail line saves a wasted iteration.)
