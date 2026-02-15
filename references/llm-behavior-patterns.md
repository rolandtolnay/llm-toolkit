# LLM Behavior Patterns

Why the heal-claude-md patterns work. Reference this when a user asks for rationale.

---

## Failure Modes and Solutions

**1. Eager Generation**
LLMs want to produce output immediately, skipping research and validation steps.
→ **Solution**: Temporal markers (FIRST/THEN/FINALLY), explicit WAIT/STOP points

**2. Training Data Contamination**
LLMs prefer patterns from training data over project-specific instructions.
→ **Solution**: Repetition of critical constraints, concrete BAD/GOOD examples

**3. Ambiguity Exploitation**
LLMs interpret vague rules loosely, choosing the path of least resistance.
→ **Solution**: If-then conditional triggers, explicit thresholds, priority labels

**4. Flat Priority Processing**
Without visual hierarchy, all instructions have equal weight.
→ **Solution**: Tiered constraints (NEVER/YOU MUST/Avoid), CRITICAL labels

**5. No Self-Verification**
LLMs generate forward without looking back to check their work.
→ **Solution**: Self-check section with explicit verification checklist

**6. Wrong Assumptions**
LLMs make assumptions about requirements and run with them without checking.
→ **Solution**: Explicit "surface assumptions" step before implementation

**7. Side-Effect Changes**
LLMs modify unrelated code (comments, refactoring) as "improvements" while doing a task.
→ **Solution**: NEVER rule against modifying code unrelated to the task

**8. Over-Engineering**
LLMs bloat abstractions and overcomplicate solutions when simpler ones exist.
→ **Solution**: Explicit "minimal solution first" constraint in Avoid tier

---

## Word-Level Patterns

Stronger language improves adherence. Transform weak phrasing:

| Weak (Permissive) | Strong (Enforced) | Why It Works |
|-------------------|-------------------|----|
| Avoid | NEVER | Absolute prohibition vs soft suggestion |
| Don't | DO NOT | Explicit negation |
| Should | MUST / YOU MUST | Obligation vs recommendation |
| Ask for clarification on... | STOP and ask when... | Creates explicit gate |
| Proceed autonomously for... | ONLY proceed without asking when... | Inverts default to caution |
| Consider | ALWAYS | Removes optionality |
| Try to | — (remove) | Eliminates wiggle room |

---

## Pattern Rationale

Why each required pattern earns its place:

| Pattern | Rationale |
|---------|-----------|
| TL;DR Section | LLMs process the beginning of context most reliably. Front-load critical constraints. |
| Tiered Constraints | Creates visual and semantic priority hierarchy. NEVER violations stand out from soft "Avoid" suggestions. |
| Data Flow Diagram | Visual diagram is memorable. Warning creates a mental checkpoint. |
| If-Then Triggers | Explicit triggers eliminate judgment calls. Claude can pattern-match rather than interpret. |
| When to Read Table | Action-verb triggers ("Building", "Creating") match task mental models. |
| Self-Check Section | Forces reflection. LLMs don't naturally self-verify — explicit prompts create checkpoints. |
| Temporal Markers | Prevents eager generation. Creates explicit phases that can't be skipped. |
