# PR Comment Triage Framework

A systematic framework for deciding which PR review comments to act on, ignore, defer, or investigate.

## Core Equation

**Comment value = P(bug) x Impact - Cost(fix)**

- **P(bug):** Probability the described scenario actually occurs in production
- **Impact:** What breaks and who's affected if it does occur
- **Cost:** Code change + complexity added + risk of introducing new bugs

This equation applies to **correctness comments** — "this will break when X." But code review also covers **code health comments** — architecture, pattern enforcement, test coverage — where P(bug) is the wrong lens entirely. For these, the question is: "Does this make the codebase harder to maintain or diverge from the team's intended direction?" See the decision matrix for how to handle each type.

## The Triage Questions

For each comment, ask in order. Stop as soon as you reach a decision.

### Scope: Is this my problem right now?

Does the comment target a file/system within this PR's scope and ownership?

**IGNORE if:**
- File is outside the PR's diff and not flagged by the PR author for inclusion
- File is owned by another team (e.g., proto files synced from backend, shared configs managed elsewhere)
- Comment targets a skill, CI config, or tool unrelated to the PR's feature

**Ticket-scope check:** A fix can be technically sound *and* out of scope. Check the originating ticket's acceptance criteria (and parent epic's architectural decisions) to decide between **ACT** (aligns with a stated goal or AC), **DEFER** (valid but needs its own ticket), and **IGNORE** (ticket explicitly contradicts the suggestion).

**ADR check:** If the project has ADRs (`docs/adr/`), check whether the suggestion contradicts a recorded decision. If it does, reference the ADR in your rationale — the decision was already made and should not be re-litigated during triage. If the friction is real enough to warrant reopening the ADR, note that explicitly.

**Do NOT ignore** comments about architecture, patterns, or test coverage just because they aren't bugs. These are legitimate code review concerns — proceed to fix assessment.

### Likelihood: Can I determine P(bug) from static analysis?

Read how the component is *actually instantiated* by its parent. Check:

- **Is the prop/state ever updated, or is the component destroyed/recreated?** If destroyed/recreated between uses, reactivity/stale-state concerns are moot.
- **Is the data set realistically large enough to trigger the issue?** A pagination concern for a list that never exceeds 10 items is theoretical.
- **Is the code path actually reachable?** Trace from the entry point — can the described scenario occur given the actual call sites?
- **Does the framework/runtime actually behave as the comment claims?** Bot reviewers often apply generic patterns without checking version-specific behavior or runtime characteristics (e.g., protobuf getters are not Vue-reactive regardless of how you reference them).

**If P(bug) = 0 from static analysis → IGNORE** with a brief rationale.
**If P(bug) is clearly > 0 → proceed to fix assessment.**
**If genuinely uncertain → mark as INVESTIGATE.**

### Fix assessment: Is the fix worth it, and does the proposed fix work?

Evaluate both the cost and quality of the fix:

- **One-line, zero-risk fix** (e.g., adding `.prevent` to a click handler, removing a filter) → **just fix it**
- **Multi-file change or behavioral change** (e.g., adding pagination loops, changing data refresh strategy) → investigate first, then fix

The threshold: if the fix takes < 5 minutes and introduces zero new risk, the cost of investigating whether it's needed exceeds the cost of just doing it.

Even when P(bug) > 0, evaluate the proposed fix:

- **Adds complexity disproportionate to the risk?** Full pagination for a list that might someday reach 26 items may not justify the added code.
- **Creates new problems?** Calling a full data reload after a mutation can cause UI flicker, race conditions, or unnecessary network traffic.
- **Obscures intent?** Wrapping a value in `computed()` when it's intentionally evaluated once signals to future readers that it needs to be reactive — a false signal.
- **Adds defensive code against impossible scenarios?** This teaches future readers the scenario is possible, increasing cognitive load.
- **Is the reviewer's proposed fix the best approach?** If not, propose a better alternative in the analysis. Debating the fix is valuable.

**If the fix makes the code worse → IGNORE or propose a simpler alternative.**
**If the issue is valid but belongs in a different effort → DEFER** (log as a ticket for future work).

### Code health: Architecture, patterns, and test coverage

These comments don't fit the P(bug) model — evaluate them on their own terms:

**Architecture / pattern comments** (e.g., "use the service layer instead of direct DB queries"):
- Check whether the reviewer is describing a team direction or just a preference. Signals: "we're moving away from X," "the pattern is Y," or the codebase already has a service/abstraction that does the same thing.
- If a team direction exists, new code should follow it — even if old code hasn't migrated. "Other code does it the old way" is not a justification. The old code is tech debt; new code shouldn't add more.
- If the fix is small and aligns with team direction → **ACT**. If the reviewer also points out existing old-pattern code, consider fixing that too — eliminating the last instance of an old pattern prevents future copy-paste.
- If the architectural change is large and orthogonal to the PR's purpose → **DEFER** with a ticket.

**Test coverage comments** (e.g., "need tests"):
- Tests ship with the code they cover. This is **always ACT, never DEFER**. Untested code is not shippable.
- Look at existing test patterns in the project to determine the right scope and style for new tests.

## Decision Matrix

| Signal | Action |
|--------|--------|
| File outside PR scope / other team's ownership | Ignore |
| One-liner, zero risk, obviously correct | Just fix it |
| "This will break when X" and you can prove X can't happen | Ignore with rationale |
| "This will break when X" and you can't determine if X happens | Investigate |
| Data shown to users might be wrong (financial amounts, counts, status) | Investigate — high impact |
| Fix adds complexity but P(bug) is speculative | Ignore or simplify |
| Fix changes behavior in ways that might cause new bugs | Investigate before acting |
| Comment is a duplicate of another comment | Merge with the original, decide once |
| Valid issue but requires cross-cutting effort beyond this PR | Defer — log as ticket |
| Valid issue but fixing only here creates inconsistency with other pages | Defer — log as ticket for consistent fix |
| UX/accessibility improvement that is real but not a regression | Defer — log as ticket |
| Reviewer identifies a pattern direction and new code violates it | Act — follow team direction, not legacy code |
| Reviewer identifies a pattern direction and old code also violates it | Act on new code; consider fixing old code too if the change is small |
| Test coverage request for code changed in this PR | Act — tests ship with the code they cover, never defer |
| Suggestion contradicts a recorded ADR | Ignore — reference the ADR. Reopen only if friction warrants it |

## When to Investigate

**Worth investigating (can't resolve from code alone):**
- Data correctness issues where the scenario depends on real data volumes or backend behavior
- User interaction bugs that can be tested in a browser
- State management after mutations where behavior depends on what the backend returns
- Comments where P(bug) depends on framework version or runtime behavior you're uncertain about

**Not worth investigating (resolve from code):**
- Reactivity/lifecycle concerns where you can trace the component's actual usage by its parent
- Comments about files outside the PR scope
- Style/naming/documentation nitpicks
- Comments where the fix is trivial enough to just do it
