# Plan Mode

## What This Replaces

Claude Code's plan mode — a mode where the model analyzes the task and produces a plan using only read-only tools, then waits for user approval before executing changes. Toggled via `/plan` or the `EnterPlanMode` tool.

## Why I Need It

For complex or risky tasks, I want the model to think through its approach before making changes. This prevents wasted effort from wrong-direction implementations and gives me a chance to steer the approach before any files are modified.

Key behaviors:
- Toggle on/off (persist across turns or per-task)
- Read-only tool access during planning (read, grep, find, ls — no write, edit, bash)
- Plan presented for review before execution
- User approves or redirects, then full tools unlock

## Pi API Surface

Relevant extension capabilities for building plan mode:

| Method | Purpose |
|--------|---------|
| `pi.registerCommand("plan")` | Toggle command |
| `pi.setActiveTools()` / `pi.getActiveTools()` | Dynamically enable/disable tools |
| `tool_call` event | Block tools with `{ block: true, reason }`, args are mutable |
| `before_agent_start` event | Modify system prompt per turn |
| `ctx.ui.setStatus()` | Show "PLAN MODE" indicator in footer |
| `ctx.ui.setWidget()` | Display the plan persistently above/below editor |
| `ctx.ui.confirm()` | Approval dialog before switching to execution |

## Recommended: Custom Extension (~80 lines)

Build a small custom extension rather than installing a community package. The extension skeleton is straightforward and the community-validated approach.

**Workflow:** `/plan` toggles on → agent explores read-only and produces a plan → user reviews → approves via confirm dialog → full tools unlock.

```typescript
// .pi/extensions/plan-mode.ts
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  let planMode = false;
  const readOnlyTools = ["read", "grep", "find", "ls"];

  pi.registerCommand("plan", {
    description: "Toggle plan mode (read-only exploration)",
    async execute(_args, ctx) {
      planMode = !planMode;
      if (planMode) {
        ctx.ui.setStatus("plan-mode", "PLAN MODE");
        pi.sendMessage({
          role: "user",
          content:
            "You are now in plan mode. Explore the codebase using read-only tools only. Write your plan, then I will approve before execution.",
        });
      } else {
        ctx.ui.setStatus("plan-mode", "");
      }
    },
  });

  pi.on("tool_call", async (event, ctx) => {
    if (!planMode) return;
    if (!readOnlyTools.includes(event.toolName)) {
      return {
        block: true,
        reason: "Plan mode active — read-only tools only. Write your plan first.",
      };
    }
  });
}
```

This is a starting skeleton. Extend with:
- `ctx.ui.confirm()` for plan approval before unlocking full tools
- `ctx.ui.setWidget()` to display the plan persistently
- Auto-disable after approval (set `planMode = false` on confirm)

## Alternative: Plan-First Skill File (No Extension)

The single most praised workflow pattern in the Pi community. A skill file that enforces structured planning purely through instructions — no extension code, no tool blocking.

Reddit (r/LocalLLaMA, 362 upvotes, Apr 23): "The real game changer was the plan-first skill file I created. Like it actually follows what you say and does everything step by step without going off the rails. Used it on actual production stuff and it held up."

Create `.pi/skills/plan-first/SKILL.md` with instructions that direct the agent to explore read-only, write a structured plan, and wait for approval before executing. No enforcement mechanism — relies on the model following instructions. Works surprisingly well with GPT 5.5's instruction-following.

**Tradeoff:** No technical enforcement of read-only mode. The model *could* write files during planning if it decides to. But community reports suggest this is rarely an issue with well-written skill instructions.

## Alternative: `pi-subagents` Planner Agent

Both `pi-subagents` (nicobailon) and `@tintinweb/pi-subagents` ship built-in `planner` / `Plan` agent types:
- Read-only tools (read, bash, grep, find, ls)
- Standalone system prompt tailored to architectural planning
- Runs entirely in terminal
- Can be ejected and customized via `.pi/agents/Plan.md`

This delegates planning to a separate agent context rather than toggling the primary agent's mode. Good for keeping planning output isolated from execution context.

## Evaluated and Not Recommended

### `@plannotator/pi-extension`

13.8K downloads/wk · v0.19.1 (Apr 2026) · 49 versions

The most sophisticated plan mode available — genuinely blocks destructive tools during planning AND provides a visual browser UI for plan review with approve/deny/annotate workflow.

**Rejected because:** Opens markdown plans in a browser annotation UI. Requires browser roundtrip for plan review. Incompatible with a terminal-first workflow. The iterative approve/deny/annotate loop via browser is impressive but adds friction for single-developer use.

### `shitty-extensions` plan-mode (hjanuschka)

96 stars (for entire bundle of 15 extensions). Activation: `/plan`, `Shift+P`, or `--plan` flag. "Claude Code-style read-only exploration mode." Part of a larger extension bundle — less documentation, mechanism for tool blocking not documented in README.

### `burneikis/pi-plan`

1 star. File-based approach where planning runs in one session and execution starts in a fresh session with the plan as sole context. Interesting two-session approach but effectively abandoned.

## Decision

Build custom extension (~80 lines) for enforced plan mode with tool blocking. Complement with a plan-first skill file for lighter-weight planning on simpler tasks. The `pi-subagents` planner agent provides a third option for delegated planning once subagents are installed.

## Status: Researched — Build on Day 1
