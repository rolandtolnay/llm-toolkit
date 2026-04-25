#!/usr/bin/env uv run
"""Hook script to log WebSearch/WebFetch calls during research skill execution.

Called by PostToolUse hooks defined in SKILL.md and research-subagent.md frontmatter.
Reads Claude Code hook JSON from stdin and appends a JSONL entry
to ~/.cache/research/logs/YYYY-MM-DD.jsonl.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path.home() / ".cache" / "research" / "logs"
LOG_RETENTION_DAYS = 30


def _cleanup_old_logs() -> None:
    """Delete log files older than LOG_RETENTION_DAYS. Silent on failure."""
    try:
        today = datetime.now(timezone.utc).date()
        for f in LOG_DIR.iterdir():
            if not f.name.endswith(".jsonl"):
                continue
            try:
                file_date = datetime.strptime(f.stem, "%Y-%m-%d").date()
                if (today - file_date).days > LOG_RETENTION_DAYS:
                    f.unlink()
            except ValueError:
                continue
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        response = str(data.get("tool_response", ""))

        _ERROR_PATTERNS = ["timeout", "status code 4", "status code 5", "econnrefused", "enotfound"]
        is_error = any(p in response.lower() for p in _ERROR_PATTERNS)

        entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "session_id": data.get("session_id", ""),
            "type": "builtin",
            "tool": tool_name,
            "query": tool_input.get("query", tool_input.get("url", "")),
            "url": tool_input.get("url", ""),
            "backend": "builtin",
            "success": not is_error,
            "error": response[:200] if is_error else "",
            "response_length": len(response) if not is_error else 0,
            "cost_usd": 0.0,
            "credits": 0,
        }

        log_file = LOG_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
        if not log_file.exists():
            _cleanup_old_logs()
        with open(log_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        # Write to stderr so failures are visible in verbose mode (Ctrl+O)
        print(f"research log-hook error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
