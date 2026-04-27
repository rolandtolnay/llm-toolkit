# Plan Mode

## What This Replaces

Claude Code's plan mode — a mode where the model analyzes the task and produces a plan using only read-only tools, then waits for user approval before executing changes. Toggled via `/plan` or the `EnterPlanMode` tool.

## Why I Need It

For complex or risky tasks, I want the model to think through its approach before making changes. This prevents wasted effort from wrong-direction implementations and gives me a chance to steer the approach before any files are modified.

Key behaviors:
- Toggle on/off via `/plan` — visible in UI as a persistent status indicator, not a one-shot skill
- Read-only tool access during planning (read, grep, find, ls — no write, edit, bash)
- Plan presented for review with structured resolution options:
  - **Accept + continue**: unlock full tools and execute in the same context
  - **Accept + reset context**: compact/clear the planning context and start execution fresh with only the plan — avoids polluting execution with exploratory reads
  - **Decline + revise**: stay in plan mode, provide feedback for the model to revise

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

## Recommended: Custom Extension (~120 lines)

Build a harness-level extension with UI integration, tool enforcement, and structured plan resolution. This is not a skill — it needs to control the UI, block tools, and manage context.

**Workflow:** `/plan` activates → footer shows PLAN MODE → agent explores read-only → plan presented → user chooses accept/reset/revise via selection dialog → tools unlock or model revises.

```typescript
// ~/.pi/agent/extensions/plan-mode.ts
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  let planMode = false;
  const readOnlyTools = ["read", "grep", "find", "ls"];

  pi.registerCommand("plan", {
    description: "Toggle plan mode (read-only exploration)",
    async execute(_args, ctx) {
      planMode = !planMode;
      if (planMode) {
        ctx.ui.setStatus("plan-mode", "📋 PLAN MODE");
        pi.sendMessage({
          role: "user",
          content:
            "You are now in plan mode. Explore the codebase using read-only tools only. " +
            "When your plan is complete, say PLAN READY and present it clearly.",
        });
      } else {
        ctx.ui.setStatus("plan-mode", "");
      }
    },
  });

  // Block non-read-only tools during planning
  pi.on("tool_call", async (event, ctx) => {
    if (!planMode) return;
    if (!readOnlyTools.includes(event.toolName)) {
      return {
        block: true,
        reason: "Plan mode active — read-only tools only. Present your plan first.",
      };
    }
  });

  // Watch for plan completion and present resolution options
  pi.on("message", async (event, ctx) => {
    if (!planMode) return;
    if (event.role !== "assistant") return;
    if (!event.content?.includes("PLAN READY")) return;

    const choice = await ctx.ui.select("Plan Review", [
      { title: "Accept — continue", description: "Unlock tools and execute in current context" },
      { title: "Accept — fresh context", description: "Compact context, keep only the plan" },
      { title: "Revise", description: "Stay in plan mode and provide feedback" },
    ]);

    if (choice === 0) {
      // Accept + continue in same context
      planMode = false;
      ctx.ui.setStatus("plan-mode", "");
      pi.sendMessage({ role: "user", content: "Plan approved. Execute it now." });
    } else if (choice === 1) {
      // Accept + reset context (compact with plan as focus)
      planMode = false;
      ctx.ui.setStatus("plan-mode", "");
      // /compact with focus preserves only the plan in the compacted summary
      pi.runCommand("compact", "Retain only the approved plan. Discard exploration context.");
      pi.sendMessage({ role: "user", content: "Plan approved. Execute it now." });
    } else {
      // Decline — stay in plan mode, let user provide feedback
      pi.sendMessage({
        role: "user",
        content: "Plan needs revision. I'll provide feedback — stay in plan mode.",
      });
    }
  });
}
```

### Why this needs to be an extension, not a skill

| Requirement | Skill file | Extension |
|-------------|-----------|-----------|
| Footer status indicator (`PLAN MODE`) | No | `ctx.ui.setStatus()` |
| Tool blocking (enforced read-only) | No | `tool_call` event with `{ block: true }` |
| Structured resolution dialog | No | `ctx.ui.select()` with options |
| Context reset on accept | No | `pi.runCommand("compact", ...)` |
| Persistent toggle across turns | No | Extension state variable |

The context reset is the key differentiator. After a planning phase that reads 20+ files, the execution context is polluted with exploratory reads that crowd out working memory. Compacting with the plan as focus gives the model a clean slate with only the approved plan — directly replicating Claude Code's "accept + reset" behavior.

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

Build the custom extension (~120 lines). The UI toggle, enforced tool blocking, structured resolution dialog, and context reset are harness-level behaviors that a skill file cannot provide. The "accept + fresh context" option — compacting away exploratory reads to give the model a clean execution slate — is the highest-value feature and requires programmatic control.

The `pi-subagents` planner agent remains useful as a complementary option: delegating planning to a separate agent context when you want total isolation rather than same-session compaction.

## Status: Researched — Build on Day 1
