# Canonical Sources for Engineering Skills

An index of software engineering books and the concepts they contribute. Use this to identify grounding for new skills — find the concepts that address the engineering problem, then extract vocabulary.

Not exhaustive. Covers sources most frequently useful for engineering skills targeting LLM-assisted development.

---

## A Philosophy of Software Design — John Ousterhout

**Core thesis:** Complexity is the root cause of most software problems. Managing complexity is the most important technical skill.

**Key concepts:**
- **Deep modules** — simple interfaces hiding significant implementation complexity. Opposite of shallow modules (complex interfaces, little functionality).
- **Information hiding** — each module encapsulates a design decision. Changes don't propagate.
- **Tactical vs. strategic programming** — tactical gets features working quickly; strategic invests in design. AI excels at tactical work; humans provide strategic direction.
- **Design it twice** — generate at least two substantially different approaches before committing.
- **Complexity signals** — change amplification, cognitive load, unknown unknowns.

**Best for:** Architecture improvement, interface design, module decomposition, code review.

---

## Working Effectively with Legacy Code — Michael Feathers

**Core thesis:** Legacy code is code without tests. Working with it requires finding safe places to make changes.

**Key concepts:**
- **Seam** — a place where you can alter behavior without editing the code at that point.
- **Characterization tests** — tests that document existing behavior before changes.
- **The legacy code dilemma** — to change safely you need tests; to add tests you need to change code.
- **Sensing and separation** — sensing: verifying what code does; separation: breaking dependencies for isolated testing.

**Best for:** Refactoring, testing legacy systems, dependency breaking, migration planning.

---

## Domain-Driven Design — Eric Evans

**Core thesis:** Software should model the business domain. The model drives both code structure and communication.

**Key concepts:**
- **Ubiquitous language** — shared vocabulary used consistently in code, conversation, and documentation.
- **Bounded context** — explicit boundary within which a domain model applies.
- **Aggregates** — clusters of domain objects treated as a unit for data changes.
- **Context mapping** — identifying relationships between bounded contexts.

**Best for:** Domain modeling, shared vocabulary, system decomposition, team alignment.

---

## The Pragmatic Programmer — Hunt & Thomas

**Core thesis:** Good programmers are pragmatic — practical choices based on context, not dogma.

**Key concepts:**
- **Tracer bullets** — end-to-end implementations of a narrow slice. Prove the architecture works before building breadth.
- **Software entropy** — systems tend toward disorder. Every change ignoring overall design accelerates decay.
- **Outrunning your headlights** — moving faster than feedback loops allow. The rate of feedback is your speed limit.
- **DRY** — not about code duplication but knowledge duplication. Single authoritative representation.
- **Orthogonality** — components that don't affect each other when changed.

**Best for:** TDD, incremental delivery, feedback loops, debugging, code organization.

---

## The Mythical Man-Month — Frederick P. Brooks

**Core thesis:** Conceptual integrity is the most important consideration in system design.

**Key concepts:**
- **Conceptual integrity** — the product appears designed by a single mind.
- **The design concept** — the shared mental model between designers. Not a document — a shared understanding.
- **No silver bullet** — no single technique produces an order-of-magnitude improvement.
- **The second-system effect** — tendency to over-engineer the second system.

**Best for:** Planning, requirements gathering, design alignment, system-level thinking.

---

## Refactoring — Martin Fowler

**Core thesis:** Restructuring existing code without changing external behavior. Small, safe, verified steps.

**Key concepts:**
- **Refactoring** — disciplined restructuring. Each step small enough that the system stays working.
- **Code smells** — surface indicators of deeper structural problems (long method, feature envy, data clumps, primitive obsession).
- **Catalog of refactorings** — named, repeatable transformations (extract method, inline function, move field).

**Best for:** Code improvement, architecture refactoring, cleanup workflows.

---

## Test-Driven Development — Kent Beck

**Core thesis:** Write a failing test, make it pass, refactor. The cycle drives design, not just verification.

**Key concepts:**
- **Red-green-refactor** — failing test (red), minimal pass (green), improve design (refactor).
- **Invest in design every day** — design is continuous, not a phase.
- **Fake it till you make it** — simplest possible implementation first, then generalize.
- **Triangulation** — tests that force generalization of overly specific implementations.

**Best for:** Testing strategy, TDD workflow, design-through-testing, feedback loops.

---

## Clean Architecture — Robert C. Martin

**Core thesis:** Architecture separates policy from mechanism. Dependencies point inward toward the domain.

**Key concepts:**
- **Dependency inversion** — high-level modules don't depend on low-level modules; both depend on abstractions.
- **The dependency rule** — source code dependencies point inward only. Inner layers know nothing about outer layers.
- **Ports and adapters** — the domain defines ports (interfaces); infrastructure provides adapters (implementations).
- **Screaming architecture** — the top-level structure should scream the domain, not the framework.

**Best for:** System architecture, dependency management, framework independence, testability.

---

## Accelerate — Forsgren, Humble, Kim

**Core thesis:** Software delivery performance predicts organizational performance. Four key metrics measure it.

**Key concepts:**
- **DORA metrics** — deployment frequency, lead time for changes, change failure rate, time to restore service.
- **Continuous delivery** — every commit is deployable. Small batches, fast feedback.
- **Trunk-based development** — short-lived branches, frequent integration to trunk.

**Best for:** CI/CD workflows, deployment skills, process improvement.
