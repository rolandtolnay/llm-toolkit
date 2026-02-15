---
description: Commit, comment, attach commit, and mark a Linear ticket as done
argument-hint: "<ticket-id>"
---

<objective>
Finalize a completed Linear ticket: commit changes, post a solution summary comment, attach the commit, and mark the ticket as done.

Usage: `/finalize-ticket MIN-42`
</objective>

<context>
- Current git status: !`git status`
- Current branch: !`git branch --show-current`
</context>

<process>

1. **Load Linear skill.** Invoke the `linear` skill using the Skill tool.

2. **Commit changes.** Invoke `/commit-commands:commit` with `[$ARGUMENTS]` as the prefix in the commit message (e.g., `[MIN-42] ...`). If there are no uncommitted changes, skip this step and use the most recent commit.

3. **Comment on the ticket.** Run the Linear CLI `comment` command on `$ARGUMENTS` with a concise solution summary. Derive from the conversation context and commit message. Focus on decisions and approach — not a file-by-file inventory.

   ```bash
   uv run ~/.claude/skills/linear/scripts/linear.py comment $ARGUMENTS "<summary>"
   ```

4. **Attach the commit.** Run the Linear CLI `attach-commit` command to link the commit to the ticket. Use the commit SHA from step 2 (or HEAD if step 2 was skipped).

   ```bash
   uv run ~/.claude/skills/linear/scripts/linear.py attach-commit $ARGUMENTS <commit-sha>
   ```

5. **Mark as done.** Run the Linear CLI `state` command to transition the ticket to Done.

   ```bash
   uv run ~/.claude/skills/linear/scripts/linear.py state $ARGUMENTS Done
   ```

</process>

<success_criteria>
- [ ] Comment posted with meaningful solution summary (not a diff inventory)
- [ ] Commit includes `[$ARGUMENTS]` prefix in message
- [ ] Commit attached to ticket via `attach-commit`
- [ ] Ticket state set to Done
</success_criteria>
