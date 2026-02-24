---
description: Analyze unpushed commits for squash and streamlining opportunities
---

<objective>
Analyze all unpushed commits on the current branch, identify meaningful squash or streamlining opportunities, and execute user-approved changes via interactive rebase.
</objective>

<context>
- Remote tracking: !`git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "no upstream"`
- Commit details: !`git log --format="%h %s%n%b---" @{upstream}..HEAD 2>/dev/null || git log --format="%h %s%n%b---" origin/main..HEAD 2>/dev/null`
- Files changed per commit: !`git log --stat --format="%h %s" @{upstream}..HEAD 2>/dev/null || git log --stat --format="%h %s" origin/main..HEAD 2>/dev/null`
</context>

<process>

1. **Determine base ref.** Use the upstream tracking branch. Fall back to `origin/main`. If neither exists, ask the user for the base ref.

2. **Bail early if nothing to do.** If fewer than 2 unpushed commits exist, tell the user there's nothing to tidy and stop.

3. **Analyze commits for squash opportunities.** Look for these patterns:
   - **Iterative refinement** — multiple commits touching the same feature/area in sequence (e.g., "add X", "refactor X", "fix X typo"). These are the highest-value squashes.
   - **Fixup commits** — a later commit corrects something introduced by an earlier commit (naming, typo, missing file). Fold into the original.
   - **Cross-cutting fixes** — a single commit that fixes issues spanning multiple earlier commits. Flag these as potentially needing a split before folding.
   - **Overlapping file changes** — multiple commits modifying the same files may indicate related work worth combining.

   For each group, assess:
   - Which commits belong together and why
   - Whether reordering is needed (and if file overlap between commits could cause conflicts)
   - What the resulting commit message should be
   - Whether any commit is cross-cutting and would benefit from splitting

4. **Present findings.** Show a clear summary table of the current commits, then describe each proposed squash group with:
   - The commits involved
   - Why they should be combined
   - The proposed resulting commit message
   - Any conflict risks from reordering

   If no meaningful squash opportunities exist, say so and stop. Do not force unnecessary changes.

5. **Confirm with the user.** Use AskUserQuestion with options like:
   - "Apply all suggestions"
   - "Let me pick which groups to squash" (then present each group individually)
   - "Show me more detail first"
   - (The implicit "Other" option covers custom requests)

   If the user wants to pick, present each squash group as a separate AskUserQuestion.

   **Before proceeding:** Capture pre-rebase baseline by running `git diff --stat <base>..HEAD` and storing the output for post-rebase verification.

6. **Execute the rebase.** For each approved squash:
   - Build a `GIT_SEQUENCE_EDITOR` script that writes the desired todo (pick/fixup/drop/edit)
   - Run `GIT_SEQUENCE_EDITOR=/tmp/rebase-tidy.sh git rebase -i <base>`
   - If a commit needs splitting (cross-cutting fix), use `edit` to pause, then manually apply the relevant changes to each target commit

   When reordering commits, check for file overlap between the moved commit and commits it will leapfrog. Warn about potential conflicts before proceeding.

   For multi-pass rebases (e.g., squash first, then fold fixes), execute sequentially — get new hashes between passes.

7. **Verify integrity.** After rebase completes:
   - Run `git diff --stat <base>..HEAD` and confirm the file list and line counts match the pre-rebase snapshot
   - Show the final commit log
   - If line counts differ, warn the user immediately

</process>

<success_criteria>
- Post-rebase diff stat matches pre-rebase diff stat (no content lost or duplicated)
- Cross-cutting commits identified and flagged before rebase (not discovered as conflicts mid-rebase)
- User confirms before any history rewrite
- Every proposed squash group includes clear rationale (not just "these touch the same files")
- Final commit history shown to the user for review
</success_criteria>
