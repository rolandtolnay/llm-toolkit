---
name: verify-work
description: Verify code changes actually achieve requirements/proposal using goal-backward verification
argument-hint: <what to verify - requirements, proposal, or goals>
---

<objective>
Verify code changes achieve their intended goal using **goal-backward verification**: start from what SHOULD be true if requirements are met, then verify the code delivers it.
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

### Step 1.2: Clarify Requirements

If `$ARGUMENTS` already specifies clear, testable goals, skip to Phase 2.

Analyze the user's verification request. If any of these are unclear, use AskUserQuestion to clarify:

1. What is the goal/outcome being verified? (not tasks, but user-observable results)
2. What files or areas are expected to be affected?
3. Are there specific behaviors that must work?

**Keep asking until you can state 3-7 observable, testable truths that must be TRUE for the goal to be achieved.**

## Phase 2: Derive Must-Haves (Goal-Backward)

### Step 2.1: Derive Observable Truths

From the clarified requirements, ask: "What must be TRUE for this goal to be achieved?"

List 3-7 truths from the user's perspective. Each truth must be:
- Observable (can be seen/tested by using the app)
- Specific (clear pass/fail criteria, not "works correctly")

### Step 2.2: Derive Required Artifacts

For each truth, ask: "What must EXIST for this truth to hold?"

Map truths to concrete file paths — specific files, not descriptions like "login component".

### Step 2.3: Derive Key Links

For each artifact, ask: "What must be CONNECTED for this to function?"

Identify critical wiring between layers (UI → logic → data → external services). **This is where stubs hide** — pieces exist but aren't connected.

## Phase 3: Verify Against Codebase

Use Explore agents (Task tool with subagent_type=Explore) to locate and analyze code. Do NOT trust file existence alone.

### Step 3.1: Verify Artifacts (Three Levels)

For each required artifact:

**Level 1 — Existence:** Does the file exist?

**Level 2 — Substantive:** Real implementation or stub? Contains meaningful logic beyond boilerplate. Scan for stub indicators: TODO/FIXME markers, placeholder returns, empty handlers, logging-only implementations.

**Level 3 — Wired:** Imported, used, and connected to the system?

| Exists | Substantive | Wired | Status |
|--------|-------------|-------|--------|
| ✓ | ✓ | ✓ | ✓ VERIFIED |
| ✓ | ✓ | ✗ | ⚠️ ORPHANED |
| ✓ | ✗ | - | ✗ STUB |
| ✗ | - | - | ✗ MISSING |

### Step 3.2: Verify Key Links

For each critical connection from Step 2.3, verify:
- The call, import, or binding exists in code
- The response or result is used (not ignored or replaced with static data)
- Data flows through to the next layer (not hardcoded at any boundary)

### Step 3.3: Verify Observable Truths

For each truth from Step 2.1:
1. Identify supporting artifacts and links
2. Check their status from Steps 3.1-3.2
3. Determine truth status:
   - ✓ **VERIFIED:** All supporting artifacts and links pass
   - ✗ **FAILED:** One or more artifacts missing, stub, or unwired
   - ? **UNCERTAIN:** Cannot verify programmatically (needs manual test)

## Phase 4: Anti-Pattern Scan

Scan all changed files. Categorize findings by severity:
- 🛑 **Blocker:** Prevents goal achievement (placeholder renders, empty handlers, hardcoded data where dynamic expected)
- ⚠️ **Warning:** Indicates incomplete work
- ℹ️ **Info:** Notable but not blocking

## Phase 5: Determine Overall Status

- **PASSED:** All truths verified, no blockers
- **GAPS FOUND:** One or more truths failed or blockers found
- **NEEDS MANUAL TEST:** Automated checks pass but some truths need human verification

</process>

<output_format>
**Required sections:**
1. **Verification Summary** — Scope, requirements summary, status (PASSED | GAPS FOUND | NEEDS MANUAL TEST), score (N/M truths)
2. **Observable Truths** — Table: #, truth, status (✓/✗/?), evidence
3. **Artifacts Verified** — Table: artifact path, exists, substantive, wired, status
4. **Key Links** — Table: from, to, status, issue (if broken)
5. **Anti-Patterns Found** — Table: file, line, pattern, severity (🛑/⚠️/ℹ️)
6. **Action Items** (if gaps found) — Numbered list per failed truth, with specific fix actions as checkboxes
7. **Manual Testing Required** (if applicable) — Checklist of what needs human verification
</output_format>

<success_criteria>
- Key links verified between layers (not just artifact existence)
- Anti-patterns scanned with severity categorization
- 3-7 observable truths derived and each verified at artifact level (exists, substantive, wired)
- If gaps found: numbered action items with specific fix actions
- Clear status determined (PASSED / GAPS FOUND / NEEDS MANUAL TEST)
</success_criteria>
