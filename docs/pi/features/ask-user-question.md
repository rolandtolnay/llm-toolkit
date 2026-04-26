# Ask User Question Tool

## What This Replaces

Claude Code's `AskUserQuestion` tool — a built-in tool the model can call to pause and ask the user a question mid-task. Presents a TUI input dialog, waits for a response, and returns the answer to the model.

## Why I Need It

Many tasks require clarification or decisions partway through. Without this, the model either guesses (often wrong) or dumps a wall of text asking you to re-prompt. The tool creates a structured interaction point — the model asks, you answer in-place, work continues.

Key behaviors:
- Free-text input for open questions
- Multiple-choice selection for constrained decisions
- Confirmation (yes/no) for destructive or ambiguous actions
- Non-blocking notification for status updates

## Pi API Surface

Pi's extension API provides TUI dialog methods on `ctx.ui`, but these are only available to *extensions* (event hooks, tool handlers), not to the LLM directly. The LLM needs an extension-registered tool to block and wait for user input.

Available `ctx.ui` methods:
- `ctx.ui.input(title, placeholder?)` — single-line text input
- `ctx.ui.editor(title, prefilled?)` — multi-line editor
- `ctx.ui.select(title, options[])` — selection from list
- `ctx.ui.confirm(title, message)` — yes/no confirmation
- `ctx.ui.notify(message, level)` — non-blocking notification
- `ctx.ui.custom(...)` — full custom TUI components with keyboard input
- `pi.sendUserMessage(message, timing)` — inject messages as if user typed them

## Recommended: `pi-ask-user` (edlsh)

44 stars · v0.6.1 (Apr 2026) · [GitHub](https://github.com/edlsh/pi-ask-user)

Registers an `ask_user` tool the LLM can invoke to block and wait for user input.

**Key features:**
- Searchable single-select and multi-select option lists
- Optional freeform responses and comments
- Timeout for auto-dismiss
- Split-pane details preview on wide terminals
- Overlay dialog mode preserving conversation visibility
- Bundled `ask-user` skill for decision-gating in high-stakes tasks
- Graceful fallback when interactive UI unavailable
- System prompt integration via `promptSnippet` and `promptGuidelines`

**Example tool call:**
```json
{
  "question": "Which deploy target?",
  "context": "We are choosing a deploy target.",
  "options": ["staging", {"title": "production", "description": "Customer-facing"}],
  "allowMultiple": false,
  "allowFreeform": true,
  "allowComment": true
}
```

**Install:**

```bash
pi install npm:pi-ask-user
```

**Known issues** (3 open):
- Feature request for configurable display mode (overlay vs inline)
- ask_user hidden when an image is displayed on screen

## Alternative: Build Custom (~50 lines)

The core pattern is minimal: `pi.registerTool()` → call `ctx.ui.select()` or `ctx.ui.input()` → return result. A basic implementation is ~50 lines of TypeScript. However, pi-ask-user's polish (searchable options, split-pane previews, overlay mode, decision-gating skill) would take meaningful effort to replicate.

## Other Options Evaluated

| Package | Stars | Notes |
|---------|-------|-------|
| `tomsej/pi-ext` (ask_user_question) | 34 | Part of 12-extension bundle, v0.1.0, less focused |
| `jayshah5696/pi-agent-extensions` | 18 | Beta, adapted from mitsuhiko/agent-stuff, v0.1.0 |

## Decision

Install `pi-ask-user`. Low star count (44) but focused scope, clean API, polished UX, and minimal issues. Building custom only makes sense if you need something ultra-minimal.

## Status: Researched — Install on Day 1
