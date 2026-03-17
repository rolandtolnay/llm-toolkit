---
name: create-hook
description: Create and configure Claude Code hooks for event-driven automation. Use when adding PreToolUse, PostToolUse, Stop, Notification, or other lifecycle hooks to settings.json. Covers all hook events, Python/UV scripts, matchers, and decision control.
---

<objective>
Create Claude Code hooks that automate workflows, validate actions, inject context, or send notifications. Hooks are shell commands, HTTP endpoints, LLM prompts, or agent verifiers that execute at specific points in Claude Code's lifecycle.

Prefer Python scripts run with `uv run` — they start fast, handle JSON natively, and need no virtual environment.
</objective>

<process>

## Step 1: Understand the automation goal

Ask what the user wants to automate. Common categories:

- **Validation/blocking** — prevent dangerous commands, enforce conventions
- **Notification** — alert when Claude needs input or finishes
- **Context injection** — load project/sprint info at session start
- **Post-processing** — format code, run linters after edits
- **Quality gates** — verify tests pass before stopping
- **Logging/audit** — track tool usage, file changes
- **Permission automation** — auto-approve safe commands

If unclear, use AskUserQuestion:
- header: "What should this hook do?"
- question: "What automation do you want to add?"
- options:
  - "Block dangerous actions" — validate before tool execution
  - "Notify me" — desktop/sound alert when Claude needs input
  - "Add context" — inject info at session start
  - "Post-process changes" — format/lint after edits
  - "Quality gate" — check conditions before Claude stops
  - "Auto-approve commands" — skip permission prompts for safe patterns
  - "Let me describe it" — I'll explain

## Step 2: Select hook event(s)

Read `references/hook-events.md` for the complete event catalog with I/O schemas.

Match the user's goal to the right event. Quick reference:

| Goal | Event | Blocks? |
|------|-------|---------|
| Validate before tool runs | `PreToolUse` | Yes |
| React after tool succeeds | `PostToolUse` | No |
| React after tool fails | `PostToolUseFailure` | No |
| Auto-approve/deny permissions | `PermissionRequest` | Yes |
| Validate user prompts | `UserPromptSubmit` | Yes |
| Quality gate before stopping | `Stop` | Yes |
| Quality gate for subagents | `SubagentStop` | Yes |
| Inject context at startup | `SessionStart` | No |
| Cleanup on exit | `SessionEnd` | No |
| Desktop/sound notifications | `Notification` | No |
| Inject context into subagents | `SubagentStart` | No |
| Gate task completion | `TaskCompleted` | Yes |
| Audit config changes | `ConfigChange` | Yes |
| Save state before compaction | `PreCompact` | No |

Present the recommended event with reasoning. If the user's goal spans multiple events, configure each one.

## Step 3: Choose handler type

| Type | Speed | Cost | Use when |
|------|-------|------|----------|
| `command` | Fast (<100ms) | Free | Most hooks — validation, logging, formatting, notifications |
| `http` | Medium | Free | External services, webhooks, remote validation |
| `prompt` | Slow (1-3s) | API credits | Natural language validation, semantic analysis |
| `agent` | Slowest (10-60s) | API credits | Multi-step verification needing file/code access |

**Default to `command` with a Python/UV script.** Only use `prompt`/`agent` when the decision requires natural language reasoning. Only use `http` when calling external services.

Not all events support all types. Events supporting all four: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `Stop`, `SubagentStop`, `TaskCompleted`, `UserPromptSubmit`. All other events: `command` only.

## Step 4: Determine scope

Hooks live in **settings files** (not standalone hooks.json):

| Location | Scope | Shareable |
|----------|-------|-----------|
| `~/.claude/settings.json` | All projects | No |
| `.claude/settings.json` | This project | Yes (commit to repo) |
| `.claude/settings.local.json` | This project | No (gitignored) |

Default to project scope (`.claude/settings.json`) unless the hook is clearly universal (like notifications → user settings).

## Step 5: Write the hook script

Read `references/python-hook-patterns.md` for templates and working examples.

