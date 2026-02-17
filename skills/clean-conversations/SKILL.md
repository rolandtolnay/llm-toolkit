---
name: clean-conversations
description: >
  Remove empty Claude Code conversations (no real interaction) across all projects.
  Use when cleaning up wasteful sessions that were opened then immediately closed.
---

<objective>
Scan all Claude Code project directories for empty sessions (no real user interaction). Show a dry-run summary, confirm, then delete.
</objective>

<process>

## Step 1: Scan all projects

Run the scan script to classify every session across all projects:

```bash
python3 ~/.claude/skills/clean-conversations/scripts/scan.py
```

Capture the JSON output for use in subsequent steps.

## Step 2: Present dry-run summary

Parse the JSON output and display a markdown table:

| Project | Wasteful | Total | % |
|---------|----------|-------|---|

Below the table, explain what will be removed:
- JSONL session files
- Companion directories (same UUID, without `.jsonl` extension)
- Matching entries in each project's `sessions-index.json`

If zero wasteful sessions found, report that and stop.

## Step 3: Confirm with user

Use AskUserQuestion with options:
- **Delete all** — remove all wasteful sessions across all projects
- **Preview files** — list specific file paths before deciding
- **Cancel** — abort without changes

If user selects "Preview files", show the paths grouped by project, then ask again with "Delete all" / "Cancel".

## Step 4: Execute deletion

Read `~/.claude/skills/clean-conversations/scripts/delete.py`, replace `$REPORT_JSON` with the exact JSON string captured from Step 1 output (escape inner quotes if needed), then execute it via `python3 << 'PYEOF' ... PYEOF`.

Report final counts: sessions deleted, errors encountered. If errors exist, list them.

</process>

<success_criteria>
- No false positives — sessions with assistant responses or real user content are preserved
- Dry-run summary shown before any deletion
- User explicitly confirmed before files are removed
- Final count reported
</success_criteria>
