---
name: triage-pr-comments
description: >
  Triage pull request comments by fetching from GitHub, analyzing each against
  codebase context and domain docs, and deciding fix vs. ignore vs. defer.
  Use when addressing PR feedback, handling code review comments, or following up on reviews.
---

Systematically triage all review comments on the current branch's pull request. Produce a per-comment analysis with clear decisions, confirm with the user, then execute: resolve dismissed threads, log deferred items, and implement accepted changes.

<essential_principles>

1. **Actual usage over theoretical possibility.** P(bug) is determined by how code is actually used — parent components, lifecycle, real data volumes — not by what could theoretically happen in isolation.

2. **Code review serves maintainability, not just correctness.** A comment does not need to identify a bug to be worth acting on. Architecture, pattern enforcement, and test coverage are legitimate review concerns. "Other code does it too" is not a valid justification for writing new code in an old pattern.

</essential_principles>

<process>

## 1. Gather context

Find the PR for the current branch and fetch its metadata:

```bash
gh pr list --head $(git branch --show-current) --json number,title,url,baseRefName,body --limit 1
gh repo view --json nameWithOwner -q .nameWithOwner
```

If no PR found, inform the user and stop.

**Read the PR body** — it often contains links to tickets or context that inform the triage.

**Fetch linked tickets.** If the PR body, branch name, or commit messages reference Linear tickets, fetch each one (plus parent epic and blockers) before triage. The Scope check depends on this context.

```bash
uv run ~/.claude/skills/linear/scripts/linear.py get TICKET-ID -c
```

Follow `parent.identifier` and `relations` entries (`blocks`/`blocked_by`) to fetch related tickets in parallel.

**Read domain docs.** Check for `CONTEXT.md` (domain glossary) and `docs/adr/` (architecture decisions) in the project root. If a `CONTEXT-MAP.md` exists, the repo has multiple contexts — follow the map to the relevant one. Use domain vocabulary from CONTEXT.md throughout the analysis. Reference relevant ADRs when they inform a triage decision — especially when a reviewer's suggestion contradicts a settled architectural decision.

Read `references/github-api-reference.md` for fetch commands.

Fetch both review comments (inline on code) and issue-level comments (top-level). Use `--paginate`. Filter out:
- Reply comments (`in_reply_to_id != null`) — keep only thread starters
- Bot summary/walkthrough comments (poems, checkboxes, automated summaries) — keep only actionable review findings
- Resolved threads — query thread resolution status via the GraphQL `reviewThreads` query (see `references/github-api-reference.md`). Match each review comment's `id` to the GraphQL `databaseId`. Exclude resolved threads.

Present a numbered inventory of unresolved comments:

```
| # | Source | File | Summary |
|---|--------|------|---------|
| 1 | @reviewer | `File.vue:42` | One-line description |
```

Note the count of excluded resolved threads above the table. Flag any duplicates.

## 2. Explore code context

Build enough context to triage each comment — understand the referenced code, how it's used, and relevant patterns.

For a handful of comments touching a few files, read directly. When comments span many files or require tracing complex call chains, use parallel explore subagents.

Also check:
- Are any commented files synced from another repo? (`git log --oneline -20` for "sync" commits)
- Does AGENTS.md / CLAUDE.md contain relevant ownership or build notes?

## 3. Triage each comment

Read `references/triage-framework.md` for the 4-question model and decision matrix.
Read `references/comment-analysis-format.md` for the output format.

Apply the framework to each comment. Determine one of:

- **ACT** — fix is needed, approach is clear
- **JUST FIX IT** — trivial fix, cheaper to do than to discuss
- **DEFER** — valid issue, wrong venue. Log as Linear ticket for future work.
- **IGNORE** — not a real issue (P(bug) = 0, wrong analysis, permanently out of scope)
- **INVESTIGATE** — P(bug) is uncertain, need more information

Present the full analysis using the per-comment format from `references/comment-analysis-format.md`. When the reviewer's proposed fix is suboptimal, propose a better alternative.

## 4. Investigate uncertain comments

For comments marked INVESTIGATE, read `references/investigation-guide.md` for verification methods (agent-browser or manual user verification). After results are in, update the triage decision to ACT or IGNORE.

## 5. Resolve uncertainty with the user

For comments with MEDIUM or LOW confidence, consolidate questions and present via the question tool. Each question should include context, 2-3 options with descriptions, and a recommended option. Batch related questions when possible.

## 6. Present final summary and confirm

After all questions are answered and investigations complete, present:

1. **Full per-comment analysis** — every comment with its reasoning chain and final decision
2. **Summary table: changes to make** — ACT + JUST FIX IT items with file, change description, priority
3. **Summary table: comments to defer** — with one-line ticket description per comment
4. **Summary table: comments to ignore** — with brief rationale per comment
5. **Assumptions** — list all assumptions that informed decisions

Confirm all ACT/IGNORE/DEFER decisions with the user before proceeding.

## 7. Handle IGNORE and DEFER comments

### IGNORE comments

For each: reply with a concise explanation of why it's not being addressed, then resolve the thread.

### DEFER comments

For each:

1. **Check for existing tickets first.** Invoke `/linear` to search for outstanding tickets covering the same issue (Backlog, Todo, In Progress states). If a match exists, reply "Valid issue — already tracked as [TICKET-ID]," resolve the thread, and skip creation.

2. **Create a ticket if no match.** Invoke `/linear` with: the "What this means" paragraph from the analysis, why it was deferred, specific files and patterns affected, and the PR number.

3. Reply "Valid issue — logged as [TICKET-ID] for future work" with a brief note on why it's deferred. Resolve the thread.

Read `references/github-api-reference.md` for reply and resolve commands. Run replies in parallel, then fetch thread IDs and resolve in parallel.

Do NOT reply to or resolve ACT comments — those will be addressed by the implementation.

## 8. Plan and implement

Enter plan mode. Create an implementation plan for all ACT comments:
- Group related changes by file
- Order by priority
- Include specific code changes with file paths and line references
- Note dependencies between changes

The plan must include a final reply-and-resolve step: for each implemented ACT comment, reply on the PR with what was done and resolve the thread. Include a comment resolution table:

```
| Comment ID | File | What was done | Thread to resolve |
|------------|------|---------------|-------------------|
```

After the user approves the plan, execute the implementation.

</process>

<reference_index>
Supporting files in `references/`:
- `triage-framework.md` — The 4-question triage model, decision matrix, and Core Equation. Read in step 3.
- `comment-analysis-format.md` — Output template for per-comment analysis and summary tables. Read in step 3.
- `github-api-reference.md` — gh CLI commands for fetching, replying to, and resolving PR comments. Read in steps 1, 7, and 8.
- `investigation-guide.md` — How to verify INVESTIGATE comments via agent-browser or manual user verification. Read in step 4.
</reference_index>

<success_criteria>

- [ ] Confirm all triage decisions with the user before proceeding — never skip confirmation
- [ ] Linked Linear tickets (plus parent epics and blockers) fetched before triage — skipped only if none referenced
- [ ] CONTEXT.md vocabulary used in analysis when available; relevant ADRs referenced when they inform a decision
- [ ] Comments requiring investigation verified via agent-browser or escalated to user — never silently assumed
- [ ] Ignored comments replied to on GitHub with reasoning and threads resolved
- [ ] Deferred comments checked against existing Linear tickets before creating new ones
- [ ] Implementation plan created in plan mode before code changes, with comment resolution table

</success_criteria>
