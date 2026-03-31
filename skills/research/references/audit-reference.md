# Research Audit & Logging Reference

Debugging and cost analysis for the research skill. This reference is for periodic auditing — not needed during normal research runs.

---

### `audit` — Analyze API usage and costs

Reads JSONL logs from `~/.cache/research/logs/` and produces a usage summary. Logs are written automatically by every CLI call and by PostToolUse hooks for WebSearch/WebFetch.

| Flag | Default | Purpose |
|------|---------|---------|
| `--days` / `-d` | `7` | Number of days to analyze |
| `--session` / `-s` | none | Filter by session ID |
| `--detail` | false | Include individual call records in output |

**Output fields:**
- `summary`: `total_calls`, `unique_sessions`, `cache_hits`, `cache_hit_rate`, `failures`, `total_cost_usd`, `total_credits`, `total_duration_ms`
- `by_tool`: per-tool breakdown with `count`, `pct`, `cost_usd`, `credits`, `cache_hits`, `failures`
- `by_backend`: per-backend breakdown (`builtin`, `perplexity`, `context7`, `firecrawl`) with `count`, `pct`, `cost_usd`, `credits`
- `by_type`: `builtin` (WebSearch/WebFetch via hooks) vs `cli` (research.py commands)
- `sessions`: per-session summary with `calls`, `cost_usd`, `credits`, `tools_used`
- `calls` (only with `--detail`): full list of individual log entries

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/research.py audit --days 30
uv run ~/.claude/skills/research/scripts/research.py audit --detail
```

---

## Log format

All CLI commands and WebSearch/WebFetch calls (via skill hooks) are logged to `~/.cache/research/logs/YYYY-MM-DD.jsonl`. Each line is a JSON object with:

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 UTC |
| `session_id` | Claude Code session ID (from hooks or `CLAUDE_SESSION_ID` env) |
| `type` | `cli` (research.py command) or `builtin` (WebSearch/WebFetch) |
| `tool` | Tool name: `ask`, `search`, `reason`, `docs`, `map`, `scrape`, `WebSearch`, `WebFetch` |
| `query` | The query string or URL |
| `backend` | `perplexity`, `context7`, `firecrawl`, or `builtin` |
| `model` | Perplexity model name (if applicable) |
| `cache_hit` | Whether the result was served from cache |
| `success` | Whether the call succeeded |
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
| WebSearch/WebFetch (main agent, QUICK mode) | PostToolUse hook in SKILL.md frontmatter | Query/URL, session ID |
| WebSearch/WebFetch (subagents, STANDARD/DEEP) | PostToolUse hook in research-subagent.md frontmatter | Query/URL, session ID |

Hook failures surface on stderr (visible in verbose mode via `Ctrl+O`).
