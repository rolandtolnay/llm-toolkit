# Judgment Compression

## The Problem

Experienced engineers make judgment calls constantly — when to write a test, when to refactor, when to add an abstraction, when to stop iterating. These calls feel intuitive but rest on internalized criteria built over years.

"Use good judgment" is an empty instruction. The LLM doesn't know which heuristics you're applying. Judgment compression converts implicit expertise into explicit, falsifiable rules the LLM can apply consistently.

## Techniques

### Multi-Criteria Gates

Convert "it depends" into a conjunction of concrete conditions. All must hold for the action to trigger.

**Before:** "Write an ADR when the decision is important."
**After:** "Write an ADR only when all three hold: hard to reverse, surprising without context, genuine trade-off with a runner-up."

Each criterion is independently testable. The gate prevents both over-triggering and under-triggering.

### Named Anti-Patterns

Name the failure mode. A named anti-pattern activates the LLM's training-data knowledge of that failure — causes, symptoms, remedies — in fewer tokens than any description.

**Before:** "Don't write tests that are too broad."
**After:** "Avoid ice cream cone testing — heavy end-to-end coverage on top, minimal unit tests underneath."

### Falsifiable Hypotheses

For diagnostic or investigative skills, require hypotheses in a form that can be proven wrong.

**Before:** "Think about what might be causing the bug."
**After:** "State a hypothesis: 'If [cause], then [observable consequence].' Design a test that would disprove it."

The LLM can't drift into vague speculation when forced to state falsifiable predictions.

### Decision Trees with Concrete Branches

Replace "choose the best approach" with explicit branching conditions.

**Before:** "Decide whether to mock or use a real implementation."
**After:** "Mock at system boundaries — network, filesystem, clock, external APIs. Use real implementations for everything inside the boundary."

The branch condition ("system boundary") is concrete and checkable.

### Vocabulary Policing

List both what to say AND what not to say. Accepted terms with their rejected alternatives.

**Before:** "Use consistent terminology."
**After:**
- Say "module," not "component" or "service"
- Say "seam," not "boundary" or "injection point"
- Say "interface," not "API" (reserve API for HTTP endpoints)

Stronger than a glossary because it explicitly closes off drift paths.

## Compression Quality Test

For each compressed rule, ask:
1. **Self-contained?** Can the LLM evaluate this without additional context?
2. **Grounded?** Does this prevent a failure mode actually observed?
3. **Non-trivial?** Could a reasonable person disagree with this rule?

If any answer is no, the rule needs refinement or doesn't earn its place.
