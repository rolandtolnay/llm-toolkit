# Format-on-Write & Diagnostics Feedback

## What This Replaces

Nothing directly — Claude Code doesn't have this. This is the single highest-leverage improvement identified from oh-my-pi's architecture: intercepting write/edit tool results to append formatter output and diagnostics, so the model self-corrects in the same turn instead of discovering errors later.

## Why I Need It

The core development loop is edit → verify → fix. Without this, the model writes code, moves on, and only discovers formatting or type errors much later (if at all). By enriching every write/edit tool result with immediate feedback, the model sees problems the instant they're created and fixes them before moving to the next step.

oh-my-pi bakes this into its core with LSP integration (11 operations, format-on-write, diagnostics-on-write for 40+ languages). We can approximate the most valuable 20% of this with a config-driven extension.

## Pi API Surface

Two events make this possible:

| Event | Purpose |
|-------|---------|
| `tool_result` | Fires after a tool completes. Can append text to the result the model sees. |
| `pi.registerTool()` | Alternative: register a wrapper tool that formats + checks after writes. |

The `tool_result` approach is better — it's invisible to the model and doesn't add tools to the system prompt.

## Implementation: Config-Driven Extension (~80 lines)

A single extension that detects the project type and runs the appropriate formatter and analyzer after every write/edit.

### Language detection

Detect from file extension, with project-level config override:

| File Pattern | Formatter | Analyzer |
|--------------|-----------|----------|
| `*.dart` | `dart format` | `dart analyze --no-fatal-infos` |
| `*.ts`, `*.tsx` | `npx prettier --write` | `npx tsc --noEmit` |
| `*.js`, `*.jsx` | `npx prettier --write` | `npx eslint` (if config exists) |
| `*.vue` | `npx prettier --write` | `vue-tsc --noEmit` |
| `*.java` | `google-java-format` (if available) | `javac` (if standalone) or skip |
| `*.json` | `npx prettier --write` | — |
| `*.yaml`, `*.yml` | `npx prettier --write` | — |

### Extension skeleton

```typescript
// ~/.pi/agent/extensions/format-on-write.ts
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { execSync } from "child_process";
import { extname } from "path";

const LANG_CONFIG: Record<string, { format?: string; analyze?: string }> = {
  ".dart": { format: "dart format {file}", analyze: "dart analyze --no-fatal-infos {file}" },
  ".ts":   { format: "npx prettier --write {file}", analyze: "npx tsc --noEmit" },
  ".tsx":  { format: "npx prettier --write {file}", analyze: "npx tsc --noEmit" },
  ".vue":  { format: "npx prettier --write {file}", analyze: "vue-tsc --noEmit" },
  ".js":   { format: "npx prettier --write {file}" },
  ".jsx":  { format: "npx prettier --write {file}" },
  ".java": { },
  ".json": { format: "npx prettier --write {file}" },
};

export default function (pi: ExtensionAPI) {
  pi.on("tool_result", async (event, ctx) => {
    if (!["write", "edit"].includes(event.toolName)) return;

    const filePath = event.input?.file_path;
    if (!filePath) return;

    const ext = extname(filePath);
    const config = LANG_CONFIG[ext];
    if (!config) return;

    const feedback: string[] = [];

    if (config.format) {
      try {
        execSync(config.format.replace("{file}", filePath), {
          timeout: 10000, encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"],
        });
        feedback.push("[formatted]");
      } catch (e: any) {
        feedback.push(`[format error] ${e.stderr?.slice(0, 200)}`);
      }
    }

    if (config.analyze) {
      try {
        const cmd = config.analyze.replace("{file}", filePath);
        execSync(cmd, { timeout: 15000, encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] });
      } catch (e: any) {
        const output = (e.stdout || e.stderr || "").slice(0, 500);
        if (output.trim()) feedback.push(`[diagnostics]\n${output}`);
      }
    }

    if (feedback.length > 0) {
      event.result = (event.result || "") + "\n" + feedback.join("\n");
    }
  });
}
```

### Key design choices

- **Config-driven, not hardcoded** — add languages by extending the `LANG_CONFIG` map. No code changes needed per language.
- **File-scoped formatting, project-scoped analysis** — `dart format` and `prettier` run on the specific file; `tsc --noEmit` and `dart analyze` check the project (catches cross-file type errors).
- **Timeouts** — 10s for formatting, 15s for analysis. Prevents hanging on large projects.
- **Truncated output** — caps diagnostic output at 500 chars to avoid flooding context.
- **Silent on success** — only appends `[formatted]` tag and diagnostic output when there are issues.

### Project-level override

For projects with non-standard tooling, support a `.pi/format-config.json` override:

```json
{
  ".dart": { "format": "dart format -l 120 {file}", "analyze": "dart analyze {file}" },
  ".ts": { "format": "dprint fmt {file}", "analyze": "npx tsc --noEmit" }
}
```

The extension checks for this file at startup and merges it over defaults.

## What This Doesn't Cover (vs oh-my-pi)

oh-my-pi's LSP integration provides: go-to-definition, find-references, hover docs, rename, code actions, symbol search, workspace diagnostics. These are IDE features that require a persistent LSP client process — significant complexity for marginal value in a terminal agent. The format + diagnostics feedback loop captures ~80% of the value.

## Status: Researched — Build in Week 2
