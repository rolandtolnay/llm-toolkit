---
name: triage-pr-comments
description: >
  Triage pull request comments by fetching from GitHub, analyzing each with a systematic
  framework to decide fix vs. ignore, resolving dismissed threads, and planning fixes.
  Use when addressing PR feedback, handling code review comments, or following up on reviews.
---

<objective>
Systematically triage all review comments on the current branch's pull request. Fetch comments, explore code context, apply a structured triage framework to each, resolve dismissed threads, log deferred items as Linear tickets, and create an implementation plan for accepted changes.
</objective>

<essential_principles>

1. **Actual usage over theoretical possibility.** P(bug) is determined by how code is actually used — parent components, lifecycle, real data volumes — not by what could theoretically happen in isolation.

2. **Code review serves maintainability, not just correctness.** A comment does not need to identify a bug to be worth acting on. Architecture, pattern enforcement, and test coverage are legitimate review concerns. When a reviewer says "we're moving away from X pattern," evaluate against the team's intended direction — not the current codebase state. "Other code does it too" is not a valid justification for writing new code in an old pattern.

</essential_principles>

<process>

## Step 1: Fetch PR comments

Find the PR for the current branch and get repo identity:

```bash
gh pr list --head $(git branch --show-current) --json number,title,url,baseRefName,body --limit 1
gh repo view --json nameWithOwner -q .nameWithOwner
```

If no PR found, inform the user and stop.

**Read the PR `body`** — it often contains links to tickets, issues, or context that inform the triage. Note any ticket or issue references for Step 2.

Read `references/github-api-reference.md` for fetch commands.

Fetch both review comments (inline on code) and issue-level comments (top-level). Use `--paginate` to get all pages. Filter out:
- Reply comments (`in_reply_to_id != null`) — keep only thread starters
- Bot summary/walkthrough comments (CodeRabbit poems, checkboxes, automated summaries) — keep only actionable review findings
- **Resolved threads** — query thread resolution status via the GraphQL `reviewThreads` query (see `references/github-api-reference.md`). Match each review comment's `id` to the GraphQL `databaseId`. Exclude comments whose threads are already resolved — these have been addressed and don't need triage.

Present a numbered inventory of **unresolved** comments to the user, grouped by source. Note the count of excluded resolved threads above the table.

```
| # | Source | File | Summary |
|---|--------|------|---------|
| 1 | @reviewer | `File.vue:42` | One-line description |
```

