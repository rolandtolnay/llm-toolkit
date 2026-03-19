# PR Comment Triage Framework

A systematic framework for deciding which PR review comments to act on, ignore, defer, or investigate.

## Core Equation

**Comment value = P(bug) x Impact - Cost(fix)**

- **P(bug):** Probability the described scenario actually occurs in production
- **Impact:** What breaks and who's affected if it does occur
- **Cost:** Code change + complexity added + risk of introducing new bugs

## The Triage Questions

For each comment, ask in order. Stop as soon as you reach a decision.

### Scope: Is this my problem right now?

Does the comment target a file/system within this PR's scope and ownership?

**IGNORE if:**
- File is outside the PR's diff and not flagged by the PR author for inclusion
- File is owned by another team (e.g., proto files synced from backend, shared configs managed elsewhere)
- Comment is pure documentation/style with no functional impact
- Comment targets a skill, CI config, or tool unrelated to the PR's feature

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