### Python/UV script structure

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""What this hook does."""
import json
import sys


def main():
    data = json.load(sys.stdin)

    # Hook logic here

    # Allow: exit 0 silently
    sys.exit(0)

    # Block via exit code (all blocking events):
    # print("Reason to block", file=sys.stderr)
    # sys.exit(2)

    # Block via JSON (event-specific):
    # json.dump({"decision": "block", "reason": "..."}, sys.stdout)


if __name__ == "__main__":
    main()
```

Save to `.claude/hooks/` (project) or `~/.claude/hooks/` (user). Make executable: `chmod +x`.

### Decision control by event type

How to output decisions differs per event — getting this wrong silently fails:

**PreToolUse** — uses `hookSpecificOutput` (NOT top-level `decision`):
```python
json.dump({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",  # "allow", "deny", or "ask"
        "permissionDecisionReason": "Explanation"
    }
}, sys.stdout)
```

**PermissionRequest** — uses `hookSpecificOutput.decision`:
```python
json.dump({
    "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {"behavior": "allow"}  # or "deny"
    }
}, sys.stdout)
```

**Stop, SubagentStop, UserPromptSubmit, PostToolUse, ConfigChange** — top-level:
```python
json.dump({"decision": "block", "reason": "Explanation"}, sys.stdout)
```

**SessionStart** — returns context:
```python
json.dump({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "Context string here"
    }
}, sys.stdout)
```

**TaskCompleted, TeammateIdle** — exit code 2 only (no JSON decision):
```python
print("Reason to block", file=sys.stderr)
sys.exit(2)
```

**Elicitation, ElicitationResult** — uses `hookSpecificOutput.action`:
```python
json.dump({
    "hookSpecificOutput": {
        "hookEventName": "Elicitation",
        "action": "accept",  # "accept", "decline", or "cancel"
        "content": {"field": "value"}
    }
}, sys.stdout)
```

**Prompt/agent hooks** — LLM responds with:
```json
{"ok": true}
{"ok": false, "reason": "what's wrong"}
```

### Matchers

Matchers are regex patterns filtering which tools/sources trigger the hook:

```json
"matcher": "Bash"              // Exact tool match
"matcher": "Write|Edit"        // Multiple tools (regex OR)
"matcher": "mcp__.*"           // All MCP tools
"matcher": "mcp__memory__.*"   // Specific MCP server
"matcher": "^Write$"           // Exact match only (won't match TodoWrite)
```

Omit `matcher` or use `"*"` to match all occurrences. Some events don't support matchers (`UserPromptSubmit`, `Stop`, `TaskCompleted`, `TeammateIdle`, `WorktreeCreate/Remove`, `InstructionsLoaded`) — they always fire on every occurrence.

Matchers are **case-sensitive** and use JavaScript regex syntax. `"bash"` won't match `"Bash"`.

## Step 6: Configure settings file

Read the existing settings file first to merge with any existing hooks.

Configuration structure:
```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "uv run \"$CLAUDE_PROJECT_DIR/.claude/hooks/my-hook.py\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

Handler fields:
- `type`: `"command"`, `"http"`, `"prompt"`, or `"agent"` (required)
- `command`: shell command (command hooks)
- `url`: endpoint URL (http hooks)
- `prompt`: prompt text with `$ARGUMENTS` placeholder (prompt/agent hooks)
- `timeout`: seconds before canceling (defaults: 600 command, 30 prompt, 60 agent)
- `async`: `true` to run in background without blocking (command hooks only)
- `statusMessage`: custom spinner text while hook runs
- `model`: model for prompt/agent hooks (defaults to a fast model)

For prompt/agent hooks:
```json
{
  "type": "prompt",
  "prompt": "Evaluate if this is safe: $ARGUMENTS. Respond with JSON: {\"ok\": true} or {\"ok\": false, \"reason\": \"why\"}"
}
```

## Step 7: Test and verify

1. **Validate JSON syntax:**
   ```bash
   python -m json.tool .claude/settings.json
   ```

2. **Test script standalone:**
   ```bash
   echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"echo hi"},"session_id":"test","cwd":".","permission_mode":"default"}' | uv run .claude/hooks/my-hook.py
   echo $?  # 0 = allow, 2 = block
   ```

3. **Test in Claude Code:**
   ```bash
   claude --debug
   ```
   Trigger the hook event and check debug output for:
   ```
   [DEBUG] Executing hooks for EventName:ToolName
   [DEBUG] Hook command completed with status 0: ...
   ```

4. **Toggle verbose mode** with `Ctrl+O` to see hook output in the transcript.

</process>

<safety>

### Stop hook infinite loop prevention

Stop and SubagentStop hooks MUST check `stop_hook_active`:
```python
if data.get("stop_hook_active"):
    sys.exit(0)  # Don't block again — prevents infinite loop
```

### General safety rules

- Always quote `$CLAUDE_PROJECT_DIR` in shell: `"$CLAUDE_PROJECT_DIR"`
- Use absolute paths for hook scripts
- Set timeouts for hooks calling external tools
- Default to allow — only block on explicit match
- SessionEnd hooks have a 1.5s timeout cap by default
- Hooks run with your full user permissions — review scripts before adding

</safety>

<reference_index>

Supporting files in `references/`:

- `hook-events.md` — Complete event catalog with input schemas, matcher values, and decision control patterns per event. Read when selecting events or configuring decision output.
- `python-hook-patterns.md` — Python/UV script templates and working examples for common patterns (blocking, formatting, notifications, logging, permission automation). Read when writing hook scripts.

</reference_index>

<success_criteria>

- [ ] Decision control uses the correct pattern for the event type (PreToolUse uses hookSpecificOutput, Stop uses top-level decision, etc.)
- [ ] Stop/SubagentStop hooks check `stop_hook_active` to prevent infinite loops
- [ ] Hook script tested standalone with sample JSON input before configuring
- [ ] Matcher pattern targets the right tools — not overly broad
- [ ] Tested with `claude --debug` showing expected behavior
- [ ] Script is executable (`chmod +x`) and runs with `uv run`
- [ ] Settings file valid JSON with correct event for the use case

</success_criteria>
