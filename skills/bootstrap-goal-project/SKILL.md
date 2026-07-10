---
name: bootstrap-goal-project
description: Set up or repair a repository's durable documentation system for independent autonomous goal runs. Use when starting a project that future LLM runs should continue without chat history, adapting the hobby-bundle goal loop to a different stack, adding PROJECT.md/CONTEXT.md/AGENTS.md/playbook/goal-log/judge infrastructure, or auditing whether an existing repository preserves decisions and evidence across runs.
---

# Bootstrap a Goal-Driven Project

Create the project-local memory and operating system that lets a cold autonomous run discover intent, use the project's language, execute safely, verify the outcome, and leave durable evidence for the next run.

Keep the repository files canonical. This skill installs and adapts the system; future runs must not depend on this skill remaining available.

## 1. Inspect before writing

1. Capture `git status --short` and preserve unrelated changes.
2. Read the repository root, build manifests, test configuration, existing agent instructions, product docs, decision records, and delivery scripts.
3. Classify the task:
   - **Initialize:** the foundation is absent.
   - **Complete:** some contracts exist but the run record or method is missing.
   - **Repair:** files exist but duplicate responsibilities, contain stale stack assumptions, broken links, placeholders, or unsafe instructions.
4. Read [references/foundation-contract.md](references/foundation-contract.md) before designing the file set.
5. Treat overlap with pre-existing user edits as a blocker. Never replace an existing artifact wholesale when a narrow merge preserves its intent.

## 2. Establish product intent

`PROJECT.md` is the highest-value artifact because it resolves product forks the task prompt does not cover.

- If `PROJECT.md` is strong, preserve it and extract its priorities, constraints, exclusions, and default judgments.
- If it is missing or vague, follow the `new-project` workflow when available. Otherwise, ask only for private judgment the repository cannot reveal: core value, intended users, non-goals, constraints, and tradeoff preferences.
- If the current conversation and repository already answer those questions, synthesize without repeating an interview.
- Do not invent product intent from implementation conventions.

Dry-run three to five plausible project-specific forks. Strengthen `PROJECT.md` until a cold run can resolve them consistently.

## 3. Adapt the foundation

Use `assets/project-foundation/` as contracts, not files to copy blindly. Read every template whose destination you will create or repair, then specialize it to the repository.

Create or reconcile:

- `PROJECT.md` — product intent and product decisions.
- `CONTEXT.md` — domain glossary only.
- `AGENTS.md` — short routing layer, standing locks, boundaries, and exact verification entry points.
- `docs/decisions.md` and lazy `docs/adr/` — implementation decision memory.
- a project-specific setup/facts document when external services, toolchains, signing, deployment, or local environment facts matter.
- `docs/goal-log.md` — append-only run record.
- `docs/goal-evidence/README.md` — retention rules for compact evidence.
- `etc/playbook.md` — stack-specific build, verify, mutation, blocker, and release method.
- `etc/judged-goal-loop.md` — fresh-context judging contract.
- `etc/writing-goals.md` — local goal-writing guide and copy-paste skeleton.

Adapt explicitly:

- replace generic commands with commands proven by repository configuration;
- name real test and product-driving surfaces: browser, native app, CLI, API, device, simulator, or fixtures;
- separate a normal verified build from deployment or release;
- define fatal blockers and irreversible or externally mutating boundaries;
- require an initial working-tree baseline and protection of unrelated changes;
- keep secrets and bulky transient output out of tracked memory;
- retain only evidence that supports a verdict or future decision;
- encode subagent model economy: keep goal ownership and high-judgment integration with the frontier model, while bounded verifiable work defaults to the least costly lower-tier model that remains comfortably capable;
- add project-specific canonical sources only when they own a distinct kind of truth.

Keep responsibilities non-overlapping. `AGENTS.md` routes; `PROJECT.md` decides product questions; `CONTEXT.md` names the domain; the playbook defines method; the goal log records what happened.

## 4. Wire the run lifecycle

Make this cold-start path obvious from `AGENTS.md`:

```text
goal prompt
  -> PROJECT.md / CONTEXT.md / decisions
  -> etc/playbook.md
  -> docs/goal-log.md + compact evidence
  -> fresh judge
  -> GOAL MET or explicit [blocked]
```

Every autonomous run must:

1. read canonical sources before choosing defaults;
2. persist the exact goal, baseline, assumptions, rubric, and guardrails;
3. build the smallest vertical slice;
4. run only applicable configured checks;
5. use a fresh judge when user-visible quality, trust, or irreversible behavior is in scope;
6. log judge findings, fixes, rejected findings, and final state;
7. stop only at `GOAL MET` or an explicit `[blocked]` condition;
8. commit, deploy, release, or mutate external systems only when the goal authorizes it.

Use the `write-loop` skill after bootstrap when available to turn rough work into the first outcome-focused goal.

## 5. Validate the cold start

Inspect the finished repository as if no chat history exists.

Verify:

- all referenced paths exist;
- no template placeholder remains;
- commands match the actual repository;
- canonical-source precedence is explicit and non-circular;
- domain terms do not conflict across files;
- setup facts contain no secrets;
- the goal log is append-only and has a usable entry template;
- evidence policy distinguishes tracked proof from ignored transient output;
- failure policy names genuine blockers without converting preferences into blockers;
- mutation, deployment, and release authority are not implied by a build goal;
- a future run can find product intent, implementation method, current run history, and the next safe action without this conversation.

Report the files created or repaired, the key project-specific adaptations, exact validation performed, and any remaining user-owned decisions. Commit only when requested.

## Success criteria

- A single explicit invocation can initialize or repair the complete foundation without erasing existing project knowledge.
- The resulting files are project-specific, linked, concise, and usable without the skill or prior chat.
- Product intent, domain language, implementation decisions, run history, evidence, and delivery method each have one clear owner.
- A fresh autonomous run has a deterministic route to `GOAL MET` or `[blocked]` and leaves the next run better informed.
