# GPT-5.5 Tuning for Engineering Skills

GPT-5.5 works best when prompts define the outcome and leave room for the model to choose the path. Engineering skills must account for this — over-specification produces worse results than under-specification.

## Outcome-First Framing

Define what good looks like before prescribing how to get there.

**Process-heavy (avoid unless order is the point):**
```
1. Read the test file
2. Identify the failing assertion
3. Trace the call chain
4. Find the root cause
5. Write a fix
6. Verify the test passes
```

**Outcome-first (prefer):**
```
Fix the failing test. The fix is correct when:
- The test passes with the original assertion unchanged
- No other tests broke
- The change is minimal — one root cause addressed, not a refactor
```

Process steps earn their place when the *sequence* matters (TDD's red-green-refactor is deliberate, not a suggestion). Omit them when the model can find its own path.

## Decision Rules Over Absolutes

ALWAYS/NEVER are for true invariants — safety rules, required fields, things that must hold regardless of context. For judgment calls, decision rules outperform blanket rules.

**Absolute (brittle):** "NEVER mock the database."
**Decision rule (robust):** "Mock at system boundaries — network, filesystem, clock. Use real implementations inside the boundary. The database is inside the boundary unless tests must run without infrastructure."

The "unless" clause handles the edge case that an absolute would forbid.

## No Redundant Reasoning Instructions

GPT-5.5 reasons internally by default. These add latency with negligible or negative impact:
- "Think step by step"
- "Consider all options"
- "Be thorough"
- "Think carefully about the trade-offs"

Replace with criteria: "Choose the approach with the fewest cross-module dependencies." A criterion shapes the outcome; a reasoning instruction shapes the process (which the model already handles).

## Explicit Stopping Conditions

Without stopping conditions, the model tends to over-polish or keep searching. Engineering skills need clear exit criteria:

```
After each test passes, ask: "Does the current implementation satisfy the acceptance criteria?"
If yes, stop. Do not refactor further unless the code has a structural problem that would block the next slice.
```

## Retrieval Budgets for Codebase Exploration

Engineering skills often need exploration. Set limits to prevent rabbit-holing:

```
Explore for modules related to [feature]. Read at most 5 files.
If the relevant module isn't found, ask the user rather than continuing to search.
```

## Start Minimal

Begin with the fewest possible instructions. Add only when you observe a specific failure mode. Over-specification is a bigger risk with GPT-5.5 than under-specification — the model's defaults are stronger than previous generations.

The implication for engineering skills: if the canonical vocabulary activates the right knowledge, you may not need process steps at all. Test the skill with just principles and vocabulary before adding procedural instructions.
