---
name: heal-claude-md
description: Optimize CLAUDE.md files for maximum LLM effectiveness using proven prompting principles - priority hierarchy, explicit triggers, self-verification patterns
argument-hint: [path-to-claude-md]
---

<objective>
Transform the CLAUDE.md file at `<args>` (defaults to `./CLAUDE.md`) into a highly effective instruction document that Claude actually follows.

CLAUDE.md is the highest-leverage file in a codebase—every instruction affects every Claude session. This command applies proven LLM prompting principles to maximize instruction adherence, not arbitrary line counts.

**Goal**: A CLAUDE.md that contains only project-specific knowledge Claude couldn't know, with explicit patterns that prevent common violations and guide Claude to ask at the right moments.
</objective>

<core_purpose>

## What CLAUDE.md Is For

CLAUDE.md onboards Claude to YOUR codebase. Since Claude doesn't know anything about your specific project at the beginning of each session, CLAUDE.md should answer:

**WHAT** - Tell Claude about your tech stack, project structure, and codebase map. What are the apps, packages, and what is everything for? Where should Claude look for things?

**WHY** - Tell Claude the purpose of the project and what everything is doing. What are the purpose and function of different parts?

**HOW** - Tell Claude how to work on THIS project. What commands to run? How to verify changes? What project-specific conventions exist?

</core_purpose>

<principles>

## Why These Patterns Work (LLM Behavior)

Understanding these failure modes explains why each pattern matters:

**1. Eager Generation**
LLMs want to produce output immediately, skipping research and validation steps.
→ **Solution**: Temporal markers (FIRST/THEN/FINALLY), explicit WAIT/STOP points

**2. Training Data Contamination**
LLMs prefer patterns from training data over project-specific instructions.
→ **Solution**: Repetition of critical constraints, concrete BAD/GOOD examples

**3. Ambiguity Exploitation**
LLMs interpret vague rules loosely, choosing the path of least resistance.
→ **Solution**: If-then conditional triggers, explicit thresholds, priority labels

**4. Flat Priority Processing**
Without visual hierarchy, all instructions have equal weight.
→ **Solution**: Tiered constraints (NEVER/YOU MUST/Avoid), CRITICAL labels

**5. No Self-Verification**
LLMs generate forward without looking back to check their work.
→ **Solution**: Self-check section with explicit verification checklist

**6. Wrong Assumptions**
LLMs make assumptions about requirements and run with them without checking.
→ **Solution**: Explicit "surface assumptions" step before implementation

**7. Side-Effect Changes**
LLMs modify unrelated code (comments, refactoring) as "improvements" while doing a task.
→ **Solution**: NEVER rule against modifying code unrelated to the task

**8. Over-Engineering**
LLMs bloat abstractions and overcomplicate solutions when simpler ones exist.
→ **Solution**: Explicit "minimal solution first" constraint in Avoid tier

## Via Negativa: What to REMOVE

**CRITICAL**: Claude already knows vast amounts from training data. Including generic knowledge wastes tokens and dilutes project-specific instructions.

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

## Word-Level Patterns

Stronger language improves adherence. Transform weak phrasing:

| Weak (Permissive) | Strong (Enforced) | Why It Works |
|-------------------|-------------------|--------------|
| Avoid | NEVER | Absolute prohibition vs soft suggestion |
| Don't | DO NOT | Explicit negation |
| Should | MUST / YOU MUST | Obligation vs recommendation |
| Ask for clarification on... | STOP and ask when... | Creates explicit gate |
| Proceed autonomously for... | ONLY proceed without asking when... | Inverts default to caution |
| Consider | ALWAYS | Removes optionality |
| Try to | — (remove) | Eliminates wiggle room |

## Decision Criteria: Inline vs Extract

**INLINE in CLAUDE.md when:**
- Content is critical AND used in 80%+ of tasks
- Violating it causes architectural damage
- It's a constraint that applies universally
- Examples: Data flow rules, layer separation, state management patterns

**EXTRACT to separate guide files when:**
- Content is detailed/reference material
- It applies only to specific task types
- It would benefit from code examples that may change
- Examples: Widget catalogs, API patterns, testing guides, detailed checklists

**Code examples are appropriate when:**
- They show concrete architectural violations (Wrong/Right tables)
- They document critical patterns that prevent common mistakes
- They're stable (won't change frequently)

</principles>

<required_patterns>

## Required Sections and Patterns

Every healed CLAUDE.md MUST include these patterns:

### 1. TL;DR Section (Top of File)

A dense 2-4 sentence paragraph capturing the most critical constraints. This gives Claude a scannable summary before the detailed sections.

```markdown
## TL;DR for Claude

Data flows UI → Provider → API—**never shortcut this**. Check `lib/common/widgets/`
before creating any widget. No file-private widgets—if it's big enough to be a widget,
it gets its own file. STOP and ask before: adding screens, changing schemas, modifying auth.
```

**Why**: LLMs process the beginning of context most reliably. Front-load critical constraints.

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

**Why**: Creates visual and semantic priority hierarchy. NEVER violations stand out from soft "Avoid" suggestions.

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

