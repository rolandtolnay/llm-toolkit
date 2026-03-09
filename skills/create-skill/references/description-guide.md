# Skill Description Guide

How to write YAML `description` fields that Claude reliably discovers and invokes.

## How Matching Works

Claude sees skills as a flat `name: description` list in a system-reminder. It matches user intent against this single string. The `name` carries semantic weight — don't repeat what the name already conveys.

## Template

```
[What it does — distinct verb]. Use [when/after] [concrete trigger conditions].
[Optional: specific user phrases or artifacts].
[Optional: Do NOT use when... (only if overlapping skills exist)].
```

**Target length:** 25-35 words. Under 20 too sparse for matching. Over 50 wastes context budget loaded into every session.

## Principles

### 1. Lead with a distinct verb

```
BAD:  "Flutter/Dart code simplification principles."
GOOD: "Reduce complexity in Flutter/Dart code."
```

The verb ("Reduce", "Organize", "Review", "Create") is the primary differentiator.

### 2. Use user vocabulary

```
BAD:  "clarity and maintainability"
GOOD: "too nested, hard to read, or has duplication"
```

Match the words users actually say.

### 3. Always include "Use when" clause

```
BAD:  "Guide for creating MCP servers"
GOOD: "Create MCP servers. Use when building custom integrations or data sources via MCP"
```

Without "Use when", Claude must infer invocation timing — lowering confidence below threshold.

### 4. Disambiguate overlapping skills

Each overlapping skill needs naturally exclusive trigger vocabulary:

| Skill | Distinct Verb | Distinct Trigger |
|---|---|---|
| flutter-senior-review | "Review...for issues" | "reviewing PRs, auditing design" |
| flutter-code-quality | "Organize...to follow conventions" | "after implementation, restructure" |
| flutter-code-simplification | "Reduce complexity" | "too nested, hard to read" |

### 5. Anchor to concrete artifacts

```
BAD:  "Use when working with skills"
GOOD: "Use when authoring new SKILL.md files"
```

File names, tool names, and format extensions (`.pptx`, `SKILL.md`) are strong matching signals.

## Gold Standard Examples

**Trigger-first with user phrases:**
```yaml
description: >
  Use when the user wants to customize keyboard shortcuts, rebind keys,
  add chord bindings, or modify ~/.claude/keybindings.json. Examples:
  "rebind ctrl+s", "add a chord shortcut", "change the submit key".
```

**Intent-mapping with quoted patterns:**
```yaml
description: >
  Helps users discover and install agent skills when they ask questions
  like "how do I do X", "find a skill for X", or express interest in
  extending capabilities.
```

**File-format with boundaries:**
```yaml
description: >
  Use this skill any time a .pptx file is involved — as input, output,
  or both. Trigger whenever the user mentions "deck," "slides,"
  "presentation," or references a .pptx filename.
```

## Anti-Patterns

| Pattern | Problem |
|---|---|
| "Expert guidance for creating, building, and using..." | Generic opener, wastes tokens |
| "principles" / "guidelines" / "best practices" | Category labels, not trigger signals |
| Identical triggers across 3 skills | Ambiguity = no invocation |
| Description under 15 words | Not enough surface for semantic matching |
| Repeating the skill name in the description | Name already carries that signal |

## Undertriggering Note

When in doubt, make descriptions slightly "pushy." Undertriggering (skill never fires) is harder to debug than overtriggering (skill fires too often, can be refined). Include edge-case phrasings users might try.
