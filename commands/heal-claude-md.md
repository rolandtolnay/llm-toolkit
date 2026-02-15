---
name: heal-claude-md
description: Optimize CLAUDE.md files for maximum LLM effectiveness using proven prompting principles - priority hierarchy, explicit triggers, self-verification patterns
argument-hint: [path-to-claude-md]
---

<objective>
Transform the CLAUDE.md file at `<args>` (defaults to `./CLAUDE.md`) into a highly effective instruction document that Claude actually follows. If the file does not exist, report the error and stop.

**Goal**: A CLAUDE.md that contains only project-specific knowledge Claude couldn't know, with explicit patterns that prevent common violations and guide Claude to ask at the right moments.
</objective>

<core_purpose>

## What CLAUDE.md Is For

CLAUDE.md onboards Claude to YOUR codebase. Since Claude doesn't know anything about your specific project at the beginning of each session, CLAUDE.md should answer:

**WHAT** - Tell Claude about your tech stack, project structure, and codebase map. What are the apps, packages, and what is everything for? Where should Claude look for things?

**WHY** - Tell Claude the purpose of the project and what everything is doing. What are the purpose and function of different parts?

**HOW** - Tell Claude how to work on THIS project. What commands to run? How to verify changes? What project-specific conventions exist?

</core_purpose>

<process>

## Phase 1: Analyze Current State

1. Read the existing CLAUDE.md file
2. Identify what content exists:
   - Project description and tech stack
   - Commands and setup
   - Constraints and anti-patterns (note: are they tiered? concrete?)
   - Workflow guidance
   - References to other docs
3. Assess content criticality:
   - What's used in 80%+ of tasks? (candidate for inline)
   - What's detailed/reference material? (candidate for extraction)
   - What's missing from required patterns?

## Phase 2: Apply Via Negativa (Subtraction)

**Before adding anything, remove what doesn't belong.**

Claude already knows vast amounts from training data. Including generic knowledge wastes tokens and dilutes project-specific instructions.

**REMOVE these (Claude already knows):**

| Category | Examples to Remove |
|----------|-------------------|
| Universal language conventions | `Files: snake_case.dart`, `Classes: PascalCase` (Dart standard) |
| Generic framework best practices | "Use ref.watch vs ref.read", "Use AsyncValue.guard()" (Riverpod docs) |
| Generic defensive coding | "Sanitize input with .trim()", "Handle errors gracefully" |
| Meta-statements | "This is a production app", "Prioritize maintainability" |
| Textbook explanations | "Providers are lazy", "Ref object is essential for..." |

**KEEP these (Claude can't know):**

| Category | Examples to Keep |
|----------|-----------------|
| Project structure | Actual folder map, what each directory contains |
| Project-specific commands | `fvm flutter run` (not just `flutter run`) |
| Project conventions | `AppWidgetName` prefix, `camelCaseProvider` naming |
| Project constraints | "No file-private widgets", "Check lib/common/widgets/ first" |
| Decision triggers | When to ask about THIS project's schemas, auth, navigation |
| Domain model | Key entities and their relationships |
| Guide file references | Paths to project-specific documentation |

**Test for each item**: "Would Claude do the wrong thing without this?" If Claude would naturally do the right thing from training, remove it.

**Check for duplication**: Is the same rule stated multiple times? Keep ONE authoritative location. Exception: TL;DR can echo critical constraints for front-loading.

**CHECKPOINT:** Present the removal list to the user before proceeding:

```
I plan to REMOVE these items (Claude already knows them):
- [item 1] — [reason: generic framework knowledge]
- [item 2] — [reason: universal convention]
- [item 3] — [reason: meta-statement]

Confirm removals, or tell me which to keep?
```

## Phase 3: Apply Required Patterns

Transform the remaining content using each required pattern from the `<required_patterns>` section below:

1. **Create TL;DR**: Distill the 3-5 most critical constraints into a dense paragraph
2. **Build tiered constraints**:
   - Identify NEVER-level violations (architectural damage)
   - Identify YOU MUST requirements (always applicable)
   - Demote soft suggestions to Avoid tier
3. **Inline data flow**: Create or extract the core architectural diagram
4. **Convert "When to Ask"**: Transform vague guidance into explicit if-then triggers
5. **Build "When to Read" table**: Ensure all referenced guides exist or will be created
6. **Add self-check section**: Create verification checklist from NEVER/MUST items
7. **Add temporal markers**: Ensure workflow section has FIRST/THEN/ONLY THEN/FINALLY structure with exploration and clarification phases

## Phase 4: Extract to Guide Files (If Warranted)

If the original CLAUDE.md contains detailed content that should be extracted:

**INLINE in CLAUDE.md when:**
- Content is critical AND used in 80%+ of tasks
- Violating it causes architectural damage
- It's a constraint that applies universally

**EXTRACT to separate guide files when:**
- Content is detailed/reference material
- It applies only to specific task types
- It would benefit from code examples that may change

**Code examples are appropriate when:**
- They show concrete architectural violations (Wrong/Right tables)
- They document critical patterns that prevent common mistakes
- They're stable (won't change frequently)

