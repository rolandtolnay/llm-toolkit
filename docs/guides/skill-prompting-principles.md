# Skill Prompting Principles

Principles extracted from Matt Pocock's engineering skills collection — a corpus of battle-tested Claude Code skills that demonstrate how to write prompts that produce disciplined, high-quality agent behavior.

## 1. Name the Discipline, Not the Tool

A skill prompt is not "instructions for an AI." It is a **discipline** — a set of constraints that a competent practitioner would follow. Frame the prompt as if briefing a senior engineer who needs reminding of the process, not teaching a student.

```
WEAK:  "You are a debugging assistant. Help the user find bugs."
STRONG: "A discipline for hard bugs. Skip phases only when explicitly justified."
```

The agent rises to the frame you set. "Discipline" produces rigor; "assistant" produces hand-holding.

## 2. Lead with the Bottleneck

Identify the single phase where most people fail and put disproportionate emphasis there. Everything else is "mechanical" — the bottleneck is "the skill."

From `/diagnose`:
> **This is the skill.** Everything else is mechanical. If you have a fast, deterministic, agent-runnable pass/fail signal for the bug, you will find the cause.

This pattern — declaring which part matters most and why — prevents the agent from distributing effort evenly across phases when one phase deserves 80% of the attention.

## 3. Explicit Phase Gates

Never let the agent drift between phases. Each phase ends with a gate condition that must be met before proceeding:

```
"Do not proceed to Phase 2 until you have a loop you believe in."
"Do not proceed until you reproduce the bug."
```

Gate conditions prevent the most common agent failure mode: optimistically assuming early work is done and charging ahead into implementation.

## 4. Ranked Options, Not Single Paths

When a phase requires choosing a technique, provide a ranked list ordered by preference. This gives the agent judgment without requiring it to invent options from scratch:

```
Try them in roughly this order:
1. Failing test
2. Curl / HTTP script
3. CLI invocation with fixture
4. Headless browser script
5. Replay a captured trace
...
```

The ranking encodes experience. The agent can deviate but knows what "normal" looks like.

## 5. Anti-Patterns Are Load-Bearing

Stating what NOT to do is as important as stating what to do. The agent has seen thousands of bad patterns in training data — you need to explicitly block the ones that look reasonable but produce bad outcomes.

```
DO NOT write all tests first, then all implementation.
This is "horizontal slicing" — treating RED as "write all tests"
and GREEN as "write all code." This produces crap tests.
```

Name the anti-pattern, explain why it's tempting, explain why it fails. This is more effective than just stating the correct approach alone.

## 6. Shared Vocabulary as Alignment Mechanism

Define a small glossary of terms and demand exact usage. This eliminates drift, ambiguity, and the agent substituting its own preferred terminology:

```
Use these terms exactly in every suggestion. Don't drift into
"component," "service," "API," or "boundary."

- Module — anything with an interface and an implementation
- Seam — where an interface lives
- Depth — leverage at the interface
```

Vocabulary activation works because language shapes thinking. When the agent must say "seam" instead of "boundary," it makes different design decisions.

## 7. Durability Over Precision

Artifacts produced by skills should survive codebase changes. Descriptions should reference interfaces, types, and behavioral contracts — never file paths, line numbers, or implementation details:

```
GOOD: "The SkillConfig type should accept an optional schedule field"
BAD:  "Open src/types/skill.ts and add a schedule field on line 42"
```

This principle applies to everything the agent writes: issues, PRDs, briefs, handoffs. If it would break after a rename refactor, rewrite it.

## 8. Behavioral Specification, Not Procedural

Describe what the system should do, not how to implement it. The agent should make implementation decisions after exploring the codebase — not follow a predetermined path:

```
GOOD: "When a user runs /triage with no arguments, they should see
       a summary of issues needing attention"
BAD:  "Add a switch statement in the main handler function"
```

Behavioral framing gives the agent room to find the best implementation for the current codebase state.

## 9. Vertical Slices Over Horizontal Layers

When breaking down work, each unit should cut through all layers end-to-end rather than completing one layer at a time:

