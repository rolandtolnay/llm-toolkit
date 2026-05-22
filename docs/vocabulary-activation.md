# Vocabulary Activation Reference

Canonical terms that produce structured, precise LLM output. Use the exact term — synonyms activate weaker associations.

---

## Analysis & Evaluation

### Impact analysis
Enumerate what a proposed change affects, assess severity, flag risks. Covers blast radius, regression risk, complexity cost, and idiom fit.

**Use when:** You have a feature idea and want to understand system-level consequences before deciding to build it.

### Blast radius
Scope of what breaks or changes when you touch something. Activates coupling analysis, dependency graphs, change propagation.

**Use when:** You want to know specifically what breaks — narrower than impact analysis, focused on damage surface.

### Trade-off analysis
Evaluate competing options against named criteria. Forces the LLM to present runner-ups and what you're giving up.

**Use when:** You've identified multiple approaches and want a structured comparison, not a recommendation.

### Spike
Time-boxed investigation to reduce uncertainty. Produces findings, not production code.

**Use when:** You don't know enough to plan yet. "Spike on whether X is feasible" prevents the LLM from jumping to implementation.

### Sanity check
Quick verification that something is reasonable — not a deep review, not a full analysis. Activates lightweight "does this pass the smell test?" mode.

**Use when:** You want a fast gut-check, not a thorough review. "Sanity check this approach" gets a paragraph, not an essay.

---

## Architecture & Design

### Seam
A place where behavior can be altered without editing surrounding code (Feathers). Activates testability, modularity, and change-point reasoning.

**Use when:** You need to find where to inject new behavior or test boundaries in existing code.

### Deep module
A module that hides significant complexity behind a simple interface (Ousterhout). Activates interface-vs-implementation reasoning.

**Use when:** Evaluating whether an abstraction is pulling its weight or just adding indirection.

### Conceptual integrity
The system speaks with one voice — consistent patterns, naming, and mental model throughout (Brooks).

**Use when:** Assessing whether a new addition fits the existing system's idioms or introduces a second way of doing things.

### Idiomatic
A solution that follows the established patterns, conventions, and style of the existing codebase (or language/framework). Prevents the LLM from introducing a "correct but foreign" approach.

**Use when:** You want the solution to look like it belongs — "give me the idiomatic way to do X" or "is this idiomatic for our codebase?"

### Essential vs. accidental complexity
Complexity inherent to the problem vs. complexity introduced by the solution (Brooks).

**Use when:** Questioning whether implementation difficulty comes from the problem itself or from poor abstraction choices.

### Leaky abstraction
When implementation details bleed through the interface (Spolsky). The caller has to understand what's behind the abstraction to use it correctly.

**Use when:** Evaluating interface quality — "is this abstraction leaking?" catches APIs that promise simplicity but demand internal knowledge.

### Surface area
How much of a module is exposed to consumers. Large surface area = more to learn, more to break, more to maintain.

**Use when:** You want the LLM to minimize what's public — "reduce the surface area" activates API trimming and encapsulation.

### Escape hatch
A deliberate way out of an abstraction when it doesn't fit the use case. The difference between a flexible design and a rigid one.

**Use when:** Evaluating whether a design is too opinionated — "where's the escape hatch?" asks if users can break out when the happy path doesn't apply.

### Invariant
A condition that must always hold, regardless of code path. "What invariant does this violate?" is dramatically sharper than "what's wrong?"

**Use when:** Reasoning about correctness — forces the LLM to name the specific rule being broken rather than describe symptoms.

---

## Debugging & Diagnosis

### Minimise the reproducer
Reduce a failing case to the smallest input that still triggers the bug.

**Use when:** You have a bug report and want the LLM to isolate rather than guess-and-fix.

### Bisect
Binary search through a range (commits, inputs, config) to find where behavior changed.

**Use when:** Something worked before and doesn't now, and you want a systematic approach rather than shotgun debugging.

