# Subagent Prompting Guide

Principles for defining subagent prompts that produce reliable, scoped behavior. Grounded in outcome-first prompting (GPT-5.5 guide), vocabulary activation, judgment compression, and the skill-prompting-principles corpus.

Subagents differ from skills: they run in isolation, receive delegated work from an orchestrator, and return results — they don't own decisions. This constraint shapes everything below.

## 1. Outcome-First with Phase Gates

Define what good looks like at each phase boundary. Trust the model to navigate within.

A subagent prompt should answer three questions:
- What does "done" look like? (outcome)
- What must be true before claiming done? (phase gates)
- What should never happen? (constraints)

Do not prescribe the path between gates unless sequence is the point. GPT-5.5 finds efficient solutions when given destination and constraints — process steps narrow its search space.

```
PROCESS-HEAVY (avoid):
1. Read the file  2. Find the bug  3. Write a fix  4. Run tests

OUTCOME-FIRST (prefer):
Fix the failing test. The fix is correct when:
- The test passes with the original assertion unchanged
- No other tests broke
- The change is minimal
```

## 2. Define an Input Contract

Every subagent expects inputs. Make the contract explicit:
- What's required vs. optional
- What each input means for scope
- How scope-limiting inputs constrain the agent

The contract goes in the subagent prompt. How to satisfy it goes in caller-side guidance (the orchestrator's skill or tool description).

```
You receive:
- Goal — what to deliver (required, this is your scope)
- Acceptance criteria — how to know it's done (derive if absent)
- Context — surrounding intent, does not expand scope
```

Frame scope-limiting inputs as constraints, not suggestions: "Context provides intent. Your scope is the goal, not the context."

## 3. Name the Discipline

Frame the subagent as a discipline, not an assistant. The model rises to the frame.

```
WEAK:  "You are a helpful code review assistant."
STRONG: "You are `reviewer`: a structural analysis discipline."
```

One line. The discipline frame activates rigor without personality instructions. No warmth, no collaboration style — subagent output is consumed by the orchestrator, not a human.

## 4. Identify the Bottleneck

Each subagent has one phase where failure is most likely and most costly. Declare it with disproportionate emphasis.

```
"Deliver a verified implementation. Implementation is the path;
verification is the discipline."
```

This prevents the model from distributing effort evenly. The bottleneck gets the longest section, the explicit gate, and the strongest stopping condition.

## 5. Binary Terminal States

A subagent reports exactly one of: success or failure. The orchestrator must be able to tell at a glance which it is and what evidence supports it.

Do not prescribe a fixed output template — the model formats well when told what information to include. Prescribe the decision the orchestrator needs to make from the output.

```
Success — criteria met, evidence stated, changed files listed.
Failure — which criteria unmet, what was attempted, why blocked.
```

No middle ground. "Partially done, probably fine" is not a terminal state.

## 6. Escalation as Decision Rules

Subagents don't own decisions — they implement within a lane. Define exactly when to break out:

- State the triggers as concrete conditions, not vibes
- Technical difficulty is NOT an escalation trigger (attempt, fail, report)
- Keep escalation triggers minimal (2-3 max)

```
Escalate when:
- Ambiguity with multiple valid implementations that differ in behavior
- Implementation requires changing behavior outside your scope

Do not escalate because something is hard.
```

## 7. Encode Anti-Patterns as Decision Rules

Name the failure modes that are genuinely tempting for the model, explain why they fail, and encode the avoidance as a positive decision rule — not a "don't" list.

Use inversion to identify them: "What would guarantee this subagent fails?" Then route around each failure with a constraint.

Common subagent failure modes:
- **Scope creep** — reading context and expanding the task. Route: "Context is intent, not scope."
- **Premature success** — reporting done without evidence. Route: the verification phase gate.
- **Silent decision-making** — resolving ambiguity without surfacing it. Route: the escalation triggers.

Only include anti-patterns you've observed or that are genuinely tempting. Don't negate unlikely behaviors.

## 8. Vocabulary Activation Over Process Description

Use canonical software engineering terms as native language. One term activates a web of associated knowledge from the model's training data.

```
VERBOSE: "Before implementing, explore the codebase to understand where
your changes should go and what other code might be affected."

ACTIVATED: "Identify the change points and their effect sketch before editing."
```

Keep activation terms lean (2-4 per subagent). The subagent's job is narrow — it doesn't need the full vocabulary of an architectural skill.

## 9. Verification as Ranked Options

When verification is part of the job, provide a ranked preference list rather than a fixed requirement. This handles the reality that different projects have different verification surfaces.

```
Verify using the strongest available signal:
1. Targeted tests
2. Type check or lint
3. Build
4. Smoke command
5. Code-path inspection with reasoning

State what you verified. If stronger was available but skipped, justify.
```

The ranking encodes experience. The agent picks the strongest available option without being blocked when the strongest isn't available.

## 10. Caller-Side Guidance

The subagent prompt defines what it expects. A separate caller-side section (in the orchestrator's skill or tool description) defines how to satisfy that contract.

Keep caller guidance outcome-first: tell the orchestrator what the subagent needs to locate, not how to format the handoff.

```
PROCESS: "Inline the issue's What to Build section as the goal parameter
and pass the PRD file content as context."

OUTCOME: "Tell the worker where to find its goal, criteria, and context.
File paths are sufficient — the worker reads what it needs."
```

## 11. Start Minimal, Add Reactively

GPT-5.5's defaults are stronger than prior models. Over-specification adds noise and narrows the search space.

Start with: role + goal + success criteria + constraints + output contract. Test. Add instructions only when you observe a specific failure mode. If the prompt exceeds ~50 lines, audit for instructions that duplicate model defaults.

The deletion test applies: imagine removing a line. If behavior doesn't change, the line isn't earning its place.

## Design Process

When building a new subagent:

1. **Define the job** — one sentence, outcome-framed
2. **Identify the bottleneck** — where does failure hurt most?
3. **Invert** — what guarantees failure? Route around each with a decision rule
4. **Define the input contract** — what does it need, what constrains scope?
5. **Define terminal states** — what does success/failure look like to the orchestrator?
6. **Pick activation vocabulary** — 2-4 canonical terms that ground the implementation posture
7. **Draft** — role + goal + contract + implementation + verification + escalation + output
8. **Test and trim** — remove anything that doesn't change behavior