Steps:

1. **Identify extraction candidates**:
   - Detailed code patterns with multiple examples
   - Widget/component catalogs
   - API implementation guides
   - Testing documentation
   - Style guides with extensive rules

2. **Create guide files** with extracted content:
   - `docs/guides/PATTERNS.md` - Entity, provider, screen patterns
   - `docs/guides/ARCHITECTURE.md` - Layer responsibilities, data flow details
   - `docs/guides/UI_GUIDE.md` - Widget catalog, spacing, theme
   - Other project-specific guides as needed

3. **Structure each guide file**:
   - Clear title and purpose
   - "When to use this guide" trigger
   - Content organized by task type
   - File references to authoritative code (e.g., `Reference: lib/feature/file.dart`)

4. **Update CLAUDE.md**: Ensure "When to Read" table points to new guides

## Phase 5: Verify Effectiveness

Check these high-skip-risk items before finishing:

- [ ] Every item passes the removal test: "Would Claude do wrong without this?"
- [ ] NEVER tier has concrete Wrong/Right examples, not just abstract rules
- [ ] "When to Ask" triggers are specific enough to pattern-match, not vague
- [ ] No vague language like "when appropriate" or "as needed" remains
- [ ] NEVER tier includes "modifying unrelated code" constraint
- [ ] Avoid tier includes "over-engineering" constraint
- [ ] Workflow includes assumption-surfacing step before implementation
- [ ] No generic framework knowledge or universal conventions remain

</process>

<required_patterns>

## Required Patterns

Every healed CLAUDE.md MUST include these patterns. If the user asks WHY a pattern matters, read `@references/llm-behavior-patterns.md`.

### 1. TL;DR Section (Top of File)

A dense 2-4 sentence paragraph capturing the most critical constraints.

```markdown
## TL;DR for Claude

Data flows UI → Provider → API—**never shortcut this**. Check `lib/common/widgets/`
before creating any widget. No file-private widgets—if it's big enough to be a widget,
it gets its own file. STOP and ask before: adding screens, changing schemas, modifying auth.
```

---

### 2. Tiered Constraints (Priority Hierarchy)

Replace flat "Avoid" lists with explicit priority tiers:

```markdown
## Critical Constraints

### NEVER (architectural violations)
These cause structural damage. Stop immediately if you catch yourself doing them.

| Wrong | Right |
|-------|-------|
| [concrete bad example] | [concrete good example] |
| Modifying code unrelated to the task | Only change what the task requires |

### YOU MUST
- **[Requirement]:** [specific action]
- **[Requirement]:** [specific action]

### Avoid (maintainability issues)
- [Issue] → [alternative]
- Over-engineering → implement the minimal solution first; expand only if needed
```