**Why**: Visual diagram is memorable. Warning creates a mental checkpoint.

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

**Why**: Explicit triggers eliminate judgment calls. Claude can pattern-match rather than interpret.

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

**Why**: Action-verb triggers ("Building", "Creating") match task mental models.

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

**Why**: Forces reflection. LLMs don't naturally self-verify—explicit prompts create checkpoints.

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

**Why**: Prevents eager generation. Creates explicit phases that can't be skipped. Encourages exploration and clarification before committing to implementation.

</required_patterns>

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

**Before adding anything, remove what doesn't belong:**

1. **Identify generic knowledge** Claude already has:
   - Universal language conventions (standard naming, formatting)
   - Framework best practices from official docs
   - Generic coding principles (error handling, validation)
   - Meta-statements that don't change behavior

2. **Apply the test**: For each item, ask "Would Claude do the wrong thing without this?"
   - If NO → Remove it (Claude knows this)
   - If YES → Keep it (project-specific)

3. **Check for duplication**: Is the same rule stated multiple times?
   - Keep ONE authoritative location
   - Exception: TL;DR can echo critical constraints for front-loading

**CHECKPOINT:** Before proceeding, present the removal list to the user:

```
I plan to REMOVE these items (Claude already knows them):
- [item 1] — [reason: generic framework knowledge]
- [item 2] — [reason: universal convention]
- [item 3] — [reason: meta-statement]

Confirm removals, or tell me which to keep?
```

Wait for user confirmation before proceeding to Phase 3. If user wants to keep specific items, note them and preserve in the final output.

## Phase 3: Apply Required Patterns

Transform the remaining content using each required pattern:

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

Check both pattern presence AND effectiveness qualities:

### Pattern Presence Checklist
- [ ] TL;DR section exists at top
- [ ] Tiered constraints (NEVER/YOU MUST/Avoid) structure
- [ ] Data flow diagram with warning
- [ ] If-then trigger table for "When to Ask"
- [ ] When to Read table with action verbs
- [ ] Self-check section with checklist
- [ ] Temporal markers in workflow (FIRST/THEN/ONLY THEN/FINALLY)

### Via Negativa Checklist
- [ ] No universal language conventions (Claude knows these)
- [ ] No generic framework best practices (Claude knows these)
- [ ] No meta-statements that don't change behavior
- [ ] No duplicate rules (single authoritative location)
- [ ] Every item passes the test: "Would Claude do wrong without this?"

### Effectiveness Qualities Checklist
- [ ] NEVER tier has concrete examples (not just abstract rules)
- [ ] "When to Ask" triggers are specific enough to pattern-match
- [ ] Strong modal verbs used (NEVER, MUST, STOP vs Avoid, Should, Consider)
- [ ] Critical patterns repeated in multiple forms (TL;DR + Constraints + Self-check)
- [ ] No vague language like "when appropriate" or "as needed"
- [ ] Decision criteria have explicit thresholds where applicable
- [ ] Workflow encourages exploration and clarification before execution
- [ ] NEVER tier includes "modifying unrelated code" constraint
- [ ] Avoid tier includes "over-engineering" constraint
- [ ] Workflow includes assumption-surfacing step before implementation

</process>

<output>

## Files Created/Modified

**Always:**
- `CLAUDE.md` - Transformed with required patterns, generic knowledge removed

**If content extracted:**
- `docs/guides/*.md` - Guide files with extracted detailed content

**User instruction after completion:**
```
CLAUDE.md has been optimized. Guide files created: [list files]

Please review the extracted guides and consider extending them with:
- Additional project-specific patterns from your codebase
- Code references to authoritative implementations
- Team conventions not captured in the original CLAUDE.md
```

</output>

<success_criteria>

## The healed CLAUDE.md succeeds when:

1. **Only project-specific knowledge** - Nothing Claude already knows from training data

2. **TL;DR captures critical constraints** - Reading only this paragraph gives Claude the most important rules

3. **Priority is visually obvious** - NEVER violations stand out from Avoid suggestions

4. **No judgment calls required** - Triggers are explicit enough that Claude can pattern-match

5. **Self-verification is prompted** - Checklist forces Claude to review before completing

6. **Sequence is enforced** - Temporal markers prevent skipping exploration/clarification phases

7. **Critical content is inline** - Anything used in 80%+ of tasks is directly in CLAUDE.md

8. **Reference material is accessible** - Detailed guides exist and are discoverable via "When to Read"

9. **Strong language throughout** - NEVER/MUST/STOP instead of Avoid/Should/Consider

</success_criteria>

<anti_patterns>

## What This Command Does NOT Do

- **Enforce arbitrary line counts** - Quality and effectiveness matter more than brevity
- **Remove all code examples** - Concrete Wrong/Right examples improve adherence
- **Create generic templates** - Each CLAUDE.md should reflect its project's actual constraints
- **Prescribe specific sections** - Beyond required patterns, structure should match project needs
- **Include generic knowledge** - If Claude knows it from training, it doesn't belong here

</anti_patterns>
