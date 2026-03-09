# Prompt Principles for Skill Authoring

Distilled principles that directly affect skill quality. Skills are prompts — these apply.

<finite_capacity>
## Finite Instruction Capacity

LLMs follow ~150-250 behavioral instructions with reasonable consistency. Each instruction dilutes all others. Not all content interferes equally:

- **Behavioral instructions** ("do X"): High interference — each competes with all others
- **Reference data** (schemas, examples): Low interference when task-relevant
- **Structural markers** (XML tags, headers): Low interference, net positive
- **Motivational fluff** ("this is important"): Pure waste — no behavioral change
- **Corrective rationale** ("never X — because Y"): Earns its place when it encodes a causal chain the LLM wouldn't infer alone

Every instruction must earn its place through measurable behavioral change, not theoretical correctness.
</finite_capacity>

<positional_bias>
## Positional Attention Bias

Beginning and end of a prompt are attention hotspots. The middle is a trough.

- **Beginning:** Objective, critical constraints, essential context
- **Middle:** Process details (keep lean)
- **End:** Success criteria, ordered by skip risk (highest first)

Restating a critical instruction at the end is peripheral reinforcement, not redundancy.
</positional_bias>

<context_budget>
## Context Is Depletable

| Context usage | Quality |
|---|---|
| 0-30% | Peak |
| 30-50% | Good |
| 50-70% | Degrading |
| 70%+ | Poor |

Shorter prompts leave more room for the LLM's work. When two approaches produce equivalent results, choose the one consuming less context.
</context_budget>

<value_test>
## Value = Behavioral Overrides

For every instruction, ask: "If I remove this, does output get worse?"

- If removing it changes nothing: it wastes budget
- If removing it causes failures: it earns its place

Test empirically, not theoretically. "The LLM should know this" is irrelevant if it doesn't reliably act on it.
</value_test>

<specificity>
## Specificity Over Abstraction

"Return JSON with fields `name` (string) and `age` (integer)" beats "return structured data." Concrete examples anchor abstract rules and reduce valid interpretations.
</specificity>

<contrastive>
## Contrastive Anchoring

Patterns + anti-patterns work together. Anti-patterns aren't wasted negation — they clarify the right pattern through contrast.

Only negate **observed failure modes** (things the LLM actually does wrong). Negating unlikely behaviors activates the concept without benefit.
</contrastive>

<progressive_disclosure>
## Progressive Disclosure

- **Eager loading:** Content present from the start. Use for content needed on every execution path.
- **Lazy loading:** Content fetched during execution when a condition is met. Use for conditional references.

Default to lazy. Promote to eager only when essential regardless of path.
</progressive_disclosure>

<voice>
## Imperative Voice

"Create the file" not "the file should be created." Imperative sentences are shorter, less ambiguous, and map directly to actions.
</voice>

<no_filler>
## No Filler

No "Let me", "Simply", "Basically", "I'd be happy to." Direct instructions and factual statements only.
</no_filler>

<specificity_matching>
## Match Specificity to Fragility

- **Fragile operations** (migrations, payments, deployments): Exact instructions, low freedom
- **Creative operations** (reviews, analysis, writing): Principles and freedom
</specificity_matching>

<xml_partitioning>
## XML Structural Partitioning

Use XML tags to separate content types (`<process>`, `<examples>`, `<success_criteria>`). Works better than language-level directives for managing interference. Use markdown within tags where natural.

Recommended by all major providers (Anthropic, OpenAI, Google).
</xml_partitioning>

<start_minimal>
## Start Minimal, Add for Failures

Begin with fewest instructions on best model. Add only when you observe a specific failure mode. Over-specification can backfire — reasoning models handle decomposition internally.
</start_minimal>

---

## Common Waste vs Common Value

| Waste | Value |
|---|---|
| "Thoroughness is more important than speed" | `uv run script.py get $ARGUMENTS` (undiscoverable reference) |
| "Do NOT delete the database" (unlikely) | "Read files yourself, don't rely on summaries" (observed tendency) |
| "File was read successfully" (never skipped) | "Do NOT combine steps 3 and 4" (verified failure mode) |
| "IMPORTANT: You must always ensure that..." | Right pattern paired with wrong pattern (contrast) |
| "Simply", "Basically" (filler) | "Format as plain text — output feeds a TTS engine" (corrective rationale) |
