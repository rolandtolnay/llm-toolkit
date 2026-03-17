# Hook Events Reference

Complete catalog of Claude Code hook events with input schemas, matcher values, and decision control.

## Event Summary

| Event | Fires when | Blocks? | Matcher filters | Handler types |
|-------|-----------|---------|-----------------|---------------|
| `SessionStart` | Session begins/resumes | No | `startup`, `resume`, `clear`, `compact` | command only |
| `InstructionsLoaded` | CLAUDE.md or rules file loaded | No | none (always fires) | command only |
| `UserPromptSubmit` | User submits prompt | Yes | none (always fires) | all four |
| `PreToolUse` | Before tool executes | Yes | tool name (`Bash`, `Edit\|Write`, `mcp__.*`) | all four |
| `PermissionRequest` | Permission dialog shown | Yes | tool name | all four |
| `PostToolUse` | After tool succeeds | No | tool name | all four |
| `PostToolUseFailure` | After tool fails | No | tool name | all four |
| `Notification` | Claude sends notification | No | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` | command only |
| `SubagentStart` | Subagent spawned | No | agent type (`Bash`, `Explore`, custom names) | command only |
| `SubagentStop` | Subagent finishes | Yes | agent type | all four |
| `Stop` | Claude finishes responding | Yes | none (always fires) | all four |
| `TeammateIdle` | Agent team member going idle | Yes | none (always fires) | command only |
| `TaskCompleted` | Task marked completed | Yes | none (always fires) | all four |
| `ConfigChange` | Config file changes | Yes | `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills` | command only |
| `WorktreeCreate` | Worktree being created | Yes | none | command only |
| `WorktreeRemove` | Worktree being removed | No | none | command only |
| `PreCompact` | Before compaction | No | `manual`, `auto` | command only |
| `PostCompact` | After compaction | No | `manual`, `auto` | command only |
| `Elicitation` | MCP server requests input | Yes | MCP server name | command only |
| `ElicitationResult` | User responds to elicitation | Yes | MCP server name | command only |
| `SessionEnd` | Session terminates | No | `clear`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` | command only |

**Handler types:** "all four" = `command`, `http`, `prompt`, `agent`. Events marked "command only" do not support prompt, agent, or http hooks.

---

## Common Input Fields

All events receive these fields via stdin as JSON:

| Field | Description |
|-------|-------------|
| `session_id` | Current session identifier |
| `transcript_path` | Path to conversation JSONL |
| `cwd` | Current working directory |
| `permission_mode` | `"default"`, `"plan"`, `"acceptEdits"`, `"dontAsk"`, or `"bypassPermissions"` |
| `hook_event_name` | Name of the event that fired |

---

## Event Details

### SessionStart

**Extra input:** `source` (`"startup"`, `"resume"`, `"clear"`, `"compact"`), `model`, optional `agent_type`

**Decision control:** stdout text or `additionalContext` is added to Claude's context:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Sprint 23. Focus: auth refactor."
  }
}
```

**Special:** `CLAUDE_ENV_FILE` env var available — write `export VAR=value` lines to persist env vars for all subsequent Bash commands in the session.

---

### UserPromptSubmit

**Extra input:** `prompt` (the text the user submitted)

**Decision control:** top-level `decision`:
```json
{ "decision": "block", "reason": "Please include a ticket number" }
```

stdout text (non-JSON) or `additionalContext` is added as context.

---

### PreToolUse

**Extra input:** `tool_name`, `tool_input` (fields depend on tool), `tool_use_id`

**Tool input fields by tool:**
- **Bash:** `command`, `description`, `timeout`, `run_in_background`
- **Write:** `file_path`, `content`
- **Edit:** `file_path`, `old_string`, `new_string`, `replace_all`
- **Read:** `file_path`, `offset`, `limit`
- **Glob:** `pattern`, `path`
- **Grep:** `pattern`, `path`, `glob`, `output_mode`, `-i`, `multiline`
- **Task:** `prompt`, `description`, `subagent_type`, `model`
- **MCP tools:** tool-specific parameters

**Decision control:** uses `hookSpecificOutput` (NOT top-level `decision`):
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive command blocked",
    "updatedInput": { "command": "modified command" },
    "additionalContext": "Extra context for Claude"
  }
}
```

