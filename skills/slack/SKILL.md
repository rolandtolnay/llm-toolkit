---
name: slack
description: >
  Send messages, search conversations, read channel history, and manage
  status in Slack. Use when sending DMs, posting to channels, searching
  messages, reading threads, editing messages, setting status, or scheduling
  messages. Examples: "message Roland", "search for deployment", "set my
  status to deep work".
---

<objective>
Conversational interface to Slack for messaging and search. Read-only commands (search, history, channels, users) execute immediately. Outbound messages always require user confirmation before sending.

**Do NOT explore the codebase** unless the user explicitly asks. Work from user's description only.
</objective>

<cli_reference>
**CLI script:** `scripts/slack.py` (relative to this skill's install directory)

Resolve the script path before first use: check `~/.claude/skills/slack/scripts/slack.py`, then `.claude/skills/slack/scripts/slack.py`. Cache the result for the session.

Run with: `uv run <resolved-path>/scripts/slack.py <command> [options]`

**Commands:**
| Command | Usage | Purpose |
|---------|-------|---------|
| `send` | `send <target> <message> [--thread/-t ts]` | Send message (or thread reply) |
| `edit` | `edit <channel_id> <ts> <new_text>` | Edit a sent message (own only) |
| `search` | `search <query> [--count/-c N]` | Search messages (default 20) |
| `history` | `history <channel> [--count/-c N]` | Recent channel messages (default 20) |
| `read-thread` | `read-thread <channel> <thread_ts>` | Read thread replies |
| `channels` | `channels [--search/-s name]` | List/search channels |
| `users` | `users [--search/-s name]` | List/search workspace members |
| `delete` | `delete <channel_id> <ts>` | Delete a message |
| `react` | `react <channel_id> <ts> <emoji>` | Add reaction to a message |
| `status` | `status [text] [--emoji/-e name] [--expires/-x duration]` | Set/clear Slack status |
| `schedule` | `schedule <target> <message> --at <time>` | Schedule message for later |

**Target resolution (for `send`):**
- Channel ID (starts with `C`, `G`, or `D`) → use directly
- `#channel-name` → finds channel by name
- Person's name (e.g. `Roland`) → finds user, opens DM, sends there

**Search query modifiers:** Slack search syntax works — `from:me`, `in:#channel`, `before:2026-03-01`, `after:2026-02-01`, `has:link`, etc.

**Status duration format:** `2h`, `30m`, `1h30m` — auto-clears after the specified time.

**Schedule time format:** `--at "in 2h"`, `--at "in 30m"`, `--at "in 1h30m"`, or a Unix timestamp.
</cli_reference>

<process>

<step name="parse_intent">
**Parse the command to determine intent:**

| Pattern | Intent | Action |
|---------|--------|--------|
| `send <target> <message>` | Send message | Go to send_flow |
| `reply to thread`, `respond in thread` | Thread reply | Use `send` with `--thread` |
| `edit message`, `fix that message`, `update what I sent` | Edit message | Execute `edit` with channel, ts, new text |
| `search <query>`, `find messages about` | Search | Execute `search` directly |
| `history <channel>`, `read #channel`, `what's happening in #channel` | Channel history | Execute `history` directly |
| `read thread`, `show thread replies` | Read thread | Execute `read-thread` directly |
| `channels`, `list channels`, `find channel` | List channels | Execute `channels` directly |
| `users`, `who's in the workspace`, `find user` | List users | Execute `users` directly |
| `delete message` | Delete | Execute `delete` directly |
| `react`, `add reaction`, `add emoji` | React | Execute `react` directly |
| `set status`, `set my status to`, `I'm doing` | Set status | Execute `status` with text, emoji, optional expiry |
| `clear status`, `remove status` | Clear status | Execute `status` with empty text |
| `schedule message`, `send later`, `send tomorrow` | Schedule | Go to send_flow but use `schedule` with `--at` |
| `message <name> <text>`, `DM <name>`, `tell <name>` | Send DM | Go to send_flow with person target |
| `post in #channel <text>` | Send to channel | Go to send_flow with channel target |
| `post about the PR`, `share the PR`, `announce the PR` | PR announcement | Go to pr_announcement_flow |
</step>

<step name="direct_commands">
**For direct commands (search, history, read-thread, channels, users, delete, react, edit, status, schedule):**

Execute CLI and format output.

```bash
uv run <slack.py> [command] [args]
```

Parse JSON response and present result:
- Success: Format messages readably — show user, text, timestamp, and permalink where available
- For `channels`/`users`: List with IDs for reference
- For `history`: Show messages in chronological order with thread indicators
- Error: Show error message and suggestions
</step>

<step name="send_flow">
**For sending and scheduling messages:**

**CRITICAL: Every outbound message MUST be confirmed by the user before sending.**

1. **Resolve target** from user's description — the CLI handles channel/user resolution automatically
2. **Draft the message** and present it to the user using `AskUserQuestion` with options to confirm or request changes.
3. **Only after the user confirms**, execute:
   - **Immediate send:**
     ```bash
     uv run <slack.py> send "<target>" "<message>" [--thread <ts>]
     ```
   - **Scheduled send:**
     ```bash
     uv run <slack.py> schedule "<target>" "<message>" --at "<time>"
     ```
4. **Confirm delivery:** Show channel/DM and timestamp from response

When the user says "message Roland about X" or "tell Ejaz Y", extract the person's name as the target and the rest as the message content.
</step>

<step name="pr_announcement_flow">
**For PR announcements (e.g. "post about the PR", "share PR in #engineering-pr"):**

Triggered when the user asks to post/share/announce a PR to a channel. Gather the PR details automatically, compose the message using the template below, then follow the normal send_flow (draft → confirm → send).

1. **Gather PR info** — run `gh pr view --json number,title,url,body` to get the current branch's PR. If the user specifies a PR number, use `gh pr view <number>` instead.
2. **Compose the message** using this format:
   ```
   PR #<number>: <title>
   <url>
   <one-liner context>
   ```
   The `<one-liner context>` is a single sentence explaining *why this matters* — what it enables or unblocks, not just what files changed. Derive from the PR body/summary. Focus on impact for the team (e.g. "Enables end-to-end local testing of payments and subscriptions" rather than "Updates local-seed.sh").
3. **Present the draft** to the user for confirmation, then follow the normal send_flow to post it.
</step>

<step name="error_handling">
**Handle errors gracefully:**

- **MISSING_TOKEN:** Read the `references/setup-guide.md` file next to this skill and guide user through setup
- **AUTH_FAILED:** Token is invalid or revoked — regenerate from Slack app settings
- **CHANNEL_NOT_FOUND:** Suggest using `channels --search` to find the right name
- **USER_NOT_FOUND:** Suggest using `users --search` to find the right person
- **PERMISSION_DENIED:** Token missing required scope — list needed scopes and suggest reinstalling the app
- **RATE_LIMITED:** Wait and retry after the indicated period

Always parse JSON error response and present human-friendly message with suggestions.
</step>

</process>

<success_criteria>
- [ ] Outbound messages (send, schedule, DM) are ALWAYS shown to the user and confirmed before posting
- [ ] Read-only commands (search, history, channels, users, read-thread) execute immediately
- [ ] Errors handled with helpful setup instructions
- [ ] Search results include permalink for easy navigation
- [ ] History output shows user names (not raw IDs) and thread indicators
- [ ] CLI output parsed and formatted — show user names, text, timestamps, and permalinks
- [ ] Target resolution handles channels (#name), channel IDs, and person names
</success_criteria>
