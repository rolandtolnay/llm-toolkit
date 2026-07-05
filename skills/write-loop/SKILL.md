---
name: write-loop
description: Turn a rough idea into a short, outcome-focused /goal prompt for an autonomous run — greenfield or brownfield. Detects what's missing, asks only the high-leverage questions to close the gaps, and assembles a gradeable goal.
disable-model-invocation: true
---

Turn a rough idea into a strong `/goal` — the short prompt a user pastes to kick off an autonomous run and walk away from.

The user hands you a half-formed idea. You find the gaps that would make the run guess badly, ask only the high-leverage questions to close them, and hand back a short, outcome-focused goal.

Why the goal can be short: it is **not** a PRD. Describe *what* and *why*; never spend the user's words on *how*. The run fills the detail itself — in a new project by deriving sensible defaults, in an existing one by reading the codebase. Your only job is to make the *destination* unambiguous so the run can build the road.

## 1. Capture the idea and detect the mode

Take the user's message as the raw goal. If they gave nothing, ask once: "What do you want to build or change, and where — a new project, or an existing one?"

Decide which mode you're in; it changes the fields and the skeleton:

- **Greenfield** — a net-new project or standalone app. The run chooses the stack and conventions.
- **Brownfield** — a change to an existing project (add / extend / fix a feature). The run must conform to what's already there, and must not break it.

If you can't tell from the idea, make resolving it your first question.

## 2. Find the gaps

Check the idea against the fields for your mode, in priority order. Mark each **present / vague / missing**.

**Both modes:**

1. **Outcome** (required) — what the user can do or see when it works, stated as a result, not a feature list. The run grades against this, so it must be concrete. In brownfield, state it as a delta from current behavior.
2. **Success signal** — how you'd know it's good. Becomes the metric (see step 3).
3. **Tail coverage** — a bare success signal exits at "mostly good," leaving the long tail (edge cases, missing states, rough edges) for the user to discover in use. For a product the user will live with, the goal should demand a derived eval before building (realistic + edge cases) and/or a soak after (use the product as the persona; fix every friction found).
4. **Guardrails** — what *not* to build, change, or touch.
5. **Hard constraints** — only if real: a required integration, specific data, a must-have feature.

**Greenfield only:**

6. **Who & when** — the person and the moment of use. A few words; the run expands it into a persona.
7. **Design kit + target device** — which kit under the design-systems dir, and mobile / tablet / desktop / responsive.

**Brownfield only:**

6. **Anchor** — which existing feature, area, or module the change attaches to, so the run starts in the right place instead of wandering.
7. **Regression boundary** — the existing behavior that must keep working. This is the brownfield safety field, not optional scope hygiene.
8. **Conventions** — an exemplar to match ("follow the pattern in `<existing thing>`") so the run extends the codebase instead of inventing a second way. UI matches the existing app, not a new kit.

## 3. Ask only the high-leverage gaps

Ask the fewest questions that turn a vague idea into a gradeable goal. Sometimes one; sometimes a few. If the idea already covers the required fields, ask nothing and go straight to assembly.

- **Batch them.** Ask everything you need in one round, not a drip.
- **Lead with outcome and success signal.** If the outcome is vague, that is question one.
- **Offer a default with every question** so the user can accept fast.
- **Don't ask what the run can discover.** Never ask about stack, testing, deployment, or persona detail. In brownfield the run reads the repo, so don't ask about existing conventions it can find — but **do** surface what it *can't* infer: the regression boundary and any off-limits areas.
- **Infer over interrogate.** If a field is reasonably inferable, infer it and state the assumption instead of asking.

**Pick the metric deliberately.** In brownfield, prefer the project's existing automated checks — tests, types, build — as the success signal ("existing checks stay green + new behavior verified"), and reach for a subjective judge only for the genuinely un-testable parts. In greenfield, the success signal is usually a short rubric the run judges against. Match the instrument's resolution to what the user will notice: a self-judged rubric passes at "the feature works" and is blind to the fine-grained flaws — spacing, awkward flows, missing empty states — the user sees in the first ten minutes of use. When polish matters, give the run an instrument that can see at that resolution: drive the real product, compare screenshots against the kit, diff against a reference.

**Flag irreversibility.** If the change is mostly schema, data migration, auth, or a public API, say so: a hands-off loop may be the wrong tool, and the work may want a reviewed plan instead. Surface this rather than silently emitting a loop.

## 4. Assemble the goal

Render a short goal with the skeleton for your mode. Outcome-first, tight character budget — every extra word competes for compliance.

**Greenfield:**

```text
/goal Build <thing> so <persona> can <outcome> when <moment of use>.
Success: <1-2 observable signals that it works well>.
Use <kit> on <mobile | tablet | desktop | responsive>.
Don't <guardrails>.
```

**Brownfield:**

```text
/goal <Add|Change|Fix> <capability> in <existing area> so <users> can <outcome>.
Success: <observable signal>; existing behavior still works (existing checks green).
Match the conventions in <exemplar / area>.
Don't break <regression boundary>; don't touch <off-limits>.
```

- Cut anything about *how* to build it.
- Drop vague quality words ("modern", "beautiful", "great UX") — let the success signal carry quality.
- Omit empty fields rather than padding.
- For a product the user will live with, add the tail-coverage line(s): "Before building, derive ~<N> realistic and edge cases into `etc/loop/<slug>-eval.md`; done when ≥<bar> pass." and/or "After building, use it as <persona> through real tasks; fix every friction until a full pass finds none."

## 5. Deliver

Present the finished goal in a code block, ready to paste after `/goal`. Save a copy to `etc/loop/<slug>.md` (a 3-5 word dash-separated slug; create the directory if needed) so it's reusable.

**Default to one artifact.** A well-formed goal is short and fits in one file. If — *after* cutting every trace of "how" — the goal still overflows the 4,000-char cap (only large, multi-slice, greenfield unattended builds should), split into two files instead of shaving meaning:

- `etc/loop/<slug>.md` — the **brief**: the run's opening prompt (unbounded). Holds only run-specific "how" that isn't derivable and isn't already in the repo — slice order, which kit to port, eval-before / soak-after demands, docs to maintain.
- `etc/loop/<slug>-goal.md` — the compact `/goal` **completion condition** (under 4,000), which the user pastes. Its first line points the run at the brief.

Before writing the brief, point the condition at the project's existing docs (PROJECT.md, playbook.md, AGENTS.md) and put in the brief *only* what those don't already carry. If the brief is mostly restating standing repo docs, you haven't cut enough — a bloated brief is the same failure as a bloated goal, just relocated.

Then run a fast self-check and fix in place:

- Could a stranger tell whether the result met the goal? If not, the success signal is too weak.
- Would the run exit while the product still has rough edges the user would find in the first ten minutes of use? If yes, add the eval or soak demand.
- Is there anything about *how* to build it? Cut it.
- Brownfield: does it name what must not break?
- Is it short enough to live within a goal's character budget? The `/goal` evaluator caps the condition at **4,000 characters** — if you're near it, you're almost certainly still carrying "how"; cut it before anything else.

## Success criteria

- Mode identified, and gaps checked against that mode's fields before any question is asked.
- Only high-leverage, batched questions asked — none about stack, testing, deployment, or persona detail.
- Metric chosen deliberately (existing checks in brownfield, rubric in greenfield), tail coverage considered for products the user will live with, and irreversible changes flagged.
- Final goal is short, outcome-focused, and gradeable, following the right skeleton.
- Saved to `etc/loop/<slug>.md` and presented ready to paste.
