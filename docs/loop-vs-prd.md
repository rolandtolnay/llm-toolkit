# Loop vs. PRD — when to reach for each

The decision isn't really "feature vs change" or "big vs small." It's **who can hold the correctness judgment, and whether you can stop watching.** Almost everything else falls out of that.

## The question that routes most cases

*Can the run tell a good result from a bad one without you reading every word?*

- If correctness is something only *you* can judge each pass — taste, product/UX feel, a contested business tradeoff — then **you are the metric**, and autonomy is a trap. Write a **PRD**. The grilling buys shared understanding, the spec is a durable record, and TDD plus human review put your judgment at the gates where it actually lands.
- If correctness can be *encoded* — tests, a build, a verifier, a ground-truth oracle — then the machine can hold it and you can hand off. Now it's only a question of *which* encoding.

## Tests vs. metric — the real PRD/TDD-vs-loop split

- If you can **enumerate** correctness up front as discrete behaviors, write them as tests. That's the PRD→plan→TDD path: the suite is the contract, a human reviews the assembly. Best for novel or important one-off work where you want to inspect the seams.
- If you **can't enumerate but can grade** — score against criteria, "better than last pass," validate against real data and flag the unsure ones — that's a **loop**. The run grades itself and cranks until the metric holds, with you out of the chair.

## Two tuners settle the borderline

- **Recurrence.** One-shot leans PRD; anything that runs over many items or repeats over time leans loop — and if each pass can teach the next (a learning wire), that's the strongest loop signal there is. Repetition is what pays back the cost of designing the machine.
- **Blast radius.** High irreversibility (schema/data migrations, security, public API, foundational architecture) leans PRD. A loop's boundary is literally "stop for irreversible," so a task made mostly of irreversible calls just halts at every one. Reversible, fenced work runs fine autonomously.

## The tells you picked wrong

- You sit down to write the loop and can't write the metric → it's a PRD. You're the grader; stop pretending otherwise. (The loop-guide is blunt about this: no metric means you haven't finished designing the loop, you've found the real work.)
- You sit down to write the PRD and the "implementation decisions" are just "do X to each of N things, check it compiles" → it's a loop. You're adding ceremony to a crank.

## Don't force one tool on the whole idea

Most real features decompose: PRD the architecturally load-bearing spine (the irreversible decisions, the "why" worth recording), loop the repetitive, gradable fill-in. Both slice vertically anyway, so the seam is natural — you can even hand the loop a slice the PRD already specified.

## Concrete cases, roughly how I'd call them

- Greenfield feature with schema, several surfaces, a team to maintain it → **PRD**.
- Cross-cutting mechanical migration (rename an API across 60 files, dependency bump with fixups) → **loop**, metric = build/tests green.
- Recurring ops or content task (nightly PR triage, ticket classification, release notes) → **learning loop** with a feedback wire.
- Bug with a reproducible failure → just **TDD** it; the failing test is the spec. Escalate to a PRD only if the root cause or fix is contested.
- "Make this screen feel right" → neither, honestly; only your eye grades it, so iterate by hand (or a loop with render-and-inspect, but you stay the final judge).

## The baseline worth saying out loud

If it's small, clear, and reversible, skip both and just build it. The PRD and the loop are both machinery you have to *earn back* — through significance and review on one side, autonomy and repetition on the other. Reach for them when the idea is big or ambiguous or repeated enough to justify the artifact, not by reflex.
