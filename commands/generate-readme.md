---
description: Generate a high-quality README for a public GitHub project
argument-hint: [project-path]
---

<objective>
Generate a README.md for the project at `$ARGUMENTS` (or the current working directory if no path given).
</objective>

<readme-principles>
The README is a storefront, not a manual. It answers three questions in 30 seconds: What is this? Why should I care? How do I start? Everything else links out.

- **Show, don't claim.** Instead of "saves you hours," show a workflow that obviously saves time. Let the reader draw conclusions.
- **Progressive disclosure.** Front-load the most important information. Push complexity into later sections, collapsible blocks, or linked docs.
- **Scanability.** Short paragraphs (2-3 sentences max), headers as signposts, tables for comparisons, code blocks for anything executable.
- **The top 20% is the pitch.** Everything above installation should work as a standalone pitch. Everything below is reference material for people already convinced.
</readme-principles>

<tone>
Voice: senior engineer explaining their tool to a peer. Confident without boastful, specific without exhaustive.

**Do:** State facts and let value be obvious. Use second person, active voice. Be specific, not superlative. Acknowledge tradeoffs honestly.

**Don't:** Hype language ("Revolutionary AI-powered..."), vague benefits ("Improve your workflow"), condescending simplifiers ("Simply run...").

**Banned words:** "supercharge," "streamline," "empower," "leverage," "seamlessly," "simply," "just," "next-generation," "enterprise-grade," "cutting-edge"

**Preferred verbs:** "automate," "generate," "skip," "replace," "handle," "check," "run"

**Framing:** Describe what each tool *does* (verb-oriented), not what it *is* (noun-oriented). "Use this to..." not "This will make you..."

**Calibration:**
- Too informal: "Dude! This API is totally awesome!"
- Right: "This API lets you collect data about what your users like."
- Too formal: "The API documented by this page may enable the acquisition of information pertaining to user preferences."
</tone>

<formatting-rules>
**Tables vs lists vs prose:**
- Tables for comparing items with multiple attributes (features, commands, options)
- Bullet lists for enumerating items with one attribute each
- Prose only for narrative context (the "What This Is" section)

**Collapsible sections** (`<details>`) for content useful to <20% of readers: platform-specific installs, advanced config.

**Badges:** 3-5 max (build status, version, license).

**Code blocks:**
- No `$` prefix — prevents clean copy-paste
- One logical action per block so each is independently copy-pasteable
- State prerequisites before the install command, not after
- Use `bash` syntax highlighting

**Collections** (multiple tools/commands/features):
- Use three-column tables: Name | What it does | When to use it
- Group by use case, not alphabetically
- Add a "How These Fit Together" section showing how tools connect in a workflow
</formatting-rules>

<process>
1. **Explore the project**
   Launch parallel explore agents (Task tool, subagent_type=Explore) to investigate the codebase concurrently. Split exploration by concern:
   - **Agent 1 — Project identity:** Read manifest files (package.json, Cargo.toml, pubspec.yaml, pyproject.toml, go.mod, or equivalent). Identify name, description, dependencies, scripts, and installation mechanism.
   - **Agent 2 — Core functionality:** Scan top-level directory structure. Read entry points (main.*, index.*, lib.*), exported modules, and CLI definitions. Summarize what the project does and its key features.
   - **Agent 3 — Existing docs:** Read existing README.md (note content worth preserving: badges, links, license). Read any docs/ folder for additional context.

   From the exploration results, determine the project type: CLI tool, library, framework, collection of tools, web app, API, or other. Note primary language, ecosystem, and installation mechanism.

2. **Fill gaps with the user**
   Use AskUserQuestion to clarify anything exploration could not determine. Examples:
   - Target audience or primary use case if not obvious from the code
   - Preferred installation method when multiple are possible
   - Key features or selling points the user wants highlighted
   - Whether to include specific sections (Contributing, Configuration, etc.)
   - Any existing content from a previous README they want preserved or dropped

   Do not guess at project positioning or feature prioritization — ask.

3. **Draft the README using this skeleton** (include only sections that apply):

   ```
   # Project Name
   > One-line tagline: names the category and key differentiator

   ## What This Is
   2-3 sentences. What it does, who it's for, what problem it solves.

   ## Features / What's Included
   Scannable table or categorized list grouped by use case.
   For collections: Name | What it does | When to use it

   ## Quick Start
   Fastest path to working result. Copy-paste ready.
   No $ prefix in code blocks. One action per block.
   State prerequisites before install commands.

   ## Usage Examples
   2-3 concrete examples, simple to complex.

   ## Configuration (if needed)
   Only required config. Link out for advanced options.

   ## Contributing (if applicable)
   Brief guidance or link.

   ## License
   One line with link.
   ```

4. **Write the README.md file**
   - Write to `$ARGUMENTS/README.md` (or `./README.md` if no path)
   - If an existing README exists, show a summary of key changes and ask the user to confirm before overwriting
</process>

<success_criteria>
1. Honest scoping — mentions when NOT to use the tool if applicable
2. Features grouped by use case with "when to use it" context, not bare lists
3. Top 20% works as standalone pitch — answers what/why/how in 30 seconds
4. Tagline names category and key differentiator in one line
5. Quick start appears early — not buried below feature matrices or philosophy sections
6. No banned words appear anywhere in the output
7. Code blocks have no `$` prefix and are independently copy-pasteable
</success_criteria>
