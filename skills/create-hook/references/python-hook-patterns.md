# Python Hook Patterns

Templates and working examples for Python hooks run with `uv run`.

## Base Template

Every Python hook follows this structure:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Brief description of what this hook does."""
import json
import sys


def main():
    data = json.load(sys.stdin)

    # Your hook logic here

    # Option 1: Allow (exit 0, no output)
    sys.exit(0)

    # Option 2: Block via exit code (works for all blocking events)
    # print("Reason to block", file=sys.stderr)
    # sys.exit(2)

    # Option 3: Block via JSON (event-specific, see below)
    # json.dump({"decision": "block", "reason": "..."}, sys.stdout)


if __name__ == "__main__":
    main()
```

Save as `.claude/hooks/hook-name.py`, then `chmod +x`.

Reference in settings.json:
```json
{
  "type": "command",
  "command": "uv run \"$CLAUDE_PROJECT_DIR/.claude/hooks/hook-name.py\""
}
```

For user-scoped hooks, save to `~/.claude/hooks/` and reference with absolute path.

---

## PreToolUse: Block Dangerous Commands

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Block destructive shell commands before execution."""
import json
import sys

BLOCKED_PATTERNS = [
    "rm -rf /",
    "mkfs",
    "> /dev/sd",
]

FORCE_PUSH_BRANCHES = ["main", "master"]


def main():
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "")

    if tool_name != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")

    # Check destructive patterns
    for pattern in BLOCKED_PATTERNS:
        if pattern in command:
            json.dump({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked: contains '{pattern}'"
                }
            }, sys.stdout)
            return

    # Check force push to protected branches
    if "git push" in command and "--force" in command:
        for branch in FORCE_PUSH_BRANCHES:
            if branch in command:
                json.dump({
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f"Force push to {branch} blocked"
                    }
                }, sys.stdout)
                return

    sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## PostToolUse: Auto-Format After Edits

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run formatter after file writes/edits."""
import json
import os
import subprocess
import sys

FORMATTERS = {
    ".py": ["black", "{file}"],
    ".js": ["prettier", "--write", "{file}"],
    ".ts": ["prettier", "--write", "{file}"],
    ".tsx": ["prettier", "--write", "{file}"],
    ".jsx": ["prettier", "--write", "{file}"],
    ".go": ["gofmt", "-w", "{file}"],
    ".swift": ["swift-format", "--in-place", "{file}"],
    ".dart": ["dart", "format", "{file}"],
}


def main():
    data = json.load(sys.stdin)
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    _, ext = os.path.splitext(file_path)
    formatter = FORMATTERS.get(ext)
    if not formatter:
        sys.exit(0)

    cmd = [arg.replace("{file}", file_path) for arg in formatter]
    try:
        subprocess.run(cmd, capture_output=True, timeout=10)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Formatter not installed or slow — don't block

    sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## Stop: Quality Gate

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Verify tests pass before Claude stops."""
import json
import subprocess
import sys


def main():
    data = json.load(sys.stdin)

    # CRITICAL: prevent infinite loop
    if data.get("stop_hook_active"):
        sys.exit(0)

    # Run tests
    result = subprocess.run(
        ["npm", "test"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=data.get("cwd", "."),
    )

    if result.returncode != 0:
        json.dump({
            "decision": "block",
            "reason": f"Tests failing. Fix before stopping.\n{result.stdout[-500:]}"
        }, sys.stdout)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## SessionStart: Inject Context

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Load project context at session start."""
import json
import os
import subprocess
import sys


def main():
    data = json.load(sys.stdin)
    cwd = data.get("cwd", ".")

    context_parts = []

    # Git branch
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=cwd
        ).stdout.strip()
        if branch:
            context_parts.append(f"Current branch: {branch}")
    except FileNotFoundError:
        pass

    # Sprint context file
    sprint_file = os.path.join(cwd, ".sprint-context.txt")
    if os.path.exists(sprint_file):
        with open(sprint_file) as f:
            context_parts.append(f.read().strip())

    if context_parts:
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "\n".join(context_parts)
            }
        }, sys.stdout)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## Notification: Desktop Alert (macOS)

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Send macOS notification when Claude needs attention."""
import json
import subprocess
import sys


def main():
    data = json.load(sys.stdin)
    message = data.get("message", "Claude needs your attention")
    title = data.get("title", "Claude Code")

    subprocess.run([
        "osascript", "-e",
        f'display notification "{message}" with title "{title}" sound name "Glass"'
    ], capture_output=True)

    sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## PreToolUse: Modify Tool Input

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Add --save-exact flag to npm install commands."""
import json
import sys


def main():
    data = json.load(sys.stdin)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")

    if command.startswith("npm install") and "--save-exact" not in command:
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Added --save-exact flag",
                "updatedInput": {
                    "command": command + " --save-exact"
                }
            }
        }, sys.stdout)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## Logging: Audit Trail

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Log all tool usage to a JSONL audit file."""
import json
import os
import sys
from datetime import datetime, timezone


def main():
    data = json.load(sys.stdin)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": data.get("hook_event_name"),
        "tool": data.get("tool_name"),
        "session": data.get("session_id"),
    }

    # Add tool-specific fields
    tool_input = data.get("tool_input", {})
    if "command" in tool_input:
        log_entry["command"] = tool_input["command"]
    if "file_path" in tool_input:
        log_entry["file_path"] = tool_input["file_path"]

    log_path = os.path.expanduser("~/.claude/hook-audit.jsonl")
    with open(log_path, "a") as f:
        json.dump(log_entry, f)
        f.write("\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## PermissionRequest: Auto-Approve Patterns

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Auto-approve safe bash commands matching known patterns."""
import json
import re
import sys

SAFE_PATTERNS = [
    r"^npm (test|run|install)",
    r"^git (status|log|diff|branch|show)",
    r"^(ls|cat|head|tail|wc|echo|pwd)",
    r"^python -m pytest",
    r"^uv run",
]


def main():
    data = json.load(sys.stdin)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")

    for pattern in SAFE_PATTERNS:
        if re.match(pattern, command):
            json.dump({
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {
                        "behavior": "allow"
                    }
                }
            }, sys.stdout)
            return

    sys.exit(0)  # Don't override — show normal permission dialog


if __name__ == "__main__":
    main()
```

---

## Testing Hooks

Test any hook standalone before configuring it:

```bash
# Simulate PreToolUse for a Bash command
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf /"},"session_id":"test","cwd":".","permission_mode":"default"}' | uv run .claude/hooks/my-hook.py

# Simulate Stop event
echo '{"hook_event_name":"Stop","stop_hook_active":false,"session_id":"test","cwd":".","permission_mode":"default"}' | uv run .claude/hooks/my-hook.py

# Simulate Notification
echo '{"hook_event_name":"Notification","message":"Claude needs input","notification_type":"permission_prompt","session_id":"test","cwd":".","permission_mode":"default"}' | uv run .claude/hooks/my-hook.py

# Check exit code
echo $?
```

Expected: exit 0 = allow, exit 2 = block (stderr has reason), JSON on stdout = structured control.
