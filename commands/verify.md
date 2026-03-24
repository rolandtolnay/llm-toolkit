---
name: verify
description: Second-opinion verification of completed work — analyzes autonomously, then interrogates interactively before declaring issues
argument-hint: "[commit range, plan path, or description of work]"
---

<objective>
Act as a second opinion on completed code changes. Analyze autonomously, then resolve every finding interactively with the user before declaring anything an issue — some findings are bugs, others are intentional omissions, and the conversation determines which.
</objective>

<context>
$ARGUMENTS

!`git status --short`
!`git log --oneline -15`
</context>

<process>

## Beat 1: Scope and Intent

If `$ARGUMENTS` provides commit hashes, a range, or a plan path — use directly. Otherwise ask the user once for scope.

Reconstruct intent from the diff, commit messages, and plan file (if available). State it as concrete truths that must hold if the work succeeded. Confirm with the user in one exchange: "Does this capture it?"

If a skill in the skill list clearly matches the domain of the changes, load it for expertise.

## Beat 2: Autonomous Analysis

Analyze the changes. Use Explore agents to parallelize. Judge which dimensions matter most for the specific change — not every change needs equal depth on every axis.

**Correctness:** Do the observable truths hold? Are artifacts real implementations (not stubs) and wired into the system?

**Preservation:** For changed functions, do edge cases from the removed code still have handling in the new code? Do callers still work? Were control flow changes safe?

**Completeness (blast-radius sweep):** Extract old patterns from removed diff lines — names, paths, conventions, identifiers. Grep the entire codebase for survivors. Check documentation, test fixtures, config files, and examples for stale references. This catches files that should have changed but didn't — the gap that code-level analysis alone cannot find.

Run tests if they exist. Test failures are findings — no need for deeper analysis on code that tests already reject.

Produce a findings list. Each finding: location, confidence (certain / likely / possible), description with code snippets, and the concrete failure scenario.

## Beat 3: Interrogation

Present findings grouped by confidence. Then resolve each with the user — never assume a finding is a bug.

For each finding, present context and your recommended assessment, then ask: fix, intentional, or investigate further.

After resolving explicit findings, probe for gaps the analysis may have missed. Walk decision branches on significant change points:
- Unhandled edge cases (empty, null, already exists, fails)
- New preconditions or assumptions introduced by the change
- Other consumers of changed interfaces

Continue until all branches are resolved. Each question should save more context than it costs — stop when remaining branches are low-risk.

After interrogation, list confirmed issues as action items with fix checkboxes. State status: CLEAN / ISSUES FOUND / NEEDS MANUAL TEST.

</process>

<success_criteria>
- Intent validated with user before analysis begins
- Blast-radius sweep explicitly performed — old patterns grepped across entire codebase
- Every finding confirmed with user before being declared an issue
- Decision-tree interrogation probes for gaps beyond what analysis found
- No fixes applied without user confirmation
</success_criteria>
