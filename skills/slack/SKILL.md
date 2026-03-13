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
Conversational interface to Slack for messaging and search. Execute immediately when intent is clear — no unnecessary questions.

**Do NOT explore the codebase** unless the user explicitly asks. Work from user's description only.
</objective>

<cli_reference>
**CLI script:** `skills/slack/scripts/slack.py`

Run with: `uv run skills/slack/scripts/slack.py <command> [options]`

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
</step>

<step name="direct_commands">
**For direct commands (search, history, read-thread, channels, users, delete, react, edit, status, schedule):**

Execute CLI and format output.

```bash
uv run skills/slack/scripts/slack.py [command] [args]
```

Parse JSON response and present result:
- Success: Format messages readably — show user, text, timestamp, and permalink where available
- For `channels`/`users`: List with IDs for reference
- For `history`: Show messages in chronological order with thread indicators
- Error: Show error message and suggestions
</step>

<step name="send_flow">
**For sending and scheduling messages:**

1. **Resolve target** from user's description — the CLI handles channel/user resolution automatically
2. **Execute:**
   - **Immediate send:**
     ```bash
     uv run skills/slack/scripts/slack.py send "<target>" "<message>" [--thread <ts>]
     ```
   - **Scheduled send:**
     ```bash
     uv run skills/slack/scripts/slack.py schedule "<target>" "<message>" --at "<time>"
     ```
3. **Confirm delivery:** Show channel/DM and timestamp from response

When the user says "message Roland about X" or "tell Ejaz Y", extract the person's name as the target and the rest as the message. Do not ask for confirmation — send immediately.
</step>

<step name="error_handling">
**Handle errors gracefully:**

- **MISSING_TOKEN:** Read `skills/slack/references/setup-guide.md` and guide user through setup
- **AUTH_FAILED:** Token is invalid or revoked — regenerate from Slack app settings
- **CHANNEL_NOT_FOUND:** Suggest using `channels --search` to find the right name
- **USER_NOT_FOUND:** Suggest using `users --search` to find the right person
- **PERMISSION_DENIED:** Token missing required scope — list needed scopes and suggest reinstalling the app
- **RATE_LIMITED:** Wait and retry after the indicated period

Always parse JSON error response and present human-friendly message with suggestions.
</step>

</process>

<success_criteria>
- [ ] Commands execute immediately when intent is clear — no unnecessary questions
- [ ] Search results include permalink for easy navigation
- [ ] History output shows user names (not raw IDs) and thread indicators
- [ ] CLI output parsed and formatted — show user names, text, timestamps, and permalinks
- [ ] Target resolution handles channels (#name), channel IDs, and person names
- [ ] Errors handled with helpful setup instructions
</success_criteria>
