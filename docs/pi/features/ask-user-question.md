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

## Pi API Surface (Known)

Pi's extension API provides these TUI dialog methods on `ctx.ui`:
- `ctx.ui.input(title, placeholder?)` — single-line text input
- `ctx.ui.editor(title, prefilled?)` — multi-line editor
- `ctx.ui.select(title, options[])` — selection from list
- `ctx.ui.confirm(title, message)` — yes/no confirmation
- `ctx.ui.notify(message, level)` — non-blocking notification

These can be called from within a custom tool's `execute` function.

## Research

- [ ] Check if an existing Pi package provides this
- [ ] Look at how IndyDevDan's extensions handle user interaction
- [ ] Determine if this should be a standalone extension or bundled with others

## Implementation

_To be filled after research._

## Status: Not Started
