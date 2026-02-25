---
name: readme-best-practices
description: Apply consistent structure, tone, and formatting to README.md files. Use when drafting, rewriting, or reviewing a project README to make it scannable and developer-friendly.
---

<objective>
Principles and patterns for writing effective README files for developer-facing projects. A README answers three questions in 30 seconds: What is this? Why should I care? How do I start? It is a storefront, not a manual — everything else links out.
</objective>

<essential_principles>

**Show, don't claim.** Developers distrust vague promises. Instead of "saves you hours" or "improves your workflow," show the tool doing something useful in three lines. The value should be self-evident — let the reader draw their own conclusions.

**Progressive disclosure.** Front-load the most important information. Push complexity into later sections, collapsible blocks, or linked docs.

**Scanability is non-negotiable.** Engineers scan, they don't read. Short paragraphs (2-3 sentences max), headers as signposts, code blocks for anything executable.

**The top 20% is the pitch.** Everything above the installation section should work as a standalone pitch. Everything below is reference material for people already convinced.
</essential_principles>

<readme_skeleton>
Include only sections that apply. This is the order — do not rearrange.

```
# Project Name
> One-line tagline: names the category and key differentiator

## What This Is
2-3 sentences. What it does, who it's for, what problem it solves.

## Features / What's Included
Scannable list or table grouped by use case.
Each item: verb-first description + "Use when:" trigger scenario.

## Quick Start
Fastest path to a working result. Copy-paste ready.

## Usage Examples
2-3 concrete examples, simple to complex.
Each example should reveal something new — don't repeat patterns.

## Configuration (if needed)
Only required config. Link out for advanced options.

## Updating
How to get new versions.

## Contributing (if applicable)
Brief guidance or link to CONTRIBUTING.md.

## License
One line with link.
```
</readme_skeleton>

<tone_and_language>

**Voice:** Senior engineer explaining their tool to a peer. Confident without boastful, specific without exhaustive.

**Do:**
- State facts, let value be obvious: "Generates type-safe API clients from OpenAPI specs in under 5 seconds."
- Use second person, active voice: "Run the command to install."
- Be specific, not superlative: "Reduces boilerplate by eliminating manual model mapping."
- Acknowledge tradeoffs: "Optimized for speed over flexibility — if you need custom X, see alternatives."
- Show personality through brevity: "No config files. No build step. Just works."

**Don't:**
- Hype language: "Revolutionary AI-powered developer experience!" — triggers immediate skepticism
- Vague benefits: "Improve your workflow and boost productivity" — says nothing concrete
- Condescending simplifiers: "Simply run..." / "It's easy" — implies the reader is foolish if they struggle
- Overly formal: "The aforementioned utility enables acquisition of..." — creates distance, wastes time

**Banned words:** "supercharge," "streamline," "empower," "leverage," "seamlessly," "simply," "just," "next-generation," "enterprise-grade," "cutting-edge" — "simply" and "just" imply the step is trivial; if it were, the reader wouldn't need documentation. Also watch for equivalent phrases ("all you need to do is…", "it's easy to…").

**Preferred verbs:** "automate," "generate," "skip," "replace," "handle," "check," "run"

**Framing:** Describe what each tool *does* (verb-oriented), not what it *is* (noun-oriented). "Use this to..." not "This will make you..."

**Calibration test:**
- Too informal: "Dude! This API is totally awesome!"
- Right: "This API lets you collect data about what your users like."
- Too formal: "The API documented by this page may enable the acquisition of information pertaining to user preferences."
</tone_and_language>

<formatting_rules>

**Tables vs lists vs prose:**
- Tables for comparing items with short, uniform attributes (~30 chars per cell). If content wraps on GitHub, switch to bullet lists.
- Bullet lists for everything else, including collections with longer descriptions.
- Prose only for narrative context (the "What This Is" section).

**Collapsible sections** (`<details>`) for content useful to <20% of readers: platform-specific installs, advanced config, edge case behaviors.

**Badges:** 3-5 max (build status, version, license). More signals insecurity, not quality.

**Code blocks:**
- No `$` prefix — prevents clean copy-paste.
- One logical action per block so each is independently copy-pasteable.
- State prerequisites before the install command, not after.
- Use `bash` syntax highlighting on fenced code blocks.

**Collections** (multiple tools/commands/features):
- Group by use case, not alphabetically.
- Format each item as:
  ```
  - **`name`** — Verb-first description of what it does.
    - Use when: short trigger scenario that helps the reader recognize relevance.
  ```
- Add a "How These Fit Together" section only when it reveals non-obvious connections. If you'd just be listing tools in order, cut it.

**Installation paths:**
- Present from most common to most specialized.
- Use clear headers and explain when to use each.
- Put rare methods in `<details>` blocks.
- When scoped install exists (user vs project), explain the tradeoff upfront:

  ```
  **User scope** — available across all your projects, only on your machine.
  **Project scope** — shared with your team via version control.
  ```
</formatting_rules>

<common_pitfalls>

1. **Wall of text at the top.** If the first three paragraphs are prose, most readers are gone. Lead with a one-liner, then a code block or table.

2. **Feature lists without context.** "Supports X, Y, Z" means nothing without showing when and why to use each. Pair features with use cases.

3. **Assuming the reader already cares.** Answer "why should I use this?" before "how do I use this?" If the reader scrolls past a ToC, feature matrix, and architecture diagram before finding how to install, the README has failed.

4. **Stale content.** Outdated installation commands or broken links erode trust faster than anything. Keep installation instructions tested.

5. **Not saying when NOT to use it.** Honest scoping builds trust. "If you need X, check out Y" makes people trust your recommendations for when your tool *is* appropriate.

6. **Documenting the self-evident.** Don't tell users `--help` exists or that they can read the source code. Every line should earn its place.

7. **Usage examples that repeat patterns.** Three examples showing different interaction styles are better than four where the last repeats the third. Each example should reveal something new.

8. **No subtraction pass.** After writing, re-read and ask "does removing this lose information?" for every section. Workflow sections, closing summaries, and scope sections often restate what's already covered.
</common_pitfalls>

<process>

1. **Explore the project**
   Investigate the codebase to understand: project name, what it does, who it's for, primary language/ecosystem, installation mechanism, key features, and existing documentation. Read manifest files, entry points, CLI definitions, and any existing README.

2. **Identify the project type**
   Determine: CLI tool, library, framework, collection of tools, web app, API, or other. This affects structure — collections need "What's Included" tables, single tools need "Features" lists.

3. **Fill gaps with the user**
   Clarify anything exploration could not determine: target audience, preferred installation method, features to highlight, sections to include/exclude, existing content to preserve or drop.

4. **Draft the README using the skeleton**
   Apply the structure from `<readme_skeleton>`. Include only sections that apply. Write the tagline first — it forces you to name the category and differentiator in one line.

5. **Subtraction pass**
   Re-read every section and ask "does removing this lose information?" Cut workflow sections that restate individual item descriptions. Cut scope sections that repeat the tagline. Cut closing summaries.

6. **Write the file**
   If an existing README exists, show a summary of key changes and confirm before overwriting.
</process>

<success_criteria>
README writing is complete when:
- [ ] Subtraction pass completed — no section restates content from another section
- [ ] Tagline names category and key differentiator in one line
- [ ] Top 20% works as standalone pitch — answers what/why/how in 30 seconds, quick start not buried
- [ ] Features grouped by use case with "Use when:" context, not bare lists
- [ ] Honest scoping — mentions when NOT to use the tool if applicable
- [ ] No banned words appear anywhere in the output
- [ ] Code blocks have no `$` prefix and are independently copy-pasteable
</success_criteria>
