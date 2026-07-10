# Goal-driven project foundation

> A repository-local memory and delivery system for autonomous LLM runs, with the hobby web stack as a worked example.

## What This Is

This directory contains the original Next.js, Firebase, and Vercel version of a goal-driven project loop. Its useful part is broader than that stack: product intent, domain language, decisions, run history, evidence, and delivery method live in the repository so each cold LLM run can continue from durable state instead of chat history.

For a new project, use the [`bootstrap-goal-project`](../skills/bootstrap-goal-project/SKILL.md) skill. It treats these files as an example, inspects the target repository, and writes a project-specific foundation without carrying over web-only assumptions.

## Quick Start

Install `llm-toolkit`, open the target repository, and ask your agent:

```text
Use $bootstrap-goal-project to set up this repository for independent autonomous goal runs. Adapt the foundation to this project's actual stack, risks, verification surfaces, and release boundary. Preserve existing docs and unrelated changes.
```

If the product intent has not been captured yet, run `new-project` first. After bootstrap, use `write-loop` to draft the first outcome-focused goal.

## What's Included

- **`agent-instructions-template.md`** — Routes a run to canonical sources and standing locks.
  - Use when: comparing how a web project specializes `AGENTS.md`.
- **`playbook.md`** — Defines the original web stack's build, verification, deployment, and failure method.
  - Use when: adapting concrete delivery rules, not when choosing a new project's stack.
- **`judged-goal-loop.md`** — Defines fresh-context product and UI judging, evidence, iteration, and `GOAL MET`.
  - Use when: deterministic tests cannot establish the complete outcome.
- **`writing-goals.md`** — Turns product outcomes into short, gradeable `/goal` prompts.
  - Use when: the standing method is already in the repository and the next run needs a destination.
- **Bundled skills** — Supply the web-specific research, design, testing, architecture, and deployment capabilities used by the original loop.
  - Use when: the target project shares those needs; do not install them as mandatory infrastructure.

## Copy-Paste Fallback Prompt

Use this with a capable coding agent when the bootstrap skill is unavailable. Run it from the new project's repository and keep the source path available.

```text
Set this repository up for independent, unattended, goal-driven LLM runs whose knowledge compounds through project files rather than chat history.

First inspect the repository, its existing documentation, build/test configuration, delivery scripts, and git status. Then read the source example at:
/Users/rolandtolnay/Documents/Development/llm-toolkit/hobby-bundle

Also inspect this more fully adapted example when it is available:
/Users/rolandtolnay/Documents/Development/harness-manager

Extract the reusable contracts from those examples, but do not copy their Next.js/Firebase/Vercel, Swift/macOS, design-system, testing, deployment, release, or filesystem assumptions into this project. Derive this project's rules from repository evidence and my stated intent.

Create or reconcile the smallest coherent foundation:
- PROJECT.md owns product identity, core value, users, scope, constraints, default judgments, and product decisions.
- CONTEXT.md owns the domain glossary only.
- AGENTS.md stays concise and routes agents to canonical sources, standing locks, boundaries, exact verification entry points, and blocker rules.
- docs/decisions.md owns lightweight implementation decisions; create docs/adr/ only when a hard-to-reverse tradeoff needs it.
- Add a non-secret setup/facts document only when external services, toolchains, deployment, signing, or release facts need a durable owner.
- docs/goal-log.md is an append-only record of each goal, initial working-tree state, assumptions, rubric, guardrails, implementation summary, checks, evidence, fresh judge passes, fixes, final verdict, and resume state when blocked.
- docs/goal-evidence/README.md defines what compact proof is retained and what transient or sensitive output stays ignored.
- etc/playbook.md defines this project's actual build, test, product-driving, mutation, failure, deployment, and release method.
- etc/judged-goal-loop.md defines when and how a fresh context judges user-visible, trust-sensitive, or otherwise non-deterministic outcomes.
- etc/writing-goals.md gives a short project-specific goal skeleton.

Use this precedence: explicit user goal > PROJECT.md > ADRs and recorded decisions > playbook/AGENTS defaults > inference. Keep observed facts, documented behavior, and inference distinct. A verified local build must not imply permission to commit, push, deploy, release, message people, change security/billing state, or mutate production data.

Encode capability-aware subagent delegation in the playbook. Keep the frontier goal owner responsible for product judgment, architecture, safety, integration, and final synthesis. Delegate bounded verifiable work to the least costly lower-tier model that remains comfortably capable: for example, Fable to Opus 4.8 or Sonnet 5, and Sol to Terra or Luna. Treat those names as current examples, resolve the available model ladder at run time, and escalate uncertain or failed work.

Preserve existing canonical content and unrelated changes. Merge narrowly rather than replacing files wholesale. Use exact commands proven by the repository. Remove every template placeholder and broken path.

Before finishing, simulate a cold run with no chat history. Verify it can determine: what product outcome wins a tradeoff; which domain language and decisions apply; what it may mutate; how to build and verify; where to record assumptions and evidence; how a fresh judge works; and whether to finish as GOAL MET or [blocked]. Report the files created or repaired, project-specific adaptations, exact validation performed, and unresolved user-owned decisions. Do not commit unless I ask.
```

## When Not to Use This

Skip the full foundation for disposable experiments or tiny scripts that will not span independent runs. Start with `PROJECT.md`, `AGENTS.md`, a short playbook, and a goal log when the project is durable but the full judge/evidence system has not earned its cost yet.
