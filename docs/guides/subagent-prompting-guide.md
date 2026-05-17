# Subagent Prompting Guide

Subagents differ from skills: they run in isolation, receive delegated work from an orchestrator, and return results. Their output is consumed by the orchestrator, not a human. This constraint shapes everything below.

The deletion test: imagine removing a line from your subagent prompt. If behavior doesn't change, the line isn't earning its place.

---

## Core — Apply to Every Subagent

### 1. Outcome-First with Phase Gates

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

### 2. Define an Input Contract

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

### 3. Unambiguous Terminal States

The orchestrator must never guess whether the agent is done or what it concluded. Prescribe what the orchestrator needs to decide next — the agent structures its output to serve that decision.

For implementation agents, this is binary:
```
Success — criteria met, evidence stated, changed files listed.
Failure — which criteria unmet, what was attempted, why blocked.
```

For research or analysis agents, this is a clear conclusion with confidence:
```
Findings — what was discovered, confidence level, open questions remaining.
Blocked — what couldn't be determined and why.
```

In both cases: no ambiguity about completion. "Partially done, probably fine" is not a terminal state — either the work is finished or it isn't, and the output says which.

---

## Extensions — Apply When Triggered

Each extension has a trigger condition. If the trigger doesn't apply, skip the section entirely. A meta prompting model should not include these in every subagent prompt.

### 4. Identify the Bottleneck

**When:** The subagent has multiple phases with asymmetric failure risk.
**Skip when:** The agent does one thing (format, classify, summarize, fetch).

Declare the high-failure phase with disproportionate emphasis. This prevents the model from distributing effort evenly — the bottleneck gets the longest section, the explicit gate, and the strongest stopping condition.

```
"Deliver a verified implementation. Implementation is the path;
verification is the discipline."
```

### 5. Escalation as Decision Rules

**When:** The orchestrator supports a back-channel and the agent may encounter ambiguity that can't be resolved within scope.
**Skip when:** The agent is fire-and-forget (transform X and return the result).

Define the decision boundary explicitly: what the subagent can decide within its scope vs. what requires escalation.

- State the triggers as concrete conditions, not vibes
- Technical difficulty is NOT an escalation trigger (attempt, fail, report)
- Keep escalation triggers minimal (2-3 max)

```
You decide: implementation approach, file organization, naming.
Escalate when:
- Ambiguity with multiple valid implementations that differ in behavior
- Implementation requires changing behavior outside your scope

Do not escalate because something is hard.
```

### 6. Verification as Ranked Options

**When:** The agent mutates state (writes files, changes config, modifies data).
**Skip when:** The agent only reads and reports (research, analysis, classification).

Provide a ranked preference list rather than a fixed requirement. This handles the reality that different projects have different verification surfaces.

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

### 7. Encode Anti-Patterns as Decision Rules

**When:** You've tested the subagent and observed specific failure modes.
**Skip when:** Writing the prompt for the first time — add anti-patterns reactively, not speculatively.

Use inversion to identify failure modes: "What would guarantee this subagent fails?" Then route around each failure with a positive decision rule — not a "don't" list.

Name only failures that are genuinely tempting for the model, explain why they fail, and encode the avoidance as a constraint. Don't negate unlikely behaviors.