```
Each slice delivers a narrow but COMPLETE path through every layer
(schema, API, UI, tests). A completed slice is demoable or
verifiable on its own.
```

This applies to TDD cycles, issue decomposition, and prototyping equally. Thin vertical slices produce working software at every step.

## 10. One Question at a Time

When a skill requires grilling/interviewing, enforce single-question discipline:

```
Ask the questions one at a time, waiting for feedback on
each question before continuing.
```

This prevents the agent from dumping a wall of questions that overwhelm the user and produce shallow answers. Sequential questions allow each answer to inform the next question.

## 11. Provide Recommended Answers

When asking the user a question, always include what you'd recommend:

```
For each question, provide your recommended answer.
```

This shifts the user's cognitive load from "generate an answer" to "evaluate a proposal." Faster convergence, better decisions, because the agent has already explored the codebase.

## 12. Defer to Evidence Over Conversation

When a question can be answered by reading code, read the code instead of asking:

```
If a question can be answered by exploring the codebase,
explore the codebase instead.
```

This prevents unnecessary back-and-forth and grounds decisions in reality rather than the user's (potentially stale) mental model.

## 13. Inline Side Effects as Decisions Crystallize

Don't batch documentation updates. When something becomes clear during a conversation, capture it immediately:

```
When a term is resolved, update CONTEXT.md right there.
Don't batch these up — capture them as they happen.
```

This prevents information loss between phases and ensures the codebase always reflects the latest understanding.

## 14. Explicit Scope Boundaries

Every task needs clear "out of scope" declarations. Without them, agents gold-plate:

```
State what is out of scope. This prevents the agent from
gold-plating or making assumptions about adjacent features.
```

Scope boundaries are especially critical for AFK agents that can't ask clarifying questions mid-task.

## 15. Falsifiable Hypotheses Over Vibes

When reasoning about cause/effect, demand predictions that can be tested:

```
Each hypothesis must be falsifiable: state the prediction it makes.

Format: "If <X> is the cause, then <changing Y> will make the bug
disappear / <changing Z> will make it worse."

If you cannot state the prediction, the hypothesis is a vibe —
discard or sharpen it.
```

This forces rigorous thinking and prevents the agent from latching onto the first plausible explanation.

## 16. Prototypes Answer Questions, Not Build Features

A prototype has one job — answer a specific question. Frame it that way:

```
A prototype is throwaway code that answers a question.
The question decides the shape.
```

This prevents scope creep in exploratory work and makes it clear when the prototype is "done" (the question has an answer).

## 17. Domain Language as Navigation Aid

Skills should use the project's domain glossary to orient themselves in the codebase:

```
When exploring the codebase, use the project's domain glossary
to get a clear mental model of the relevant modules, and check
ADRs in the area you're touching.
```

This appears in nearly every skill — it's a universal preamble that grounds the agent in the project's conceptual map before it acts.

## 18. Deletion Test for Necessity

Before adding anything (a module, a test, an abstraction), apply the deletion test:

```
Imagine deleting the module. If complexity vanishes, it was a
pass-through. If complexity reappears across N callers, it was
earning its keep.
```

This heuristic works for code, tests, documentation, and even skill phases. If removing it changes nothing, it shouldn't exist.

## 19. The Interface Is the Test Surface

Tests and callers cross the same boundary. If you need to test past the interface, the module is the wrong shape:

```
Callers and tests cross the same seam. If you want to test
past the interface, the module is probably the wrong shape.
```

This principle cascades: it shapes how you design modules, how you write tests, and how you evaluate architecture.

## 20. Structured Escape Hatches

When a phase genuinely cannot proceed, provide a structured way to stop rather than letting the agent improvise:

```
When you genuinely cannot build a loop:
Stop and say so explicitly. List what you tried.
Ask the user for: (a) access to the environment,
(b) a captured artifact, or (c) permission to add
temporary production instrumentation.
Do not proceed to hypothesise without a loop.
```

Escape hatches prevent the agent from silently degrading quality when conditions aren't met. They turn "stuck" into "explicit handoff."
