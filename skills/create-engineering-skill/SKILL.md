---
name: create-engineering-skill
description: Create engineering skills that activate canonical software vocabulary. Use when building a new skill for debugging, testing, architecture, or code review — encoding expert judgment as falsifiable rules.
---

<essential_principles>

Engineering skills activate knowledge the LLM already has. Frontier models have read Ousterhout, Feathers, Evans, Fowler, Hunt & Thomas, Beck, and Brooks. Using the right term — "deep module," "seam," "tracer bullet" — doesn't explain a concept; it activates a web of associated knowledge from training data. One canonical term replaces paragraphs of description.

The skill author's job:
1. Identify which canonical concepts address the engineering problem
2. Extract the vocabulary that activates those concepts
3. Compress experienced judgment into falsifiable rules

Engineering skills are sparse, direct, and vocabulary-dense. They read like instructions from a senior engineer who assumes shared context — because the LLM has read the same books.

</essential_principles>

<process>

## Step 1: Capture the Engineering Problem Space

Identify what the skill addresses. Engineering skills target one of:
- A **failure mode** — something that goes wrong repeatedly (AI produces shallow modules, tests are brittle, debugging spirals)
- A **practice** — a proven technique applied consistently (TDD, interface-first design, architecture refactoring)
- A **workflow** — a multi-step engineering process that benefits from structure (diagnosis, code review, migration planning)

Determine:
- "What goes wrong without this skill?" (the failure mode it prevents)
- "What does good look like?" (the outcome it produces)
- "When should the LLM reach for this?" (the trigger condition)

If the user has been working on something in conversation, extract these answers from context. Otherwise, use AskUserQuestion:
- header: "Skill target"
- question: "What engineering problem should this skill address?"
- options:
  - "Prevent a failure mode" — something keeps going wrong
  - "Encode a practice" — a technique I want applied consistently
  - "Structure a workflow" — a multi-step process that needs guardrails

**Output:** A 1-2 sentence statement of the engineering problem and the outcome.

### Convergence test

Before moving on, verify a shared design concept exists between you and the user. Describe a concrete scenario where the skill would intervene — what the user says, what the LLM does, what the output looks like. Ask the user: "Is this what you had in mind?"

If the scenario surprises them, you don't share a design concept yet. Iterate until the scenario matches their mental model. This is cheap now and expensive to fix after drafting.

## Step 2: Identify Canonical Grounding

Read `references/canonical-sources.md`.

Find the canonical sources that address this engineering problem. Look for:
- **Named concepts** that map directly to the problem ("software entropy" for code degradation, "deep modules" for interface design)
- **Named anti-patterns** that describe the failure mode ("horizontal slicing," "shallow modules," "big ball of mud")
- **Named practices** that encode the solution ("red-green-refactor," "tracer bullets," "design it twice")

Present to the user:
"Here's the canonical grounding I'd use:
- [Concept] from [Author/Book] — [why it applies]
- [Anti-pattern] — [the failure mode it names]

Does this match your mental model? Any sources I'm missing?"

If the user references unfamiliar sources, ask them to describe the key ideas — then integrate using the same vocabulary activation pattern.

**Output:** 2-5 canonical concepts with source and relevance.

### Complexity gate

Assess whether the skill needs the full treatment or a minimal draft:

