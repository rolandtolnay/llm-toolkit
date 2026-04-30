# Writing Effective CLAUDE.md Files

Reference for writing, auditing, and trimming CLAUDE.md files. Applies to new projects (start thin) and existing projects (cut to essentials).

## Core Premise

CLAUDE.md exists to correct behavior, not describe reality. If the model can discover it from the codebase, it doesn't belong in the file.

## Why Most CLAUDE.md Files Hurt Performance

- Models can follow ~150-200 instructions reliably. Claude Code's system prompt already uses ~50. Every instruction you add competes with all others.
- As instruction count increases, instruction-following quality degrades **uniformly** — not just for the new instructions, but for ALL of them.
- Research shows LLM-generated context files (e.g., `/init`) have a **negative effect** on task completion (-3%) and increase cost by 20%+.
- Developer-written files only improved performance by ~4% on average — and that includes well-maintained ones.
- Claude Code wraps CLAUDE.md content with a system reminder telling the model the context "may or may not be relevant" and to ignore it unless highly relevant. The more irrelevant content you include, the more likely Claude ignores the entire file.

## Guiding Principles

### 1. Only include what the model would otherwise get wrong

The model discovers project structure, tech stack, dependencies, and file locations through tooling (grep, glob, package.json, imports). It's trained on millions of codebases and is good at this.

**Include:** Invisible conventions, non-obvious tooling choices, consistent mistakes you've observed.
**Exclude:** Project structure, tech stack descriptions, dependency lists, architecture overviews, things discoverable from the code.

**Test:** For each line, ask: *"Would the model do the wrong thing without this — including in long sessions with heavy context?"* Models follow defaults reliably in short conversations but lose them as context grows. An instruction that seems redundant fresh may be load-bearing 50K tokens in. Test against realistic session conditions, not a clean slate.

### 2. Mention = bias, but negate observed failures

LLMs are autocomplete machines. Everything in context increases the probability of related output. Mentioning TRPC biases the model toward using TRPC. Saying "don't use X" makes X more salient than if you never mentioned it.

- Don't list technologies you want the model to avoid preemptively — just don't mention them
- If a legacy technology exists in the codebase, sequester it (rename folders, add `_legacy` suffix) rather than adding instructions about it

**Exception: observed failure modes.** If the model *actually keeps doing something wrong*, negating it paired with the correct alternative is high-value contrastive anchoring. The waste is negating things the model wasn't going to do. Negating things it demonstrably does wrong is one of the most effective instruction types.

```markdown
# Wasteful — model wasn't going to do this
Do NOT delete the database.

# Valuable — model keeps reaching for the wrong thing
Use Convex queries for data access, not TRPC — TRPC is legacy and limited to `src/legacy/`.
```

### 3. Every line must be universally applicable

CLAUDE.md loads into **every single session**. A line about database schema conventions is irrelevant when working on frontend components — and it degrades the model's attention to instructions that ARE relevant.

- If an instruction only applies to certain tasks, move it to a separate file and point to it (progressive disclosure)
- If an instruction only matters once, put it in the prompt instead

### 4. Prefer fixing the codebase over adding instructions

When the model consistently does something wrong, the instinct is to add a rule to CLAUDE.md. Instead, first ask: *Can I make the codebase steer the model correctly?*

- Model puts files in wrong location → reorganize directories to be self-evident
- Model uses wrong import patterns → add better type exports, barrel files
- Model skips type checking → add type checking to the test/build commands it already runs
- Model uses outdated API patterns → update or remove the outdated code

CLAUDE.md is a band-aid. Fixing the codebase is the cure.

### 5. Progressive disclosure over comprehensive instructions

Don't tell the model everything it could possibly need. Tell it **how to find** what it needs.

```markdown
## Task-Specific Guides
Read the relevant guide before starting work in these areas:
- Database migrations: `docs/migrations.md`
- API endpoint patterns: `docs/api-conventions.md`
- Test fixtures: `docs/testing.md`
```

This keeps the root CLAUDE.md thin while ensuring task-relevant detail is available when needed — and only when needed.

### 6. Be specific and imperative

Write direct commands, not descriptions. Specific instructions outperform vague ones. Point to exact files rather than describing patterns — this doubles as "pointers over copies" since code snippets go stale but file references stay current.

```markdown
# Vague and passive
API routes should generally follow existing patterns in the codebase.

# Specific and imperative
Follow the pattern in `src/app/api/users/route.ts` for new API routes.
```

### 7. Attach rationale to non-obvious instructions

