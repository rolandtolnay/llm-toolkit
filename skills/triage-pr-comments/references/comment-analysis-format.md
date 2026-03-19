# Comment Analysis Format

Output template for per-comment triage analysis.

## Per-Comment Template

```
### Comment N — [Short title describing the issue]
**Source:** @username (or bot name) | **File:** `filename.ext:line` | **Scope:** [Yes/No + brief reason]

> [Full text of the original comment, quoted]

**What this means:** [2-3 sentence plain-English explanation of the issue. Describe
the user-visible consequence if this bug were real, how likely it is to occur in
practice, and the single key fact that determines the verdict. Write for a senior
engineer who has strong judgment but may not know the specific framework, language,
or implementation details of this codebase.]

**Likelihood:** [Core analysis of whether this can actually happen. Trace actual
component usage, lifecycle, data flow. Reference specific lines. This section can
be multi-paragraph when the reasoning chain is non-trivial — do not compress
analytical depth for formatting reasons.]

**Impact:** [HIGH/MEDIUM/LOW — what breaks and who's affected. Usually 1-2 lines,
but can elaborate when the impact chain is non-obvious.]

**Fix assessment:** [Combines fix cost and fix quality into one section. When both
are straightforward: "One-line fix, strictly better." When the proposed fix has
problems or a better alternative exists, discuss at length — debating the fix and
proposing a superior approach is valuable analysis that should not be constrained.]

**Decision: [ACT / IGNORE / DEFER / JUST FIX IT / INVESTIGATE]** | **Confidence: [HIGH / MEDIUM / LOW]**

**Change:** [If ACT/JUST FIX IT: description of what to change. If IGNORE: brief
rationale. If DEFER: one-line ticket description for Linear.]
```

### Section guidelines

- **Scope** is on the source line because it is almost always short and binary ("Yes, in the PR diff"). If scope requires extended discussion (e.g., file ownership debate), expand into Likelihood.
- **Likelihood** and **Fix assessment** are the two sections most likely to be multi-paragraph. Never compress them to fit a format — the format serves the analysis, not the other way around.
- **What this means** should always be present. It is the reader's primary tool for deciding whether to trust the analysis, probe deeper, or challenge the reasoning.

## Summary Tables

After individual analysis, present three summary tables.

### Changes to make

```
| # | Priority | File | Change | Confidence |
|---|----------|------|--------|------------|
| 1 | P1 | `File.vue:line` | Description of change | HIGH |
```

### Comments to defer

```
| # | File | Ticket description |
|---|------|--------------------|
| 5 | `SubscriptionsPage.vue` | Add keyboard navigation to list page table rows |
```

### Comments to ignore

```
| # | File | Reason |
|---|------|--------|
| 7 | `proto.file:line` | Proto synced from backend, not our ownership |
```

## Decision Taxonomy

- **ACT** — fix in this PR, approach is clear
- **JUST FIX IT** — trivial fix, cheaper to do than to discuss
- **DEFER** — valid issue, wrong venue. Will be logged as a Linear ticket for future work. Use when the issue is real but: out of PR scope, requires a cross-cutting effort, or is a UX/accessibility improvement that shouldn't be addressed in isolation.
- **IGNORE** — not a real issue (P(bug) = 0, wrong analysis, permanently out of scope)
- **INVESTIGATE** — P(bug) is uncertain, need more information before deciding

## Confidence Ratings

- **HIGH:** Outcome determined from static analysis alone. No user input needed.
- **MEDIUM:** Analysis is sound but relies on assumptions the user should confirm (e.g., file ownership, data volumes, acceptable UX tradeoffs).
- **LOW:** Cannot determine P(bug) or correct approach without investigation or domain knowledge.

## Saved Analysis Document

When saving the full analysis to a file, include:

1. **Header:** PR number, title, branch, date, comment sources
2. **Framework reference:** Brief note that the triage framework was applied
3. **All per-comment analyses** in the template format above
4. **Summary tables** for ACT, DEFER, and IGNORE
5. **Key insights** — project-specific learnings that emerged during triage (e.g., "proto files are synced from X", "component Y is always destroyed/recreated", "pagination is inconsistent across pages"). These help future triage sessions and skill creation.
