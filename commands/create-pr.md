---
description: Create a pull request with a context-rich summary derived from code changes and conversation context
argument-hint: [commit instructions or additional context]
---

<objective>
Create a pull request targeting main with a descriptive summary that combines code diff analysis with reasoning extracted from past conversations in this project.
</objective>

<context>
- Current branch: !`git branch --show-current`
- Git status: !`git status --short`
- Uncommitted diff: !`git diff --stat`
- Staged diff: !`git diff --cached --stat`
- Remote tracking: !`git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "no upstream"`
- Default base branch: !`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo "origin/main"`
- Recent commits on this branch vs base: !`git log --oneline "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)"..HEAD 2>/dev/null || true`
- Working directory: !`pwd`
</context>

<process>

**Step 1 — Determine PR mode**

Analyze the context above and present the user with the appropriate options using `AskUserQuestion`:

- **If there are uncommitted changes AND the branch has no commits ahead of main**, offer:
  1. "New branch with uncommitted changes" — stash changes, update main, create a new branch, apply stash, commit, and PR
  2. "Commit to current branch and PR" — commit changes on the current branch and PR from there

- **If the current branch has commits ahead of main (with or without uncommitted changes)**, offer:
  1. "PR from current branch" — create PR from the current branch's commits (optionally committing any uncommitted changes first)
  2. "New branch with uncommitted changes only" — only if there are also uncommitted changes: isolate them onto a new branch

- **If on main with no changes**, tell the user there's nothing to PR and stop.

Always confirm the chosen mode before proceeding with any git operations.

If `$ARGUMENTS` contains commit instructions (e.g. "use the last 3 commits", "cherry-pick abc123"), follow those instructions instead of the default mode selection.

**Step 2 — Execute git operations (with confirmation)**

For **"New branch with uncommitted changes"** mode:
1. Propose a branch name based on the nature of the changes. Use `AskUserQuestion` to confirm the name.
2. Stash uncommitted changes.
3. Fetch and fast-forward local main: `git fetch origin main && git checkout main && git merge origin/main --ff-only`
4. Create the new branch from main: `git checkout -b <branch-name>`
5. Pop the stash: `git stash pop`
6. Stage and commit the changes with a descriptive commit message.

For **"PR from current branch"** mode:
1. If there are uncommitted changes, stage and commit them first.
2. Ensure the branch is pushed to origin.

For **"New branch with uncommitted changes only"** mode:
1. Propose a branch name based on the uncommitted changes. Use `AskUserQuestion` to confirm.
2. Stash uncommitted changes.
3. Create a new branch from main: `git fetch origin main && git checkout -b <branch-name> origin/main`
4. Pop the stash: `git stash pop`
5. Stage and commit the changes with a descriptive commit message.

**Step 3 — Gather context for PR summary**

The goal is to understand *why* these changes were made, *what problem* they solve, and *what alternatives* were considered — enough for a reviewer to understand the reasoning.

**Primary sources, in order:**

1. **Current conversation.** If the work was discussed, planned, and executed here, this is often sufficient on its own.

2. **Past conversations.** When the current conversation lacks context (e.g., multi-session work, or you were invoked fresh with just "create a PR"), search past conversations via an Explore subagent. Conversations are JSONL files at `~/.claude/projects/[encoded-path]/` where the encoded path is the working directory with `/` replaced by `-`, prefixed with `-`. The subagent should grep for keywords from the diff and extract motivation, decisions, and trade-offs.

3. **Linear tickets.** If a ticket ID appears anywhere in the context (commit messages, branch name, conversation, `$ARGUMENTS`), invoke the `/linear` skill to fetch the ticket. Also fetch related tickets (parent, blocking/blocked-by) if they exist — these often contain the broader motivation. Always do this when a ticket is referenced; don't skip it even if the conversation seems to have enough context, since the ticket may have details that weren't discussed.

**Step 4 — Compose PR summary**

Combine insights from:
- The code diff (what changed)
- The conversation context (why it changed)
- `$ARGUMENTS` (any additional context the user provided)

Draft the PR using this structure:

```
## Summary

[1-3 paragraphs: what changed and WHY — lead with the motivation/problem, then describe the solution. Use the conversation research to explain the reasoning that led to these changes.

Weave Linear ticket links naturally into the summary text where they provide context — e.g., "This resolves [ENG-123](linear-url) by..." or "As discussed in [ENG-456](linear-url), the approach...". Include links for all relevant tickets (the primary ticket, parent epics, related/blocking issues). Don't dump them in a separate list — they should read as part of the narrative.]

### Ticket

[If the PR addresses a single primary ticket, include a standalone link here — e.g., "Resolves [ENG-123](linear-url)". Omit this section if there is no clear primary ticket.]

### Changes

[Bulleted list of specific changes — group by logical area, not by file]

## Test plan

[Bulleted checklist of how to verify the changes work]
```

**Step 5 — Confirm with user**

Present the full PR title and summary as a regular chat message (not AskUserQuestion, to avoid truncation) and ask the user to confirm or request changes.

**Step 6 — Create PR**

Once confirmed:
1. Push the branch if not already pushed: `git push -u origin <branch-name>`
2. Create the PR: `gh pr create --title "<title>" --body "<body>" --base "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||' || echo main)"`
3. Return the PR URL.

**Step 7 — Post to Slack**

Load the `slack` skill using the `Skill` tool, then follow its `pr_announcement_flow` to compose and send the PR announcement to `#engineering-pr`.

- **If MISSING_TOKEN or AUTH_FAILED:** Skip this step silently — Slack is not configured.
- **If CHANNEL_NOT_FOUND:** Use `AskUserQuestion` to ask the user which channel to post in.

</process>

<success_criteria>
- [ ] No git operations (mode selection, branch creation, commit, push) executed without user confirmation
- [ ] Branch name confirmed via AskUserQuestion when creating a new branch
- [ ] PR context sourced from current conversation, past conversations, and/or Linear tickets as appropriate
- [ ] Linear ticket fetched via `/linear` skill whenever a ticket ID appears in context — including related tickets
- [ ] PR summary presented as regular chat message for user review before creation
- [ ] PR created with descriptive summary combining diff analysis and conversation reasoning
- [ ] PR URL returned to user
- [ ] Slack notification sent to `#engineering-pr` after user confirms the message draft (skipped silently if Slack not configured)
</success_criteria>
