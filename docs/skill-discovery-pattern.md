# Skill Discovery Pattern

Reference for adding reliable skill loading to commands. Based on first-principles analysis against `prompt-quality-guide.md`.

## Why It Fails

Vague instructions like "check available skills" and "load matching skills" fail because:

- **No location**: "available skills" doesn't tell the LLM where to look. It may reason from memory instead of scanning the actual skill list.
- **No tool named**: "load" is abstract. Without naming the Skill tool, the instruction lacks an executable action.
- **No decision branches**: Unspecified outcomes (one match? multiple? none?) default to "skip entirely."
- **Buried positioning**: Embedding skill loading as a sub-paragraph inside a step with a different primary purpose puts it in the attention trough.

## Canonical Format

Use this block verbatim or adapt minimally. Place as a **dedicated step** or the **first action in the process** — never as a sub-paragraph of another step.

```markdown
Scan the skill list in your system message for skills matching the [ticket's/task's] technology or domain. Invoke each match via the Skill tool before proceeding — skills contain conventions and patterns that change what you look for during [exploration/verification/implementation].

- One clear match → invoke it directly
- Multiple candidates → use AskUserQuestion to let the user choose
- No match → proceed without
```

Adjust the bracketed terms to fit the command's context.

## Why Each Element Matters

| Element | Purpose | Without it |
|---|---|---|
| "skill list in your system message" | Names exact location to scan | LLM may not scan at all |
| "Invoke ... via the Skill tool" | Names exact tool | LLM treats "load" as abstract thought |
| Decision branches (one/multiple/none) | Covers all outcomes explicitly | Ambiguity → skipping |
| Dedicated step or first action | Positional prominence | Competes with parent step's goal |
| "change what you look for" | Corrective rationale (failure mode) | No motivation to comply |

## Anti-Patterns

- **"Check available skills for any that match"** — "check" and "available" are vague. Scan where? Match how?
- **"Load matching skills now so their guidance informs X"** — motivational rationale, not corrective. Doesn't encode what goes wrong if skipped.
- **Embedding inside another step** — positional attention bias causes the LLM to focus on the parent step's primary goal and skip the sub-instruction.
