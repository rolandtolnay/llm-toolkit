---
name: create-pr
description: Open a pull request whose description explains why the change exists, then hand back a reusable summary for Slack or release notes. Use when changes are ready to ship.
disable-model-invocation: true
argument-hint: "[commit instructions or additional context]"
---

<objective>
Open a pull request against the default base branch with a description that explains the change — what problem it solves and why this approach — not just what the diff touched. Finish by handing back a distilled summary the engineer can repurpose for Slack, release notes, or a changelog.
</objective>

<context>
Start by inspecting the repo state yourself with git. Establish enough to choose how to land the change:

- the current branch, and what's staged vs unstaged
- the default base branch (`git symbolic-ref --short refs/remotes/origin/HEAD`, falling back to `origin/main`)
- commits on this branch vs base, and the diff stat
- the repo's recent commit-message style (`git log --oneline -5`)
</context>

<what-good-looks-like>
A reviewer reads the description and understands the motivation before the mechanics. Linear tickets are linked inline where they add context, not dumped in a list. Changes are grouped by logical area, not by file. The test plan says how to verify the change. The closing summary is 2-3 plain sentences an engineer can paste elsewhere with minimal edits.
</what-good-looks-like>

<constraints>
- Never create a branch, commit, or push without confirming the plan first. Uncommitted work is easy to lose — confirm before stashing or switching branches.
- If the arguments carry commit instructions (e.g. "use the last 3 commits", "cherry-pick abc123"), follow them over the default landing choice.
- If the branch is the base branch with no changes, say there's nothing to PR and stop.
</constraints>

<process>

Lead with a one-sentence preamble — acknowledge the request and name your first step — before doing any work.

**Land the change.** Pick how the change reaches a PR-able branch, confirm it with the user, then execute. Match the repo's existing commit style.

- *Branch already ahead of base* → PR from it. Commit any uncommitted changes first, then push.
- *Uncommitted changes on the base branch* → move them to a new branch. Confirm a name with the user, then: stash → `git fetch origin <base> && git checkout -b <name> origin/<base>` → `git stash pop` → commit.
- *Uncommitted changes to isolate off a busy branch* → same new-branch flow, carrying only those changes.

**Gather the why.** Get just enough to explain the motivation, the problem, and any notable alternative considered. The current conversation is often enough — reach further only when the why is still thin:

- Past sessions for this project — if you can search them — for multi-session work or a fresh "just make a PR" invocation.
- The Linear ticket plus its parent and blocking tickets — whenever a ticket ID appears in the branch, commits, conversation, or arguments. Fetch it from Linear; the ticket often holds context the conversation never mentioned.
- The driving PRD, if one exists (often under `etc/prd/`) — it states the problem, the solution, and the decisions this change implements.
- The project's domain docs — `CONTEXT.md` (or a root `CONTEXT-MAP.md`) for the canonical terms to name things correctly, and relevant ADRs under `docs/adr/` for why a non-obvious approach was chosen.

Stop gathering once you can state why the change exists. If the why can't be recovered from any source, describe what the change does and flag the missing rationale in the PR — don't fabricate a motivation.

**Write the PR.** Combine the diff (what changed), the gathered why, and any arguments passed in. Ground the motivation in the diff, conversation, or ticket — don't invent reasoning to make the change sound stronger:

```
## Summary

[1-3 paragraphs. Lead with the motivation and problem, then the solution and the reasoning that shaped it. Weave Linear links into the prose where they add context — "This resolves [ENG-123](url) by…" — covering the primary ticket and any parent or blocking issues. Don't list them separately.]

### Ticket

[Standalone link only if there's a single primary ticket — "Resolves [ENG-123](url)". Omit otherwise.]

### Changes

[Bulleted, grouped by logical area, not by file.]

## Test plan

[Checklist of how to verify the change works.]
```

**Humanize the draft.** Draft the description in your own voice first — don't read the humanizer before writing. Once the draft above exists, read `~/.pi/agent/skills/humanizer/SKILL.md` and follow it to revise the description, including its anti-AI audit pass. The order matters: revising concrete text produces cleaner prose than writing from the rules cold, which comes out stiff and self-conscious. Preserve the structure, facts, and ticket links — only the wording changes. Carry the revised description into Confirm.

**Confirm.** Show the complete PR title and body in chat for the user to confirm or edit. Apply any changes they ask for.

**Create.** Push if needed, then create the PR against the default base branch:

```bash
gh pr create --title "<title>" --body "<body>" --base "$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||' || echo main)"
```

Return the PR URL.

**Hand back a reusable summary.** Close with a 2-3 sentence distilled summary of the PR — what shipped and why, leading with the user-facing outcome. Plain prose, no headers or ticket links, written so the engineer can drop it into Slack, a release note, or a changelog. Draw only from what the PR actually contains; don't invent metrics or outcomes.

</process>

<success_criteria>
- [ ] No branch creation, commit, or push ran without the user confirming the plan
- [ ] Branch name confirmed with the user when a new branch is created
- [ ] The why was sourced from the conversation, and from past sessions, Linear, the PRD, or domain docs when the conversation was thin
- [ ] Linear ticket and related tickets fetched whenever a ticket ID appeared in context
- [ ] PR description leads with motivation, links tickets inline, and groups changes by logical area
- [ ] Description drafted in normal voice first, then revised with the humanizer — draft-then-edit, never edit-first
- [ ] Full PR body shown for confirmation before creation
- [ ] PR URL returned
- [ ] Closed with a 2-3 sentence reusable summary an engineer can repurpose for Slack or release notes
</success_criteria>