A bare instruction tells the model *what*. Adding *why* lets it generalize to cases you didn't enumerate. The rationale must encode a causal chain the model wouldn't infer on its own — not just restate the instruction.

```markdown
# Bare instruction — model follows it but can't generalize
Use bun, not npm.

# With rationale — model also avoids yarn, pnpm without being told
Use bun, not npm — the bun lockfile is committed and CI depends on it.
Other package managers create conflicting lockfiles that break the build.
```

### 8. Position for attention

LLMs bias toward instructions at the **peripheries** — the beginning and end of the file. Instructions buried in the middle get the least attention.

- **Top of file:** Most critical constraints, verification commands, non-negotiable conventions
- **Middle:** Elaboration, progressive disclosure pointers (keep lean)
- **Bottom:** Reinforce whatever the model is most likely to forget or skip

If you have one instruction that matters more than all others, put it first AND last.

### 9. Never auto-generate, always curate

`/init` and auto-generation produce files full of information the model already found on its own — then feeds it back as instructions. This is circular and wasteful.

Write every line deliberately. If you can't justify why a specific line changes the model's behavior, remove it.

## What Belongs in CLAUDE.md

| Category | Example | Why it helps |
|---|---|---|
| Non-standard tooling with rationale | "Use `bun` not `npm` — bun lockfile is committed, other managers break CI" | Model defaults to npm; rationale lets it also avoid yarn/pnpm |
| Verification commands | "Run `make check` before finishing" | Model needs to know what to run, not how to find it each time |
| Conventions that contradict defaults | "Use `snake_case` for all DB columns" | Model defaults to camelCase in JS/TS ecosystems |
| Persistent gotchas | "The `auth` middleware must be the first in the chain" | Ordering constraints aren't self-evident from code |
| Strategic framing | "This project is greenfield — schema changes are fine" | Prevents over-cautious behavior around migrations |
| Observed failure correction | "Use Convex queries, not TRPC — TRPC is legacy in `src/legacy/`" | Contrastive anchoring: correct + wrong pattern together |
| Progressive disclosure pointers | "Read `docs/deploy.md` before any deployment work" | Keeps detail out of root file while ensuring access |

## What Does NOT Belong in CLAUDE.md

| Category | Why it hurts |
|---|---|
| Project structure / architecture overview | Discoverable via glob/grep. Goes stale. Biases model toward described structure even after refactors |
| Tech stack description | Discoverable from imports and config. Biases toward mentioned technologies |
| Code style guidelines | Use linters/formatters. Models match surrounding code patterns naturally |
| Dependency lists | In package.json / requirements.txt / go.mod already |
| Command listings from package.json | Model reads package.json on its own |
| Detailed data models | Discoverable from schema files. Goes stale quickly |
| Preemptive negations ("don't do X") for things the model wasn't doing | Activates the concept without benefit. Remove or rename the thing instead |
| Negations without the correct alternative | "Don't use TRPC" alone is weaker than "Use Convex, not TRPC — TRPC is legacy" |

## Applying the Principles

### New project, no CLAUDE.md yet

Start with nothing. Work with the agent for a few sessions. When you notice it **consistently** doing something wrong that you can't fix in the codebase, add a single targeted instruction. Expect the file to be 10-30 lines for most projects.

### Existing project, no CLAUDE.md

Don't write one preemptively. Start working with the agent and add instructions only as behavioral problems emerge. The model is likely to perform well with just the codebase.

### Existing project, bloated CLAUDE.md

Audit every line with the test: *"Would the model do the wrong thing without this?"*

1. **Delete** anything the model can discover (structure, stack, commands, patterns visible in code)
2. **Delete** style guidelines — configure a linter/formatter instead
3. **Delete** preemptive negations for things the model wasn't doing
4. **Rewrite** negations of *observed* failure modes: pair each with the correct alternative and rationale
5. **Move** task-specific instructions to separate files, replace with one-line pointers
6. **Keep** non-obvious conventions, verification commands, and strategic framing
7. **Add** rationale to surviving instructions where the "why" enables generalization
8. **Reorder** — most critical constraints first, progressive disclosure pointers in the middle, reinforcement of skip-prone instructions at the end
9. **Add** progressive disclosure pointers if important docs exist but aren't referenced

Target: under 60 lines for most projects. Under 30 is better.

### Ongoing maintenance

- When you add an instruction, try to delete one
- With each model upgrade, test with a stripped-down file — newer models need less steering
- Use the file diagnostically: instruct agents to flag surprises, then fix the codebase rather than adding more rules
- If an instruction has been in the file for months without being triggered, it's probably unnecessary
