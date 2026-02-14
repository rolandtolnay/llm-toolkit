---
name: create-slash-command
description: Create and configure Claude Code slash commands. Use when building custom /commands, editing command YAML frontmatter, adding arguments or dynamic context, or understanding command structure.
---

<objective>
Create effective slash commands for Claude Code — reusable prompts invoked with `/command-name` syntax.
Slash commands live in `.claude/commands/` (project) or `~/.claude/commands/` (personal) as `.md` files.
</objective>

<quick_start>

<workflow>
1. Create `.claude/commands/` directory (project) or use `~/.claude/commands/` (personal)
2. Create `command-name.md` file
3. Add YAML frontmatter (at minimum: `description`)
4. Write command prompt
5. Test with `/command-name [args]`
</workflow>

<example>
**File**: `.claude/commands/optimize.md`

```markdown
---
description: Analyze this code for performance issues and suggest optimizations
---

Analyze the performance of this code and suggest three specific optimizations:
```

**Usage**: `/optimize`

Claude receives the expanded prompt and analyzes the code in context.
</example>
</quick_start>

<generation_protocol>

1. **Analyze the user's request**:
   - What is the command's purpose?
   - Does it need user input ($ARGUMENTS)?
   - Does it produce files or artifacts?
   - Is it simple (single-step) or complex (multi-step)?

2. **Load relevant references**:
   - Read `references/arguments.md` when the command uses `$ARGUMENTS` or positional arguments
   - Read `references/patterns.md` for examples of similar command types
   - Read `references/tool-restrictions.md` when configuring `allowed-tools`

3. **Create frontmatter**:
   ```yaml
   ---
   description: Clear description of what it does
   argument-hint: [input] # Only if arguments needed
   allowed-tools: [...] # Only if tool restrictions needed
   ---
   ```

4. **Create XML-structured body**:

   **Always include:**
   - `<objective>` — what the command does
   - `<process>` — numbered steps, imperative voice
   - `<success_criteria>` — 5-7 items max, ordered by skip risk

   **Include when relevant:**
   - `<context>` — dynamic state (! `` `commands` ``) or file references (@ files)
   - `<verification>` — checks when producing artifacts. Always include for commands that create or modify files.
   - `<output>` — files created/modified

5. **Write effective prompt content**:

   Objectives: state what the command does. No "This helps...", "This ensures...", "This provides..." filler.

   <example_contrast>
   **Bad:**
   ```markdown
   <objective>
   Fix issue #$ARGUMENTS following project coding standards.

   This ensures bugs are resolved systematically with proper testing.
   </objective>
   ```

   **Good:**
   ```markdown
   <objective>
   Fix issue #$ARGUMENTS following project coding standards.
   </objective>
   ```
   </example_contrast>

   Process steps: imperative voice, specific actions ("Stage relevant files" not "Files should be staged").

   Success criteria: order by skip risk — items the LLM is most likely to skip come first. Omit low-skip-risk items ("file was read"). Cap at 5-7 items; each additional item dilutes all others.

   Every instruction must change the LLM's behavior — if removing it doesn't degrade output, remove it.

6. **Integrate $ARGUMENTS properly**:
   - If user input needed: add `argument-hint` and use `$ARGUMENTS` in body
   - If self-contained: omit `argument-hint` and `$ARGUMENTS`

7. **Save the file**:
   - Project: `.claude/commands/command-name.md`
   - Personal: `~/.claude/commands/command-name.md`
</generation_protocol>

<yaml_frontmatter>

<field name="description">
**Required** — Describes what the command does

```yaml
description: Analyze this code for performance issues and suggest optimizations
```

Shown in the `/help` command list.
</field>

<field name="argument-hint">
**Optional** — Shows expected arguments in `/help`

```yaml
argument-hint: <issue-number> [priority]
```

Use `<required>` and `[optional]` conventions.
</field>

<field name="allowed-tools">
**Optional** — Restricts which tools Claude can use

```yaml
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
```

**Formats**:
- Array: `allowed-tools: [Read, Edit, Write]`
- Single tool: `allowed-tools: SequentialThinking`
- Bash restrictions: `allowed-tools: Bash(git add:*)`

If omitted: all tools available.
</field>
</yaml_frontmatter>

<xml_structure>
All generated slash commands use XML tags in the body (after YAML frontmatter).

**Required tags:**
- `<objective>` — what the command does (no filler)
- `<process>` — numbered steps to accomplish the objective
- `<success_criteria>` — measurable completion criteria (5-7 items, skip-risk ordered)

**Conditional tags:**
- `<context>` — dynamic state via ! `` `bash` `` or @ file references
- `<verification>` — checks when producing artifacts
- `<testing>` — test commands when tests are part of workflow
- `<output>` — files created/modified
</xml_structure>

<dynamic_context>

Execute bash commands before the prompt using the exclamation mark prefix directly before backticks (no space between).

**Note:** Examples below show a space after the exclamation mark to prevent execution during skill loading. In actual slash commands, remove the space.

```markdown
<context>
- Current git status: ! `git status`
- Current git diff: ! `git diff HEAD`
- Current branch: ! `git branch --show-current`
</context>
```

The bash commands execute and their output is included in the expanded prompt.
</dynamic_context>

<file_references>

Use `@` prefix to reference specific files:

```markdown
Review the implementation in @ src/utils/helpers.js
```
(Note: Remove the space after @ in actual usage)

Claude can access the referenced file's contents.
</file_references>

<success_criteria>
1. Generated objectives contain no filler ("This helps/ensures/provides...")
2. Success criteria ordered by skip risk, 5-7 items max
3. Lazy-loaded relevant references before generating (arguments, patterns, tool-restrictions)
4. `$ARGUMENTS` handling matches command's needs (arguments vs self-contained)
5. YAML frontmatter includes `description` and `argument-hint` where applicable
6. XML structure uses semantic tags (`<objective>`, `<process>`, `<success_criteria>`)
</success_criteria>
