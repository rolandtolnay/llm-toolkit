---
description: After a fix or improvement, explore the codebase for other places where the same learning might apply
---

<objective>
Probe the codebase for other locations where a discovery from this session — a bug pattern, a wrong assumption, a better approach learned from a reference — might be relevant.
</objective>

<process>
1. Articulate what was learned. Name the abstract pattern behind the fix: what assumption was wrong, what convention was misunderstood, what was duplicated with a subtle variation, or what reference implementation revealed a better approach.

2. Search broadly for code that shares the same pattern or lineage. Look beyond the obvious — check code that:
   - Was likely written at the same time or copy-pasted from the same source
   - Makes the same assumption the bug relied on
   - Interacts with the same API, convention, or data path
   - Diverges from a reference implementation that informed the fix
   Use parallel Explore agents when the search space spans multiple areas.

3. For each candidate, assess honestly whether the learning applies. The same pattern does not always mean the same bug. Explain your reasoning either way.

4. Report findings:
   - Issues found: describe what, why it's the same problem, and propose a fix
   - Nothing found: say so, summarize what you checked, explain why the pattern doesn't transfer
   - Both outcomes are equally valid — do not force findings where there are none
</process>

<success_criteria>
1. The abstract pattern is explicitly stated before searching — not just "the bug we fixed" but the transferable principle
2. Search covers non-obvious locations, not just the same file or directory
3. Each candidate is individually assessed with reasoning
4. Findings are not forced — "checked X, Y, Z and the pattern doesn't apply because..." is a good outcome
</success_criteria>
