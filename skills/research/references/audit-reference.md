# Research Audit & Logging Reference

Debugging and cost analysis for the research skill. This reference is for periodic auditing — not needed during normal research runs.

---

### `audit` — Analyze API usage and costs

Reads JSONL logs from `~/.cache/research/logs/` and produces a usage summary. Logs are written automatically by every CLI call and directly by Pi's `web_search` / `web_fetch` tools.

| Flag | Default | Purpose |
|------|---------|---------|
| `--days` / `-d` | `7` | Number of days to analyze |
| `--session` / `-s` | none | Filter by session ID |
| `--detail` | false | Include individual call records in output |

**Output fields:**
- `summary`: `total_calls`, `unique_sessions`, `cache_hits`, `cache_hit_rate`, `failures`, `total_cost_usd`, `total_credits`, `total_duration_ms`
- `by_tool`: per-tool breakdown with `count`, `pct`, `cost_usd`, `credits`, `cache_hits`, `failures`
- `by_backend`: per-backend breakdown (`builtin`, `perplexity`, `context7`, `firecrawl`, `yt-dlp`) with `count`, `pct`, `cost_usd`, `credits`
- `by_type`: `builtin` (`web_search` / `web_fetch`) vs `cli` (research.py commands)
- `sessions`: per-session summary with `calls`, `cost_usd`, `credits`, `tools_used`
- `calls` (only with `--detail`): full list of individual log entries

**Example:**
```bash
uv run ~/.pi/agent/skills/research/scripts/research.py audit --days 30
uv run ~/.pi/agent/skills/research/scripts/research.py audit --detail
```

---

## Log format

All CLI commands and Pi `web_search` / `web_fetch` calls are logged to `~/.cache/research/logs/YYYY-MM-DD.jsonl`. Each line is a JSON object with:

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 UTC |
| `session_id` | Pi session ID for `web_search` / `web_fetch`; CLI calls use `CLAUDE_SESSION_ID` when present |
| `type` | `cli` (research.py command) or `builtin` (`web_search` / `web_fetch`) |
| `tool` | Tool name: `ask`, `search`, `reason`, `docs`, `map`, `scrape`, `youtube`, `web_search`, `web_fetch` |
| `query` | The query string or URL |
| `backend` | `perplexity`, `context7`, `firecrawl`, or `builtin` |
| `model` | Perplexity model name (if applicable) |
| `cache_hit` | Whether the result was served from cache |
| `success` | Whether the call succeeded |
| `url` | Request URL (builtin WebFetch only) |
| `error` | Truncated error message, max 200 chars (builtin only, when `success` is false) |
| `response_length` | Length of successful response body (builtin only, when `success` is true) |
| `duration_ms` | API call duration in milliseconds |
| `usage` | Token usage from Perplexity (prompt_tokens, completion_tokens) |
| `cost_usd` | Estimated cost (0 for free/cached calls) |
| `credits` | Firecrawl credits consumed |

Logs are retained for 30 days and automatically cleaned up on the first write of each new day.

---

## How logging works

| Source | Mechanism | Captures |
|--------|-----------|----------|
| CLI calls (`ask`, `search`, `reason`, `docs`, `map`, `scrape`) | `research.py` logs after each call | Timing, cost, token usage, cache hits, errors |
| YouTube search (`youtube`) | `youtube.py` logs after each call | Timing, videos searched/fetched/preprocessed |
| `web_search` / `web_fetch` (main agent, QUICK mode) | Direct logging in `~/.pi/agent/extensions/codex-search.ts` | Query/URL, Pi session ID, cache hits, duration, source |
| `web_search` / `web_fetch` (subagents, STANDARD/DEEP) | Same direct logging; subagents load the web tools extension | Query/URL, Pi session ID, cache hits, duration, source |

Web-tool audit logging is best-effort and must never break tool execution.
