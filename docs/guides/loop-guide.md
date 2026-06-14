# Loop Guide

How to turn a pile of requirements into a single prompt you can hand to an autonomous run (e.g. a `/goal` command) and walk away from. Such a prompt is not a task description — it's a **loop**: you define what "done" means, how the run checks its own work, and how far it can go alone, then it cranks until it's there.

This is a first-principles guide. It is model-agnostic: a loop written this way should run well on any current frontier model. It carries the instruction lines you'll actually paste, so it stands alone.

---

## What a loop is

A prompt is a single ask you hand-crank: ask, read, refine, repeat — you're in the driver's seat every turn. A loop is the machine that cranks for you. It works because a capable model can hold a long, ambiguous, multi-step task and self-correct; your job moves from executing each step to designing the machine. You design three things:

1. **Objective** — what "done well" looks like, in one sentence, stated as an outcome you can observe from the outside (not the steps to get there).
2. **Metric** — how the *run itself* tells whether a pass came out better or worse, without you reading every word.
3. **Boundary** — what it can do alone, and where it must stop and check with you.

Get these three right and you stop babysitting: the loop asks, checks its own work against the metric, adjusts, and keeps going. The prompt doesn't disappear — the loop is still made of prompts. You've just stopped writing each one by hand.

---

## A loop that runs vs. a loop that learns

A loop that **runs** does the same thing every pass — automation. A loop that **learns** feeds each pass's result back into the next, so it compounds. Aim for the second whenever the task repeats.

The difference is one **feedback wire**: a place where the outcome of a pass changes what the next pass does. A classifier whose verdicts build a list that shrinks next run's work; a draft scored low that becomes a note the next draft reads; a flagged item a human corrects, and the correction persists. Same loop, plus a wire, gets smarter every use.

When you write the prompt, ask: *is there a cheap signal at the end of each pass that should change the next one?* If yes, name it explicitly and give it somewhere to persist — a file, a table, a list. That one sentence is often the highest-leverage line in the whole prompt.

---

## The metric is the hard part

Objective and boundary are usually easy to write. The metric is where most loops quietly fail. If you can't say how the run grades its own pass, you haven't finished designing the loop — you've found the real work. The question to answer: *how would it know a pass came out better or worse, without you reading every word?*

Four ways to give a loop a metric, cheapest to richest. Pick the strongest one the task allows; combine them when you can.

1. **Self-score against explicit criteria.** The run scores its own output against named criteria and redoes anything below a bar. *"After each pass, score 1–10 against: [criterion A], [B], [C]. Below [9], critique and redo. Up to [N] passes, then return the best."* Cheap, fully autonomous, needs no ground truth — but only as good as the criteria you name.
2. **Run real validation.** When the output is checkable by a tool, make the check part of the loop: tests for changed behaviour, type/lint checks, a build, or a minimal smoke test when full validation is too expensive. If validation can't run, the loop should say why and describe the next best check.
3. **Independent verification.** Have a fresh, separate context check the work against the spec — a verifier that didn't produce the output. This catches what self-critique misses, because the doer tends to rate its own work generously. Run it at an interval as the work builds, not just at the end.
4. **Ground-truth oracle + confidence flag.** When the truth is cheaply inspectable, check output against the real data and *flag* what's uncertain instead of guessing. The flag converts the unsure cases into a human feedback wire (see *learns vs. runs*).

Whatever you pick, make honest reporting part of it: the run should audit each progress claim against an actual result before reporting it, and say plainly when something isn't verified or a step was skipped. And write the exit as **the metric satisfied, not a step count** — that's what makes a real stopping condition.

---

## The prompt template

A reusable skeleton. Keep it outcome-first: say what you want from your side and the constraints that matter, then let the run choose the path.

```markdown
# <Project> — <one-line outcome>

## Why
One short paragraph, first person: the problem you actually have, and what
this is the engine for. Intent lets the run connect the task to the right
context instead of guessing it.

## What I want (from my side)          ← the OBJECTIVE
Bullets describing the experience YOU get, not the implementation.
"I run it and it produces X." "I open it and see Y."
Each bullet is observable from outside the system.

## It should get smarter the more I use it   (only if it's a loop that learns)
Name the feedback wire: what signal each pass produces, how it changes the
next pass, and where it persists.

## Constraints / Locked decisions
Only the constraints that must not be re-litigated: language, key services,
a hard rule (e.g. a cost or privacy limit). Lock as little as possible —
every locked line is a path the run can no longer optimize.

## How to work                          ← the BOUNDARY + working style
- Operate autonomously; organize the work yourself. Don't end a turn on a
  plan or a promise — do the work.
- Stop only for <the genuinely irreversible / blocked cases>.
- Ground every claim in real results; if something isn't working, say so.
- Build the simplest thing that works; don't add what I didn't ask for.

## Done when                            ← the METRIC satisfied
An observable end state, not a step count.
"Done when I can <do the thing> against real data and <the quality bar holds>."
```