---

### 3. Data Flow Diagram

Inline the core architectural flow with an explicit warning:

```markdown
## Data Flow

```
User Action → UI calls provider.method() → Provider calls API
    → API returns entity → Provider updates state → UI rebuilds
```

**If you're tempted to shortcut this flow, stop.** [Explain why the layers exist]
```

---

### 4. If-Then Triggers for "When to Ask"

Replace vague "ask for clarification on business logic" with explicit conditional triggers:

```markdown
## When to STOP and Ask

**IF** any of these apply, confirm before proceeding:

| Trigger | Why |
|---------|-----|
| Adding or removing a screen | Affects navigation structure |
| Modifying database schema | Migration strategy needed |
| Changing authentication flow | Security implications |
| Deleting user data | Confirmation UX decisions |

**ONLY proceed without asking when:**
- Following existing patterns with established entities
- Using components from shared libraries
- Running formatting, linting, code generation
```

---

### 5. When to Read Table (Trigger-Based)

Use action verbs and clear file references:

```markdown
## When to Read

**FIRST** check if a guide exists before implementing:

| When you are... | Read |
|-----------------|------|
| Building screens, widgets, or layouts | `@docs/guides/UI_GUIDE.md` |
| Creating entities, providers, or screens | `@docs/guides/PATTERNS.md` |
| Understanding layer rules or data flow | `@docs/guides/ARCHITECTURE.md` |
```

---

### 6. Self-Check Section

Explicit verification checklist before task completion:

```markdown
## Before Completing Any Task

Self-check before marking done:

- [ ] Searched shared components for existing solutions?
- [ ] Data flows through proper layers without shortcuts?
- [ ] No architectural violations from the NEVER list?
- [ ] Ran code generation if needed?
- [ ] All user-facing strings use localization?
```

---

### 7. Temporal Markers in Workflow

Use FIRST/THEN/ONLY THEN/FINALLY to enforce sequence and encourage exploration before action:

```markdown
## Working Effectively

**FIRST:** Scan the skill list in your system message for skills matching this project's
technology or domain. Invoke each match via the Skill tool — skills contain conventions
and patterns that change what you look for during exploration.

**THEN:** Explore before committing. Use parallel explorer agents to understand existing
patterns, conventions, and how similar features are implemented in this codebase.

**THEN:** Check for existing solutions:
- Search shared widget/component directories for reusable pieces
- Look at similar features for established patterns
- Verify the functionality doesn't already exist

**THEN:** Surface assumptions. Before implementing, state what you're assuming about:
- Requirements that weren't explicitly specified
- How existing code behaves
- Edge cases and error handling

If any assumption feels risky, ask.

**THEN:** Clarify requirements. Use AskUserQuestion as many times as needed to understand:
- Expected behavior and edge cases
- Design decisions that aren't specified
- Ambiguous requirements

**ONLY THEN:** Plan and execute. With context gathered and requirements clear,
implement using established patterns.

**FINALLY:** Run code generation, format, and fix before marking complete.
```

</required_patterns>

<output>

## Files Created/Modified

**Always:**
- `CLAUDE.md` - Transformed with required patterns, generic knowledge removed

**If content extracted:**
- `docs/guides/*.md` - Guide files with extracted detailed content

</output>

<success_criteria>

## The healed CLAUDE.md succeeds when:

1. **Only project-specific knowledge** — Nothing Claude already knows from training data
2. **Priority is visually obvious** — NEVER violations stand out from Avoid suggestions
3. **No judgment calls required** — Triggers are explicit enough to pattern-match
4. **Self-verification is prompted** — Checklist forces review before completing
5. **Sequence is enforced** — Temporal markers prevent skipping exploration/clarification
6. **Strong language throughout** — NEVER/MUST/STOP instead of Avoid/Should/Consider

</success_criteria>