Note any duplicates (e.g., bot echoing a human's comment).

## Step 2: Explore code context

Identify all unique files referenced by comments. Build enough context to triage each comment — this means understanding the referenced code, how it's used, and relevant patterns.

For a handful of comments touching a few files, reading directly may be fastest. When comments span many files or require tracing complex call chains, use parallel Explore subagents to gather context without bloating the main conversation.

Also check project-level context:
- Are any commented files (e.g., proto files) synced from another repo? Check `git log --oneline -20` for "sync" commits.
- Does CLAUDE.md contain relevant ownership or build notes?

**Fetch Linear ticket context** if the PR description, branch name, or commit messages reference any tickets or issues. Don't just scan for ID patterns — read the PR body from Step 1 and follow any links to tickets, epics, or issues. Invoke the `/linear` skill to fetch each referenced ticket including its comments. Also fetch related tickets (parent epic, blocking/blocked-by) since they often contain the broader motivation and acceptance criteria that inform whether a reviewer's suggestion is in scope. This context helps distinguish "valid concern but out of scope for this ticket" from "this contradicts what the ticket requires."

## Step 3: Triage each comment

Read `references/triage-framework.md` for the 4-question model and decision matrix.
Read `references/comment-analysis-format.md` for the output format.

Apply the framework to each comment using context from Step 2. Walk through Scope → Likelihood → Fix assessment and determine:

- **ACT** — fix is needed, approach is clear
- **JUST FIX IT** — trivial fix, cheaper to do than to discuss
- **DEFER** — valid issue, wrong venue. Log as Linear ticket for future work.
- **IGNORE** — not a real issue (P(bug) = 0, wrong analysis, permanently out of scope)
- **INVESTIGATE** — P(bug) is uncertain, need more information

Present the full analysis to the user using the per-comment format from `references/comment-analysis-format.md`. When the reviewer's proposed fix is suboptimal, propose a better alternative.

## Step 4: Handle investigations

For comments marked INVESTIGATE, read `references/investigation-guide.md` for how to verify them (via agent-browser or manual user verification). After results are in, update the triage decision to ACT or IGNORE.

## Step 5: Present open questions

For comments with **MEDIUM or LOW** confidence, consolidate questions and present via **AskUserQuestion**. Each question should include:
- Context: which comment and what the uncertainty is
- 2-3 options with descriptions
- A recommended option based on best judgment

Batch related questions into a single AskUserQuestion call when possible.

## Step 6: Present final summary

After all questions are answered and investigations complete, present:

1. **Full per-comment analysis** — every comment with its reasoning chain and final decision
2. **Summary table: changes to make** — ACT + JUST FIX IT items with file, change description, priority
3. **Summary table: comments to defer** — with one-line ticket description per comment
4. **Summary table: comments to ignore** — with brief rationale per comment
5. **Assumptions** — list all assumptions that informed decisions

## Step 7: Confirm and save

Offer to save the full analysis to `etc/personal/pr-{number}-comment-triage.md`. If saving, use the saved analysis format from `references/comment-analysis-format.md` and include a Key Insights section with project-specific learnings.

Confirm the ACT/IGNORE/DEFER decisions with the user before proceeding. Incorporate any adjustments.

## Step 8: Handle IGNORE and DEFER comments

### IGNORE comments

For each IGNORE comment on the PR:
1. Reply with a concise explanation of why it's not being addressed
2. Resolve the thread

### DEFER comments

For each DEFER comment:

1. **Check for existing tickets first.** Before creating anything, invoke the `/linear` skill to search for outstanding tickets that already cover the same issue. Search by relevant keywords from the comment (e.g., "keyboard navigation table rows", "pre-tax amounts"). Check tickets in Backlog, Todo, and In Progress states. If a matching ticket exists:
   - Skip ticket creation
   - Reply on the PR comment: "Valid issue — already tracked as [TICKET-ID]. [Brief note on why it's deferred]."
   - Resolve the thread
   - Move on to the next DEFER comment

2. **Create a ticket only if no match found.** Invoke the `/linear` skill to create a ticket. Pass these as context for the skill to structure per its own format:
   - The **"What this means"** paragraph from the triage analysis (this is the core of the ticket description)
   - Why it was deferred (e.g., "requires cross-page consistency", "not a regression, needs dedicated effort")
   - The specific files and patterns affected
   - The PR number where this was identified

3. Reply on the PR comment: "Valid issue — logged as [TICKET-ID] for future work." Include a brief note on why it's deferred (e.g., "needs a cross-page effort to maintain consistency").

4. Resolve the thread

Read `references/github-api-reference.md` for reply and resolve commands.

Run replies in parallel. Then fetch thread IDs and resolve threads in parallel.

Do NOT reply to or resolve comments that are being ACT'd on — those will be addressed by the implementation.

## Step 9: Plan and implement

Enter plan mode. Create an implementation plan for all ACT comments:
- Group related changes by file
- Order by priority (P1 first)
- Include specific code changes with file paths and line references
- Note dependencies between changes

**The plan MUST include these two final steps** (the user may clear context after approving the plan, so these instructions must be self-contained in the plan document):

1. **Reload context step:** "Invoke the `/triage-pr-comments` skill or read `etc/personal/pr-{number}-comment-triage.md` to reload the comment triage context (PR number, repo, comment IDs, and what was addressed)."

2. **Reply and resolve step:** "For each ACT comment that was implemented, reply on the PR with a brief description of what was done (e.g., 'Fixed — added pagination loop matching the pattern in DetailPage.vue') and resolve the thread. Use `references/github-api-reference.md` for the API commands. Include the comment IDs and their corresponding changes in a table within the plan so the executor has everything needed without the original conversation context."

The plan must embed a **comment resolution table** listing every ACT comment with:

```
| Comment ID | File | What was done | Thread to resolve |
|------------|------|---------------|-------------------|
| 2953283704 | DetailPage.vue:416 | Added CANCELLATION_REQUESTED to sidebarActionMap | Yes |
```

After the user approves the plan, execute the implementation.

</process>

<reference_index>
Supporting files in `references/`:
- `triage-framework.md` — The 4-question triage model, decision matrix, and when-to-investigate guide. Read in Step 3.
- `comment-analysis-format.md` — Output template for per-comment analysis and summary tables. Read in Step 3.
- `github-api-reference.md` — gh CLI commands for fetching, replying to, and resolving PR comments. Read in Steps 1, 8, and 9.
- `investigation-guide.md` — How to verify INVESTIGATE comments via agent-browser or manual user verification. Read in Step 4.
</reference_index>

<success_criteria>
- [ ] Comments requiring investigation are either verified via agent-browser or escalated to user — never silently assumed
- [ ] All MEDIUM/LOW confidence decisions presented to user for confirmation before acting
- [ ] Ignored comments replied to on GitHub with reasoning and threads resolved
- [ ] Deferred comments checked against existing Linear tickets before creating new ones — duplicates reference the existing ticket instead
- [ ] Implementation plan created in plan mode before any code changes
- [ ] Plan includes comment resolution table with IDs, changes, and instructions to reply/resolve after implementation
- [ ] Plan includes instruction to reload triage context (skill or saved analysis) in case of context clear
</success_criteria>