`permissionDecision` values: `"allow"` (bypass permission), `"deny"` (block), `"ask"` (prompt user)

---

### PermissionRequest

**Extra input:** `tool_name`, `tool_input`, `permission_suggestions`

**Decision control:** uses `hookSpecificOutput.decision`:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": { "command": "npm run lint" },
      "updatedPermissions": [{ "type": "toolAlwaysAllow", "tool": "Bash" }]
    }
  }
}
```

For deny: `"behavior": "deny"`, optional `"message"` and `"interrupt": true`.

---

### PostToolUse

**Extra input:** `tool_name`, `tool_input`, `tool_response`, `tool_use_id`

**Decision control:** top-level:
```json
{
  "decision": "block",
  "reason": "Linting errors found",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Fix these issues: ...",
    "updatedMCPToolOutput": "replaced output (MCP tools only)"
  }
}
```

---

### PostToolUseFailure

**Extra input:** `tool_name`, `tool_input`, `tool_use_id`, `error`, `is_interrupt`

**Decision control:** `additionalContext` only:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUseFailure",
    "additionalContext": "This failure is expected during setup, proceed"
  }
}
```

---

### Stop / SubagentStop

**Extra input:** `stop_hook_active` (boolean). SubagentStop also has `agent_id`, `agent_type`, `agent_transcript_path`.

**Decision control:** top-level:
```json
{ "decision": "block", "reason": "Tests still failing — fix before stopping" }
```

**CRITICAL:** Always check `stop_hook_active`. If `true`, do NOT block — exit 0 silently. Otherwise: infinite loop.

---

### Notification

**Extra input:** `message`, `title`, `notification_type`

**No decision control.** Use for side effects only (desktop alerts, sounds).

---

### SubagentStart

**Extra input:** `agent_id`, `agent_type`

**Decision control:** `additionalContext` injected into the subagent:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "Follow security guidelines for this task"
  }
}
```

---

### TaskCompleted / TeammateIdle

**TaskCompleted extra input:** `task_id`, `task_subject`, `task_description`, optional `teammate_name`, `team_name`
**TeammateIdle extra input:** `teammate_name`, `team_name`

**Decision control:** exit code 2 blocks the action, stderr is fed back as feedback.

---

### ConfigChange

**Extra input:** `source`, `file_path`

**Decision control:** top-level `decision: "block"`. Note: `policy_settings` changes cannot be blocked.

---

### SessionEnd

**Extra input:** `reason` (`"clear"`, `"logout"`, `"prompt_input_exit"`, `"bypass_permissions_disabled"`, `"other"`)

**No decision control.** Cleanup only. Default timeout: 1.5 seconds (override with `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`).

---

### PreCompact / PostCompact

**Extra input:** `trigger` (`"manual"`, `"auto"`). PreCompact also has `custom_instructions`. PostCompact has `compact_summary`.

**No decision control.** Observability and side effects only.

---

### InstructionsLoaded

**Extra input:** `file_path`, `memory_type`, `load_reason`, optional `globs`, `trigger_file_path`, `parent_file_path`

**No decision control.** Audit/observability only.

---

### WorktreeCreate / WorktreeRemove

**WorktreeCreate input:** `name` (slug for the worktree)
**WorktreeRemove input:** `worktree_path`

**WorktreeCreate output:** Print the absolute path to the created worktree on stdout.
**WorktreeRemove:** No decision control. Cleanup only.

---

### Elicitation / ElicitationResult

**Elicitation input:** `mcp_server_name`, `message`, `mode`, optional `url`, `requested_schema`
**ElicitationResult input:** `mcp_server_name`, `action`, optional `content`, `mode`

**Decision control (both):**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "Elicitation",
    "action": "accept",
    "content": { "field": "value" }
  }
}
```

`action` values: `"accept"`, `"decline"`, `"cancel"`. Exit code 2 denies.
