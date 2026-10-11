---
name: create-pr
description: Open a pull request whose description explains why the change exists and how much review it needs. Use when changes are ready to ship.
argument-hint: "[commit instructions or additional context]"
---

Open a pull request against the default base branch with a description that explains the change: what problem it solves and why this approach, not just what the diff touched.

Invoking this skill is the go-ahead for the whole flow: committing what the branch needs, pushing, and opening the PR with the description you write. Ask first only before stashing or switching branches with uncommitted work, since that work is easy to lose, and propose the new branch name in that same question. If the branch is the base branch with no changes, say there is nothing to PR and stop. Arguments carrying commit instructions ("use the last 3 commits", "cherry-pick abc123") override the default landing choice.

## What good looks like

A reviewer reads the description and understands the motivation before the mechanics. Linear tickets are linked inline where they add context, not dumped in a list. Changes are grouped by logical area, not by file. The risk paragraph tells the reviewer how deeply to read and where, since reviewers route depth by blast radius, reversibility, and sensitive areas rather than by diff size. The test plan says how to verify the change. Every claim comes from the diff, the conversation, or the ticket: when the rationale cannot be recovered, describe what the change does and flag the missing why rather than inventing one, and add no metrics or outcomes the PR does not contain.

## Land the change

Inspect the repo with git: the current branch, staged versus unstaged work, the default base branch (`git symbolic-ref --short refs/remotes/origin/HEAD`, falling back to `origin/main`), commits and diff stat against base, and the recent commit-message style. Get the change onto a branch ahead of base without losing uncommitted work: a feature branch already ahead takes its uncommitted changes as a commit and a push; uncommitted work on the base branch, or work to isolate off a busy branch, moves to a new branch cut from the fetched base. Match the repo's existing commit style.

## Gather the why

Get just enough to explain the motivation, the problem, and any notable alternative considered. The current conversation is often enough; reach further only when the why is still thin:

- Past sessions for this project, if you can search them, for multi-session work or a fresh "just make a PR" invocation.
- The Linear ticket plus its parent and blocking tickets, whenever a ticket ID appears in the branch, commits, conversation, or arguments; the ticket often holds context the conversation never mentioned.
- The driving PRD, if one exists (often under `etc/prd/`): it states the problem, the solution, and the decisions this change implements.
- The project's domain docs: `CONTEXT.md` (or a root `CONTEXT-MAP.md`) for the canonical terms, and relevant ADRs under `docs/adr/` for why a non-obvious approach was chosen.

Stop gathering once you can state why the change exists.

## Write the PR

Combine the diff, the gathered why, and any arguments passed in:

```
## Summary

[1-3 paragraphs. Lead with the motivation and problem, then the solution and the reasoning that shaped it. Weave Linear links into the prose where they add context — "This resolves [ENG-123](url) by…" — covering the primary ticket and any parent or blocking issues. Don't list them separately.]

### Ticket

[Standalone link only if there's a single primary ticket — "Resolves [ENG-123](url)". Omit otherwise.]

### Changes

[Bulleted, grouped by logical area, not by file.]

## Risk

[One short paragraph: what breaks and who notices if this is wrong; whether a plain revert undoes it or a migration, data change, or external side effect does not; which sensitive areas it touches (auth, money, secrets, schema, infra, a new dependency, a module boundary); and which hunks deserve a careful read versus a skim. Derive it from the diff, not from confidence in the change. A mechanical, revert-safe change gets one sentence saying so.]

## Test plan

[Checklist of how to verify the change works.]
```

Draft the description in your own voice first, then humanize it with whatever the session provides for that (a humanize tool, or a humanizer skill read only after the draft exists) so it reads as a person wrote it for reviewers, with the structure, facts, and ticket links intact. Write the humanized description to a new file in a fresh temporary directory. Use the humanized text without further stylistic edits; fix a factual error with a targeted edit rather than another humanization pass.

## Create

Push if needed, then create the PR against the base branch, passing the humanized description file with `--body-file` rather than reproducing it in shell arguments:

```bash
gh pr create --title "<title>" --body-file "<humanized-description-path>" --base "<base>"
```

Check that the created PR's body is the description and not empty or a receipt, then return the PR URL.

## Success criteria

- The why is sourced from the conversation, and from past sessions, Linear, the PRD, or domain docs when the conversation was thin
- The description leads with motivation, links tickets inline, groups changes by logical area, states risk from the diff, and ends with a test plan
- The description was drafted first, humanized once, and used as humanized apart from targeted factual fixes
- The PR exists with the humanized body and its URL is returned
