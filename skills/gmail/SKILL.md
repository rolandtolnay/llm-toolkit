---
name: gmail
description: >
  Read-only Gmail source-material retrieval for agents. Use when you need to
  find relevant newsletters, reports, receipts, or topic-related emails without
  dumping the mailbox into context.
---

<objective>
Read-only Gmail source-material retrieval through the **Gmail Read CLI**.

Use this skill to find and read a narrow set of relevant Gmail messages as source material for research, summarization, or evidence gathering. Do not use it as a mailbox dump tool.
</objective>

<cli_cheatsheet>
Script path: `~/.claude/skills/gmail/scripts/gmail.py`

Run with: `uv run <script> <command> [options]`

```
uv run <script> search [--from X] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--subject TEXT] [--text TEXT] [--query RAW] [--label LABEL] [--mailbox all|inbox] [--limit N] [--snippet-chars N] [--include-sent] [--include-spam-trash] [--load-shell-env]
uv run <script> get <message-id> [--max-chars N] [--load-shell-env]
uv run <script> thread <thread-id> [--max-messages N] [--max-chars-per-message N] [--load-shell-env]
uv run <script> labels [--load-shell-env]
uv run <script> config [--load-shell-env]
uv run <script> doctor [--load-shell-env]
```

Defaults: search uses All Mail, received mail only, excludes spam/trash, returns bounded snippets rather than full bodies, and applies conservative result limits.
</cli_cheatsheet>

<configuration>
Required credentials:

- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`

Provide these variables through the agent environment, process environment, or the CLI's supported credential files.

Run `config` to see which credential sources loaded and whether required variables are present. Secret values are never printed. If credentials are exported only from shell startup files, use `--load-shell-env`.

Run `doctor` to verify read-only IMAP connectivity without returning email content.
</configuration>

<guardrails>
Before running broad mailbox searches, narrow the request by at least one of:

- Sender or domain (`--from`)
- Topic/body text (`--text`) or subject (`--subject`)
- Label (`--label`)
- Timeframe (`--after`, `--before`)
- Raw Gmail query (`--query`)

Do not use this as a mailbox dump tool. Search first, inspect metadata/snippets, then fetch only selected messages or threads with `get` or `thread`.
</guardrails>

<privacy_rules>
- Read-only v1: no sending, replying, deleting, archiving, labeling, or mark-read/unread operations.
- Search returns metadata and snippets by default, not full bodies.
- `get` and `thread` return normalized plain text with explicit truncation metadata.
- Attachment handling is metadata-only: filename, content type, and approximate size when available. Attachment contents are not downloaded, written, or parsed.
- The CLI does not cache or log email bodies, snippets, subjects, senders, or results.
- Do not run live Gmail tests in normal development workflows; use `doctor` manually when credentials are available.
</privacy_rules>

<examples>
Newsletter research from a domain:

```bash
uv run ~/.claude/skills/gmail/scripts/gmail.py search --from example.com --after 2026-01-01 --text "pricing" --limit 5
```

Find recent finance reports without reading bodies yet:

```bash
uv run ~/.claude/skills/gmail/scripts/gmail.py search --label Finance --subject "monthly report" --after 2026-01-01
```

Read one selected message from search results:

```bash
uv run ~/.claude/skills/gmail/scripts/gmail.py get <message-id> --max-chars 8000
```

Read a selected conversation with sent replies included and direction markers:

```bash
uv run ~/.claude/skills/gmail/scripts/gmail.py thread <thread-id> --max-messages 10 --max-chars-per-message 6000
```
</examples>
