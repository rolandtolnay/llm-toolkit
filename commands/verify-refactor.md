---
description: Verify refactored code preserves behavior, handles edge cases, and introduces no regressions
argument-hint: <context about the refactoring - what was changed and why>
---

<objective>
Verify refactored code introduces no regressions or correctness issues using **behavioral diff analysis**: reconstruct what the code did before, what it does now, and surface any gaps, regressions, or missed edge cases.
</objective>

<context>
**User's verification request:**
$ARGUMENTS

**Current git status:**
!`git status --short`
</context>

<process>

Scan the skill list in your system message. Match skill descriptions against the technology stack and domain of the code being verified. Invoke matching skills via the Skill tool to load domain expertise before verification begins. If exactly one skill clearly matches, invoke it directly. If multiple candidates match, use AskUserQuestion to let the user select which to load. If none match, proceed without.

## Phase 1: Establish Verification Scope

### Step 1.1: Clarify Change Scope

Use AskUserQuestion to determine what code changes to verify:

```
Question: "What code changes should I verify?"
Options:
- "Uncommitted changes" - Verify current uncommitted work (git diff)
- "Specific commits" - Verify a commit or range (ask for commit refs)
- "All changes on branch" - Verify all commits since branching from main
```

Based on user selection, gather the relevant changes:
- Uncommitted: `git diff` and `git diff --cached`
- Specific commits: `git show <commit>` or `git diff <from>..<to>`
- Branch changes: `git diff main...HEAD`

### Step 1.2: Understand Refactoring Intent

If `$ARGUMENTS` already describes the intent, skip to Phase 2.

Otherwise, use AskUserQuestion to clarify:
1. What was the refactoring trying to improve? (readability, performance, structure, etc.)
2. What specific files or modules were refactored?

## Phase 2: Reconstruct Behavioral Contracts

### Step 2.1: Identify Changed Functions/Components

From the diff, list every function, method, class, or component that was modified. For each, document:
- **Inputs**: parameters, state dependencies, external data
- **Outputs**: return values, side effects, state mutations, emitted events
- **Error handling**: what exceptions/errors are caught, thrown, or propagated

### Step 2.2: Map Edge Cases in Original Code

For each changed function, examine the **removed lines** (- lines in diff) and identify:
- Boundary checks (null, empty, zero, negative, overflow)
- Special-case branches (if/else, switch, guard clauses)
- Error/exception handling paths
- Default values and fallback logic
- Type coercion or conversion handling

These are the edge cases the original code explicitly handled.

### Step 2.3: Map Control Flow Changes

Identify structural changes that could alter behavior:
- Reordered operations (order may matter for side effects)
- Changed loop structures (for to map, while to recursion, etc.)
- Modified conditional logic (merged/split branches, inverted conditions)
- Altered async/await patterns or promise chains
- Changed error propagation paths

## Phase 3: Regression Analysis

Use Explore agents (Task tool with subagent_type=Explore) to gather caller sites, module context, and related code needed for Steps 3.1-3.2.

### Step 3.1: Build Findings

Analyze the diff against the behavioral contracts, edge cases, and control flow changes from Phase 2. For each issue found, record a **finding** with:

- **Location**: file path and line number(s)
- **Severity**: 🛑 Blocker / ⚠️ Warning / ℹ️ Info
- **Confidence**: Certain (provably different behavior) / Likely (strong evidence) / Possible (worth investigating)
- **What changed**: Before/after code snippets (3-5 lines each) showing the actual difference
- **Why it matters**: The concrete failure scenario — what input or state would trigger wrong behavior

Severity definitions:
- 🛑 **Blocker**: Provably incorrect — dropped edge case, inverted condition, resource leak, null dereference path
- ⚠️ **Warning**: Likely regression or behavioral change that may be unintended
- ℹ️ **Info**: Notable change worth reviewing but not evidently broken

Bug patterns to check:
- **Off-by-one errors**: loop bounds, slice indices, range comparisons
- **Null/undefined propagation**: optional chaining removed, null checks dropped
- **Scope changes**: variable hoisting, closure captures, this-binding
- **Short-circuit evaluation**: changed && / || / ?? order
- **Type coercion**: implicit conversions introduced or removed
- **Race conditions**: async operations reordered
- **Resource leaks**: cleanup/dispose/close calls removed or bypassed
- **API contract violations**: changed return types, missing fields, altered error types

### Step 3.2: Caller/Consumer Impact

Check all callers of changed functions/components:
- Do callers still pass valid arguments?
- Do callers handle the return values correctly?
- Are any callers relying on behavior that changed?

Record caller issues as findings with the same severity/confidence format.

### Step 3.3: Improvement Assessment

Briefly assess whether the refactoring delivers its stated intent:
- Does the refactored code actually improve what it claims to?
- Did the refactoring introduce unnecessary complexity?

## Phase 4: Determine Overall Status

- **CLEAN**: No findings at ⚠️ or 🛑 severity
- **ISSUES FOUND**: One or more 🛑 or ⚠️ findings
- **NEEDS MANUAL TEST**: Code analysis alone cannot confirm correctness for some behaviors

If both issues and untestable behaviors exist, use ISSUES FOUND and include section 6.

</process>

<output_format>

### 1. Verification Summary

Scope, refactoring intent, overall status (CLEAN | ISSUES FOUND | NEEDS MANUAL TEST), and counts: N findings (X 🛑, Y ⚠️, Z ℹ️).

### 2. Findings (severity-ordered)

List all findings grouped by severity (🛑 first, then ⚠️, then ℹ️). Each finding:

```
### 🛑 F1: [Short description]
**Location:** `path/to/file.ts:42`
**Confidence:** Certain / Likely / Possible
**What changed:**
// Before:
[3-5 lines of old code]
// After:
[3-5 lines of new code]
**Why it matters:** [Concrete failure scenario — what input/state triggers wrong behavior]
```

### 3. Verified Safe

Compact bulleted list of behavioral contracts that were checked and confirmed preserved. One line each, no detail needed — this section builds confidence the analysis was thorough without consuming space.

### 4. Improvement Assessment

2-3 sentences: does the refactoring deliver its stated improvement? Any unnecessary complexity introduced?

### 5. Action Items (if issues found)

Numbered list referencing finding IDs, with specific fix actions as checkboxes:
```
1. **F1** — [description]
   - [ ] Fix action
   - [ ] Fix action
```

### 6. Manual Testing Required (if applicable)

Checklist of behaviors that need human verification.

</output_format>

<success_criteria>
- Findings include before/after code snippets — not abstract descriptions but actual changed lines
- Each finding has a concrete failure scenario explaining what input/state triggers wrong behavior
- Edge cases from removed code verified in new code — dropped edge cases are 🛑 severity
- Callers of changed functions checked for compatibility
- Verified Safe section confirms what was checked and passed
</success_criteria>
