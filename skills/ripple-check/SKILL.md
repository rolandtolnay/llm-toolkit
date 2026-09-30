---
name: ripple-check
description: After a fix or improvement, explore the codebase for other places where the same learning might apply. Use when checking whether a bug pattern, wrong assumption, or better approach should ripple to similar code.
disable-model-invocation: true
---

A fix teaches you something the codebase did not know it had wrong: an assumption that does not hold, a convention that was misread, a better approach a reference revealed. Code written under the same assumption elsewhere carries the same latent problem. This session has already paid to learn the symptom and its cause, so checking the rest of the codebase now is cheap, and finding the same bug later in production is not. The flow that was just fixed is boy-scout's territory; this pass covers everywhere else.

Invoking this skill asks for the check, not for findings. "Checked X, Y, Z; the pattern does not transfer because..." is a complete answer, and forcing findings where there are none is the failure. The report goes to the user, who decides what to act on, so write it so they can judge each candidate without opening the code.

## Name the learning

Before searching, state the abstract pattern behind the fix: what assumption was wrong, what convention was misunderstood, what was duplicated with a subtle variation, or what the reference implementation did better. The search is for this pattern, not for the literal code that was changed.

## Find and judge candidates

Look for code with shared lineage: same author, same assumption, same seam. Use subagents when the search space spans several areas.

A candidate earns a place in the report only when you can name the specific mechanism it shares with the original issue. The same shape of code does not always carry the same bug; when it does not, say why, briefly.

## Report

For each candidate that passes: where it lives, why it is the same problem, and the proposed fix. When nothing passes: say so, summarize what you checked, and explain why the pattern does not transfer.

Make no changes until the user picks, unless the invocation asked you to apply them; then implement the picked items.