---

## Planning & Scoping

### Solution horizon
Tactical (patch it now), pragmatic (fix it properly), strategic (redesign the area). Forces the LLM to present options at different investment levels.

**Use when:** You want to see the full spectrum of fix depth before choosing how much to invest.

### Pragmatic
Favor the solution that works and ships over the one that's theoretically optimal. Accept trade-offs, minimize investment, tolerate imperfection.

**Use when:** You want to prevent over-engineering — "give me the pragmatic approach" cuts off gold-plating and premature abstraction.

### First principles
Derive the answer from fundamentals rather than pattern-matching from conventions or prior examples. The opposite of "idiomatic."

**Use when:** You suspect the existing approach is wrong and want the LLM to reason from scratch rather than copy what's already there.

### Pareto (80/20)
Identify the 20% of effort that delivers 80% of the value. Activates scope-cutting and prioritization reasoning.

**Use when:** Scoping work, trimming feature lists, or asking "what's the minimum that actually matters here?"

### Tracer bullet
A thin end-to-end implementation that touches every layer, proving the architecture works before filling in details (Hunt & Thomas).

**Use when:** Starting a new feature and you want the skeleton working across all layers before fleshing anything out.

### Walking skeleton
Similar to tracer bullet but emphasizes the minimal deployable version that exercises the full stack.

**Use when:** You want to validate integration and deployment pipeline early, not just architecture.

### One-way door / two-way door
A one-way door is hard or impossible to reverse; a two-way door is cheap to undo (Bezos). Changes how the LLM weighs risk and recommends caution.

**Use when:** Making architectural or infrastructure decisions — "is this a one-way door?" forces explicit reversibility reasoning.

### Strangler fig
Incrementally replace a legacy system by building the new one around it, routing traffic piece by piece until the old one is dead (Fowler).

**Use when:** Discussing migrations or rewrites — prevents the LLM from proposing big-bang replacements.

---

## Interrogation & Challenge

### Walk every path of the decision tree
Exhaustively enumerate every branching choice in a design, resolving each one before moving on. Prevents the LLM from collapsing options into a single recommendation too early.

**Use when:** You have a plan or design and want every hidden assumption surfaced — not just the happy path.

### Stress-test
Challenge a design against edge cases, failure modes, and adversarial inputs. Activates "what breaks if..." reasoning.

**Use when:** You have a plan you're fairly confident in and want it pressure-tested, not interrogated from scratch.

### Steel-man
Present the strongest possible version of a counter-argument or alternative approach before dismissing it.

**Use when:** You've made a decision but want to verify you're not ignoring a legitimately better option out of anchoring bias.

### Devil's advocate
Argue the opposite position to find weaknesses. More adversarial than steel-man — the LLM actively tries to break your reasoning.

**Use when:** You want someone to poke holes, not just present alternatives politely.

---

## Code Quality

### Change propagation
How far a single change ripples through the system. High propagation = high coupling.

**Use when:** Evaluating whether a proposed change is isolated or will cascade across modules.

### Shotgun surgery
A single logical change requires edits scattered across many files (Fowler).

**Use when:** You notice a change touching many files and want the LLM to assess whether the code needs consolidation.

### Feature envy
A method that uses another module's data more than its own (Fowler). Signals misplaced responsibility.

**Use when:** Reviewing code placement decisions — "does this logic belong here?"

---

## Output Shaping

### Enumerate
Forces exhaustive listing rather than a selective sample. "Enumerate all X" vs "what are some X" is the difference between a complete inventory and a few examples.

**Use when:** You need every instance, option, or case — not a representative sample.

### Rubber duck
Make the LLM narrate its understanding step by step rather than jump to a solution. Forces the explanation to come before the answer.

**Use when:** You want to verify the LLM actually understands the problem before it starts solving — "rubber duck this for me" surfaces wrong assumptions early.