**Minimal** when: 1-2 canonical concepts cover the problem, no multi-step process, single intent. Draft directly — essential principles + success criteria, skip vocabulary tables and judgment compression steps. (Pocock's `zoom-out` is 2 lines. Not every skill needs reference files.)

**Full** when: 3+ concepts, multi-step workflow, judgment calls that need compression, or the skill touches architecture/planning/domain modeling.

If minimal, skip to Step 5 with just the canonical concepts from this step as your grounding.

## Step 3: Extract Activation Vocabulary

Read `references/vocabulary-activation.md`.

From the canonical sources, extract terms that form the skill's native language. For each term:

1. **Canonical form** — the exact term as used in the source ("seam," not "injection point")
2. **Rejected framings** — synonyms to avoid (prevents vocabulary drift)
3. **Activation test** — does the LLM produce meaningfully different behavior when this term is used vs. plain-language? If not, it's not earning its place.

Target: 3-8 terms per skill.

Present as a compact table:

| Term | Source | Rejected framings |
|------|--------|-------------------|
| deep module | Ousterhout | "component," "service" |
| seam | Feathers | "boundary," "injection point" |

## Step 4: Compress Judgment into Rules

Read `references/judgment-compression.md`.

Identify judgment calls the skill needs to make — places where an experienced engineer would "just know." For each:

1. Convert to a **falsifiable criterion** — "If [condition], then [action]" or a multi-criteria gate
2. Name the **anti-pattern** it prevents
3. Pair with the **correct pattern** (contrastive anchoring)

Examples:
- "Use good judgment about test scope" → "Test at the public interface of each deep module. Mock only at system boundaries — network, filesystem, clock."
- "Know when to write an ADR" → "Write an ADR only when all three hold: hard to reverse, surprising without context, genuine trade-off with a runner-up."

## Step 5: Draft the Skill

Read `references/gpt55-tuning.md` before writing.

### Writing the body

**Structure:**
- Open with the engineering problem and outcome (1-2 sentences)
- `<essential_principles>` for concepts that apply on every execution path (3-5 items max)
- Numbered steps for the process
- XML tags for major boundaries (`<process>`, `<success_criteria>`)
- Markdown within tags for substeps and lists

**Language:**
- Imperative voice. "Test at the seam." Not "You should consider testing at the seam."
- Canonical vocabulary as native language. "Identify the seams" not "what Feathers calls 'seams.'"
- Name anti-patterns directly. "This prevents horizontal slicing" not "this prevents doing too much at once."
- Zero hedging, zero filler. Every sentence either gives an instruction or a falsifiable criterion.
- Sparse prose, dense structure. ~3:1 ratio of structural elements to prose.

**GPT-5.5 tuning:**
- Outcome-first: define what good looks like, then constrain how to get there
- Decision rules over absolutes: "prefer X when Y" over "ALWAYS X"
- No chain-of-thought instructions — the model reasons internally
- Explicit stopping conditions for iterative processes

**What NOT to include:**
- Explanations of canonical concepts (vocabulary activates that knowledge)
- Motivational language ("thoroughness matters")
- Negations of unlikely behaviors
- Step-by-step reasoning instructions

### Deciding structure

Default to simple (single SKILL.md).

**Simple** when: single workflow, under 200 lines, one primary intent.

**Complex** (any one triggers): multiple distinct intents, large domain knowledge (>300 lines would bloat SKILL.md), reusable scripts, expected scope growth.

Complex layout:
```
skill-name/
├── SKILL.md        # under 500 lines
├── references/     # domain knowledge, lazy-loaded from process steps
└── scripts/        # standalone executables (only if needed)
```

Only create directories that earn their place. References one level deep from SKILL.md.

### Deciding scope

- **User scope** (`~/.claude/skills/<name>/`) — general-purpose skills useful across projects
- **Project scope** (`.claude/skills/<name>/`) — skills tied to this project's tooling, APIs, or domain

If ambiguous, ask the user.

### Writing the frontmatter

Write the frontmatter LAST, after the body is complete.

**name:**
- kebab-case, matches directory name, max 64 chars
- No "claude" or "anthropic" (reserved)

**description:** Read `references/skill-description-guide.md` and apply its principles.

**Optional fields** — set only what's needed:
- `disable-model-invocation: true` — user-only invocation (for dangerous workflows)
- `allowed-tools` — restrict tool access
- `context: fork` — run in a subagent
- `argument-hint` — autocomplete hint, e.g. `[issue-number]`

### Domain language integration

Decide whether the created skill should read or write a project glossary (e.g. `CONTEXT.md`). Skills that touch architecture, planning, or domain modeling should:
- Read the project's domain glossary as a first action (terms inform module names, seam locations, interface vocabulary)
- Update the glossary inline when new concepts emerge during execution (same discipline as Pocock's `grill-with-docs`)

Skills that are purely procedural (TDD cycle, diagnosis loop) typically don't need glossary integration — canonical vocabulary from the skill itself is sufficient.

If the skill needs glossary integration, add explicit instructions. Example for a created skill:

```
Read CONTEXT.md (if it exists) before exploring the codebase. When a new
domain concept emerges during execution, add it to CONTEXT.md immediately
— don't batch updates. Create the file lazily if it doesn't exist.
```

### Cross-skill composition

Map the new skill's relationships to other skills:
- **Feeds from:** Does another skill or workflow produce the input this skill expects? (e.g., a grilling session produces a plan that `to-issues` breaks down)
- **Hands off to:** Does this skill reach a point where a different skill takes over? (e.g., `diagnose` hands off to `improve-codebase-architecture` after a fix)
- **Shares vocabulary with:** Do other skills use the same domain glossary or canonical terms?

If relationships exist, add them as handoff instructions in the skill body — "After [condition], recommend [other skill] with [context to pass]." If no relationships exist, move on.

### Writing the skill file(s)

Write the SKILL.md and any supporting files. Ensure all referenced files exist.

## Step 6: Validate

Run through every item in the `<success_criteria>` block below. Fix any failures before presenting to the user.

Present the completed skill with a summary of the canonical grounding used.

## Step 7: Testing Guidance

After presenting the skill, provide testing guidance:

**Two invocation methods:**
1. **Auto-trigger:** Ask something matching the description (tests description quality)
2. **Direct:** Use `/skill-name` (tests body instructions)

**What to check:**
1. Does it trigger when it should? (description test)
2. Does Claude follow the instructions? (body test)
3. Is output quality good? (end-to-end test)

**Description debugging:** Ask Claude "When would you use the [skill-name] skill?" — it quotes the description back, revealing matching gaps.

**Common iterations:**
- **Undertriggering:** Add keywords to description, be more pushy about triggers
- **Overtriggering:** Add "Do NOT use when..." clause, be more specific
- **Instructions not followed:** Check positioning (critical items at start/end), reduce verbosity, add examples

</process>

<success_criteria>

**Process gates (highest skip risk):**
- [ ] Convergence test passed — user confirmed the scenario matches their mental model
- [ ] Domain language integration decided (read/write glossary, or explicitly skipped)
- [ ] Cross-skill relationships mapped (handoffs added, or no relationships)

**Engineering grounding:**
- [ ] References 2+ canonical sources by vocabulary, not citation
- [ ] Rejected framings listed for key terms (if full treatment)
- [ ] Judgment calls converted to falsifiable criteria, not vague directives
- [ ] Anti-patterns named and paired with correct patterns
- [ ] No concept explanations that duplicate what the LLM already knows

**Skill structure:**
- [ ] name: kebab-case, matches directory, max 64 chars, no reserved words
- [ ] description: 25-35 words, distinct verb, "Use when" clause, user vocabulary, no XML tags
- [ ] Description written LAST, after body is complete
- [ ] SKILL.md under 500 lines
- [ ] References one level deep, all referenced files exist
- [ ] Optional frontmatter fields set only when needed

**Prompt quality:**
- [ ] Imperative voice throughout
- [ ] Zero motivational filler
- [ ] No negations of unlikely behaviors
- [ ] Success criteria ordered by skip risk
- [ ] References lazy-loaded from process steps

**GPT-5.5 readiness:**
- [ ] Outcome-first framing
- [ ] Decision rules, not absolutes (except true invariants)
- [ ] No redundant reasoning instructions
- [ ] Explicit stopping conditions

**Completion:**
- [ ] Testing guidance provided after presenting the skill

</success_criteria>
