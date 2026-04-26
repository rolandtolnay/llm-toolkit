# Security Hooks

## What This Replaces

Claude Code's `PreToolUse` hooks for Bash and file operations — shell scripts that intercept tool calls and block dangerous commands or path access before execution. Configured via `settings.json` under `hooks.PreToolUse`.

## Why I Need It

Pi runs in YOLO mode by default — no permission prompts, full system access. Real incidents of agents deleting entire projects have been reported. A custom guard system provides fine-grained control: regex-based command blocking, path protection tiers (zero-access, read-only, no-delete), and inline interpreter detection — without the overhead of a generic permission gate extension.

## Claude Code Setup (for reference)

Two `PreToolUse` hooks:

| Hook | Matcher | What It Does |
|------|---------|--------------|
| `bash-guard.py` | `Bash` | Checks commands against regex patterns and path rules. Handles tilde/env-var expansion, inline interpreter code (`python3 -c`, `node -e`, etc.), write-intent analysis, redirection targets. Can block or escalate to "ask". |
| `file-guard.py` | `Edit\|Write\|Read\|Glob\|Grep` | Checks file paths against zero-access (block all), read-only (block writes), and allowReadPaths (exempt reads from zero-access). |

Both are driven by a shared `patterns.json` config with these path tiers:

| Config Key | Effect |
|------------|--------|
| `zeroAccessPaths` | Block all operations (read, write, delete) |
| `readOnlyPaths` | Allow reads, block writes/edits/deletes |
| `noDeletePaths` | Allow reads and writes, block deletes |
| `allowReadPaths` | Exempt specific paths from zero-access for reads only |
| `bashPatterns` | Regex patterns to block or escalate bash commands |

Guard scripts are private — not included in this repo. User must provide their own implementations.

## Pi API Surface

Pi's `tool_call` event is the equivalent of Claude Code's `PreToolUse`:

```typescript
pi.on("tool_call", async (event, ctx) => {
  // event.toolName: "bash" | "read" | "write" | "edit"
  // event.input: tool parameters (e.g. { command: "rm -rf /" } for bash)
  // Return { block: true, reason: "..." } to prevent execution
  // Return nothing to allow
});
```

Key differences from Claude Code hooks:
- **TypeScript, not shell scripts** — extension code, not external processes
- **Richer blocking** — return `{ block: true, reason }` directly, no exit codes
- **No "ask" mode** — Pi has no built-in permission prompt. Use `ctx.ui.confirm()` to build your own.
- **Event shape differs** — `event.toolName` is lowercase (`bash`, `read`, `write`, `edit`), `event.input` matches Pi's tool parameter schema

## Porting Strategy

### Approach: TypeScript Shim + Existing Python Scripts

Minimal rewrite. A thin Pi extension translates the `tool_call` event into the JSON format the existing Python guards expect, shells out to them, and interprets exit codes.

**What the shim does:**
1. Subscribes to `tool_call` event
2. Maps Pi's event shape → guard script's expected stdin JSON format
3. Pipes the translated JSON to the appropriate Python script via `execSync`
4. Exit code 0 → allow, exit code 2 → block (stderr becomes the reason)
5. JSON output with `permissionDecision: "ask"` → call `ctx.ui.confirm()` for user decision

**What the user provides:**
- `bash-guard.py` — bash command guard script (reads JSON from stdin, exits 0/2)
- `file-guard.py` — file operation guard script (reads JSON from stdin, exits 0/2)
- `patterns.json` — shared config with path rules and bash patterns

Place these in `~/.pi/agent/hooks/` (or any stable path) and reference from the extension.

### Expected stdin format for guard scripts

The shim must translate Pi's `tool_call` event into this shape:

```json
{
  "tool_name": "Bash",
  "tool_input": { "command": "rm -rf /" },
  "cwd": "/path/to/project"
}
```

For file tools:

```json
{
  "tool_name": "Write",
  "tool_input": { "file_path": "/etc/passwd" },
  "cwd": "/path/to/project"
}
```

Pi tool names are lowercase (`bash`, `write`, `edit`, `read`). The shim must capitalize them to match the guard scripts' expectations (`Bash`, `Write`, `Edit`, `Read`). Pi uses `grep` and `find` as separate tools (not `Glob`/`Grep`) — map accordingly.

### Extension skeleton

```typescript
// ~/.pi/agent/extensions/security-guard.ts
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { execSync } from "child_process";
import { resolve } from "path";

const HOOKS_DIR = resolve(process.env.HOME!, ".pi/agent/hooks");

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    // 1. Determine which guard script to call based on event.toolName
    // 2. Translate event shape to guard's expected stdin JSON
    // 3. execSync the guard script, pipe translated JSON to stdin
    // 4. If exit code 2: return { block: true, reason: stderr }
    // 5. If stdout contains permissionDecision "ask": ctx.ui.confirm()
    //
    // User must provide: bash-guard.py, file-guard.py, patterns.json
    // in HOOKS_DIR
  });
}
```

### Tool name mapping

| Pi tool | Guard expects | Guard script |
|---------|---------------|--------------|
| `bash` | `Bash` | `bash-guard.py` |
| `write` | `Write` | `file-guard.py` |
| `edit` | `Edit` | `file-guard.py` |
| `read` | `Read` | `file-guard.py` |
| `grep` | `Grep` | `file-guard.py` |
| `find` | `Glob` | `file-guard.py` |

### "Ask" mode translation

Claude Code hooks can output `permissionDecision: "ask"` to escalate to a permission prompt. Pi has no built-in equivalent, but `ctx.ui.confirm()` provides a yes/no dialog:

```typescript
if (guardWantsAsk) {
  const allowed = await ctx.ui.confirm("Security Guard", reason);
  if (!allowed) return { block: true, reason };
}
```

## Decision

Port via TypeScript shim that delegates to existing Python guard scripts. This preserves the battle-tested guard logic without rewriting it, and keeps the extension itself minimal (~30-40 lines).

## Status: Researched — Build on Day 1
