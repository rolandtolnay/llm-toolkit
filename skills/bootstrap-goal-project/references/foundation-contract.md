# Goal-driven project foundation contract

Use this reference to decide which repository files to create and what each one owns. The filenames are defaults; preserve a repository's established equivalents when their responsibility is already clear.

## Ownership map

| Artifact | Owns | Must not become |
|---|---|---|
| `PROJECT.md` | Product identity, core value, users, scope, constraints, default judgments, product decisions | Build instructions or an implementation diary |
| `CONTEXT.md` | Canonical domain vocabulary and concise definitions | A behavior spec or architecture guide |
| `AGENTS.md` | Source precedence, standing locks, boundaries, routing, concise verify entry points | A duplicate of every canonical document |
| `docs/decisions.md` | Lightweight non-obvious implementation decisions and revisit conditions | Product roadmap or chronological work log |
| `docs/adr/` | Hard-to-reverse, surprising decisions with real alternatives | A destination for routine choices |
| setup/facts doc | Non-secret observed toolchain, service, environment, release, or deployment facts | Secrets, aspirations presented as observed facts, or product policy |
| `docs/goal-log.md` | Append-only goals, baselines, assumptions, rubrics, checks, judge passes, fixes, completion/blocker state | A scratchpad, full raw logs, or rewritten history |
| `docs/goal-evidence/` | Small tracked artifacts necessary to support a verdict | Build caches, secrets, real user data, or full transient logs |
| `etc/playbook.md` | Standing build, verification, mutation, failure, deployment, and release method | Product intent or one goal's checklist |
| `etc/judged-goal-loop.md` | Rubric shape, fresh-judge protocol, evidence expectations, stopping rules | A generic demand for subjective self-review |
| `etc/writing-goals.md` | How this project expresses a small outcome-oriented goal | A restatement of the playbook |

## Source precedence

Use this default and specialize only when the project has a stronger recorded hierarchy:

```text
explicit user goal
  > PROJECT.md product intent
  > ADRs and recorded decisions
  > playbook and AGENTS.md defaults
  > inference
```

Official external documentation and current observed behavior beat memory for volatile compatibility facts. Record review dates when drift matters.

## Minimum versus optional

Minimum for independent goal runs:

- `PROJECT.md`
- `AGENTS.md`
- `docs/goal-log.md`
- `etc/playbook.md`

Add `CONTEXT.md` when the project has domain terms. Add a judge loop when correctness includes user experience, product effectiveness, trust, or behavior not captured by deterministic tests. Add evidence retention when a fresh judge needs screenshots, fixture comparisons, traces, or other proof. Add setup/facts and compatibility documents when the project depends on external or volatile state.

The full foundation is appropriate for a project expected to span many unattended runs. A tiny library or disposable script may need less ceremony.

## Subagent model economy

Record this in the project playbook when the harness supports model selection:

- Keep the frontier goal owner responsible for product judgment, architecture, safety boundaries, integration, and final synthesis.
- Delegate bounded work to the least costly lower-tier model that remains comfortably capable. Default one tier down for substantial scoped work and two tiers down for routine research, exploration, fixture enumeration, mechanical edits, and objective checks.
- Treat names as current examples rather than durable policy: Fable may delegate to Opus 4.8 or, for narrow verifiable work, Sonnet 5; Sol may delegate to Terra or, for routine research and exploration, Luna.
- Supply minimum sufficient context, explicit constraints, a bounded deliverable, and a verification contract. The goal owner reviews and integrates the result.
- Keep ambiguous product forks, cross-cutting architecture, destructive or external mutation, and hard-to-detect failure modes at owner or peer capability. Escalate after an uncertain or failed pass.

The durable rule is capability-aware delegation, not a fixed alias ladder. Resolve the current model hierarchy at run time.

## Adaptation rules

1. Derive stack and commands from repository evidence; do not carry assumptions from the source template.
2. Preserve existing canonical documents and merge narrowly.
3. Keep canonical content readable outside a particular LLM harness.
4. Make completion falsifiable. `GOAL MET` requires evidence; `[blocked]` requires an exact condition and resume step.
5. Keep a normal build local unless the goal separately authorizes deployment, release, external messages, billing, credentials, or destructive mutation.
6. Use fixture or temporary copies for destructive tests. Never weaken a real safety boundary to make automation convenient.
7. Record observed facts, documented behavior, and inference separately when confusing them would break trust.

## Cold-start questions

The foundation passes when a new run can answer these without chat history:

1. What product outcome wins when requirements conflict?
2. Which terms and boundaries does this codebase use?
3. Which decisions must not be reopened casually?
4. What exact commands and surfaces verify a change?
5. What may the run mutate, deploy, or release without new authority?
6. Where does it record assumptions, evidence, findings, and blockers?
7. How does it know the goal is genuinely complete?
