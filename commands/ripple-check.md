---
description: After a fix or improvement, explore the codebase for other places where the same learning might apply
---

<objective>
Probe the codebase for other locations where a discovery from this session — a bug pattern, a wrong assumption, a better approach learned from a reference — might be relevant.
</objective>

<process>
1. Articulate what was learned. Name the abstract pattern behind the fix: what assumption was wrong, what convention was misunderstood, what was duplicated with a subtle variation, or what reference implementation revealed a better approach.

2. Search for code with shared lineage — same author, same assumption, same seam. Use parallel Explore agents when the search space spans multiple areas.

3. For each candidate, assess honestly whether the learning applies. The same pattern does not always mean the same bug. Explain your reasoning either way.

4. Report findings:
   - Issues found: describe what, why it's the same problem, and propose a fix
   - Nothing found: say so, summarize what you checked, explain why the pattern doesn't transfer
   - Both outcomes are equally valid — do not force findings where there are none
</process>

<success_criteria>
1. Report a candidate only when you can name the specific mechanism it shares with the original issue
2. "Checked X, Y, Z — pattern doesn't transfer because..." is a valid outcome; never pad findings
</success_criteria>