Where the three ingredients live: `What I want` + `Done when` carry the **objective**; `Done when` plus the grounding line carry the **metric**; `How to work` carries the **boundary**; the "gets smarter" section is the **learning wire**.

---

## Writing principles

These hold regardless of which model runs the loop.

- **Outcome-first, not steps.** Describe the destination and let the run find the path. Over-specifying the process narrows its search space and produces mechanical work; capable models do better with room. State *what good looks like*, *what's available*, and *what the result must contain*.
- **Decision rules over absolutes.** Reserve ALWAYS / NEVER / must for true invariants — safety, a hard cost/privacy rule, required output fields. For judgment calls (when to ask, when to keep iterating, which tool to reach for), give a decision rule, not a command.
- **Lock as little as possible.** Put genuinely settled trade-offs in `Constraints` so the run doesn't re-open them; leave everything else open. Over-locking turns a loop back into a checklist.
- **Ground in real data, not fixtures.** A loop tuned on made-up cases passes on made-up cases. Real inputs are also what make a ground-truth metric and honest progress claims possible.
- **State the boundary by irreversibility.** Let it proceed on reversible actions that follow from the request; stop only for destructive/irreversible actions, real scope changes, or input only you can provide. This is where your risk tolerance lives — be explicit so it neither stalls for permission nor barrels through something it shouldn't.
- **Delegate bulky, repetitive work.** The run's own context is precious. Push high-volume or repetitive sub-work to subagents or cheaper passes and keep the main loop reasoning over summaries. Set a budget for expensive operations (searches, full-content reads) so it stops gathering once it has enough.
- **Give it examples of good.** If you have examples of the output you want, attach them. A few good examples shape results more than another paragraph of instruction.
- **Keep it tight.** Instruction budget is finite — each behavioral instruction competes with the others for compliance, so adding one dilutes the rest. Cut any line that doesn't change behaviour. Drop motivational filler ("this is important"); it adds load and changes nothing.
- **Slice vertically.** Don't write one mega-loop. Split into a sequence where each slice is independently runnable and leaves something working, with its own `Done when`. Each slice can then be ambitious because it's bounded.

---

## Paste-ready instruction lines

Neutral, load-bearing lines for the `How to work` section. Use the ones your loop needs — don't paste all of them; each one competes for compliance.

**Autonomy / don't stall:**
```text
You are operating autonomously; the user is not watching and cannot answer mid-task.
For reversible actions that follow from the request, proceed without asking. Before
ending a turn, check your last paragraph: if it's a plan, a question, a list of next
steps, or a promise ("I'll…"), do that work now instead. End only when the task is
complete or you're blocked on input only the user can provide.
```

**Boundary / checkpoint:**
```text
Stop for the user only when the work genuinely requires it: a destructive or
irreversible action, a real scope change, or input only they can provide. If you hit
one, ask and end the turn rather than ending on a promise.
```

**Act, don't over-plan:**
```text
When you have enough information to act, act. Don't re-derive settled facts,
re-litigate a decided choice, or narrate options you won't pursue. If weighing a
choice, give a recommendation, not a survey.
```

**Simplest thing:**
```text
Don't add features, refactor, or introduce abstractions beyond what the task needs.
Do the simplest thing that works; don't build for hypothetical future requirements.
Validate only at system boundaries; trust internal code.
```

**Ground progress claims:**
```text
Before reporting progress, audit each claim against an actual result from this run.
Report only work you can point to evidence for; if something isn't verified, say so.
If a check fails, say so with the output; if a step was skipped, say that.
```

**Self-verification:**
```text
Establish a way to check your own work as you build, and run it at an interval against
the spec — preferably with a fresh, separate context rather than self-critique.
```

---

## Checklist before you run it

1. **Objective** — Can I state "done well" in one sentence, observable from my side?
2. **Metric** — Can the run tell a good pass from a bad one *without me reading every word*? Self-score, validation, independent verification, or ground-truth oracle — which, and is it written down?
3. **Boundary** — Is it clear what runs alone and what stops to check in, phrased around irreversibility?
4. **Learning wire** — If this repeats, is there a feedback signal that compounds, with somewhere to persist?
5. **Outcome-first** — Did I describe results, not steps? Did I avoid needless absolutes?
6. **Grounded** — Will it tune against real data and audit claims against real results?
7. **Tight** — Is every line earning its place?

If 1–3 are solid you have a loop. Add 4 and it learns. The rest is craft.

---

*Synthesized from the "write a loop, not a prompt" idea and general LLM-prompting principles. Model-specific tuning (effort settings, refusal handling, a given model's defaults) belongs in that model's own prompting guide, not here.*
