# <Project name> — agent working notes

Standing method for this repository. The task-specific outcome comes from the prompt.

## Canonical sources

- Product intent, scope, and product decisions → `PROJECT.md`.
- Domain language → `CONTEXT.md`.
- Lightweight implementation decisions → `docs/decisions.md`; hard-to-reverse tradeoffs → `docs/adr/`.
- Non-secret environment and delivery facts → `<project-specific setup document>`.
- Goal history and judge evidence → `docs/goal-log.md` and `docs/goal-evidence/`.
- Full build and verification method → `etc/playbook.md`.
- Judged goal loop and goal-writing guidance → `etc/judged-goal-loop.md` and `etc/writing-goals.md`.

When guidance conflicts: explicit user goal > `PROJECT.md` > ADRs/decisions > playbook defaults.

## Standing locks

- <Non-negotiable product or safety boundary.>
- <Canonical source or design-system rule.>
- <External mutation, data, or security boundary.>

## Stack and boundaries

<One concise stack statement and the important module/effect boundaries.>

Build the smallest vertical slice that meets the goal. Do not add adjacent features, abstractions, infrastructure, or release work without outcome pressure.

## Verify

Run only configured and applicable checks:

```bash
<exact command discovered from the repository>
```

Report exact results. Use a fresh judge for user-visible, trust-sensitive, or otherwise non-deterministic outcomes according to `etc/judged-goal-loop.md`.

## Commits, external effects, and blockers

Record the initial working-tree status, preserve unrelated changes, and treat overlap with pre-existing user edits as a blocker. Commit only when requested. A completed build does not imply deployment or release.

Treat <project-specific fatal conditions> as blockers. Leave the tree recoverable, record `[blocked]` in `docs/goal-log.md`, and report the exact condition and safest resume step.
