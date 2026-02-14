# README Guide

Principles and patterns for writing effective README files for internal tool collections shared with engineering colleagues. Optimized for discoverability and adoption by people who already trust you, not for convincing strangers.

---

## Core Principles

1. **The README is a map, not a storefront.** It answers three questions in 30 seconds: What's here? What's relevant to me right now? How do I get started? Everything else links out.

2. **State benefits directly.** Your readers are colleagues, not skeptics. "This saves you from writing commit messages manually" is faster than making someone infer value from an example. Be explicit about what each tool does for them.

3. **Describe, don't dramatize.** There's a line between stating a benefit and dressing it up. "Automates commit messages" is direct. "Transforms your commit workflow" is performing. When you optimize every phrase for impact, you cross from helpful colleague into copywriter. Plain descriptions build more trust than polished ones.

4. **Write like a knowledgeable colleague.** Not a marketer, not a professor. Conversational, direct, technically precise, and respectful of the reader's time.

5. **Progressive disclosure.** Front-load the most important information. Push complexity into later sections, collapsible blocks, or linked docs.

6. **Situational triggers over feature descriptions.** Developers don't think "I want to use tool X." They think "I'm about to review a PR" or "I need to debug something." Map tools to the situations that trigger their use.

7. **Scanability is non-negotiable.** Engineers scan, they don't read. Short paragraphs (2-3 sentences max), headers as signposts, tables for comparisons, code blocks for anything executable.

8. **The top section is a navigation aid.** Everything above installation should orient the reader to what exists and help them find what's relevant. Everything below is detail for people who've located what they need.

9. **Installation is adoption.** If the install is friction-free, people use the tool. If it's not, they don't. Treat installation as co-primary with the overview — not an afterthought buried below a feature tour.

---

## Recommended Structure

```
# Project Name
> One-line tagline: names the category and key differentiator

## Prerequisites
Shared dependencies needed before anything else.
List tools, versions, and a one-liner install for each.

## What's Included
Scannable table grouped by situation/workflow.
Format: Name | What it does | When to reach for it
State the benefit of each tool directly.

## Quick Start / Install
Copy-paste ready. One block per action.
Fastest path to a working result.

## Workflows
How the tools combine in practice.
Organized by developer situation, not by tool.

## Usage Examples (if not covered above)
2-3 concrete examples progressing from simple to complex.

## Configuration / Setup (if needed)
Only what's required. Link to full docs for advanced config.

## Updating
How to get new versions.

## Contributing (if applicable)
Brief guidance or link to CONTRIBUTING.md.
```

### Structural Decisions

**Tables vs lists vs prose:**
- Tables for comparing items (features, commands, options with multiple attributes)
- Bullet lists for enumerating items with one attribute each
- Prose only for narrative context (the "What This Is" section)

**Collapsible sections** (`<details>`) for:
- Platform-specific installation variants
- Advanced configuration
- Anything useful to 20% of readers but noise for the other 80%

---

## Tone Guidelines

### Target Voice

Senior engineer explaining their tool to a peer. Confident without being boastful, specific without being exhaustive.

### Do

| Principle | Example |
|-----------|---------|
| State benefits directly | "Automates commit messages so you skip writing them by hand." |
| Describe plainly, don't dramatize | "Slash commands for verifying code" not "Slash commands that verify your code actually works" |
| Use second person, active voice | "Run the command to install the skill into your project." |
| Be specific, not superlative | "Reduces boilerplate by eliminating manual model mapping." |
| Acknowledge tradeoffs honestly | "Optimized for speed over flexibility — if you need custom X, see alternatives." |
| Show personality through brevity | "No config files. No build step. Just works." |

### Don't

| Anti-pattern | Example | Why it fails |
|--------------|---------|--------------|
| Hype language | "Revolutionary AI-powered developer experience!" | Triggers immediate skepticism |
| Vague benefits | "Improve your workflow and boost productivity" | Says nothing concrete |
| Condescending simplifiers | "Simply run the command" / "It's easy" | Implies the reader is foolish if they struggle |
| Overly formal | "The aforementioned utility enables acquisition of..." | Creates distance, wastes time |
| Excessive punctuation | "Check out these amazing features!!!" | Reads as desperate |
| Implicit-only value | Showing an example without stating what it saves you | Makes the reader do inference work your sentence could do |
| Dramatized descriptions | "Transforms your commit workflow" / "Turns plain English into structured tickets" | Reads as polished rather than honest — plain description builds more trust |

### Word Choice

**Avoid:** "supercharge," "streamline," "empower," "leverage," "seamlessly," "next-generation," "enterprise-grade," "cutting-edge"

**Prefer:** "automate," "generate," "skip," "replace," "handle," "check," "run"

**Framing:** Describe what each tool *does* (verb-oriented), not what it *is* (noun-oriented). Frame around developer agency: "Use this to..." not "This will make you..."

### The Google Calibration Test

- Too informal: "Dude! This API is totally awesome!"
- Just right: "This API lets you collect data about what your users like."
- Too formal: "The API documented by this page may enable the acquisition of information pertaining to user preferences."

---

## Prerequisites Section

When multiple tools share common dependencies, document them once at the top rather than repeating per-tool.

```markdown
## Prerequisites

Before installing anything, make sure you have:

- **UV** — Python package manager. Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node 20+** — `brew install node` or use your preferred version manager
```

This removes the most common adoption blocker upfront. A reader who hits a dependency error during installation will abandon the process. Catching this first prevents that.

---

## Installation Section

### Formatting Rules

- **No `$` prefix** in code blocks — prevents clean copy-paste.
- **One logical action per code block** so each block is independently copy-pasteable.
- **State prerequisites before the install command**, not after.
- Use `bash` syntax highlighting on fenced code blocks.

### Multiple Installation Paths

Present from most common to most specialized. Use clear headers and explain when to use each:

```markdown
### Quick Install (recommended)

One-liner description of what this does.

\```bash
curl -fsSL https://example.com/install.sh | bash
\```

### Via Homebrew

\```bash
brew install toolname
\```

### Manual Installation

<details>
<summary>Click to expand</summary>

Step-by-step for edge cases...

</details>
```

### Scoped Installation (User vs Project)

When the tool supports different scopes, explain the tradeoff upfront:

```markdown
**User scope** — available across all your projects, only on your machine.

\```bash
install-command --user
\```

**Project scope** — shared with your team via version control.

\```bash
install-command --project
\```
```

### Symlinks vs Copies

- **Symlinks** for personal/user scope: auto-update when the source changes
- **Copies** for shared/project scope: won't break for other team members, but need manual re-copy to update

Note the tradeoff explicitly so users understand why each approach is used.

---

## Presenting Collections

When the README covers multiple tools, commands, or features, discoverability is the main challenge. The reader needs to scan the collection and find the 1-2 things relevant to their current need.

### Use Three-Column Tables

```markdown
| Tool | What it does | When to reach for it |
|------|-------------|----------------------|
| `tool-a` | Verb-first description + explicit benefit | Concrete trigger scenario |
| `tool-b` | Verb-first description + explicit benefit | Concrete trigger scenario |
```

The "When to reach for it" column is what makes a collection useful. Without it, the reader has to read each tool's full documentation to know if it's relevant.

State the benefit in the description column. Not "Analyzes code" but "Catches structural issues before they reach code review."

### Group by Situation

Don't alphabetize — group by the *developer situation* that triggers use. A developer looking for "something to help with code review" will scan category headers, not an alphabetical list.

```markdown
### Writing Code
| Tool | ... | ... |

### Reviewing Code
| Tool | ... | ... |

### Debugging
| Tool | ... | ... |
```

### Show How Tools Compose

After listing the tools, show how they chain together in real workflows. This turns a list of independent tools into a coherent system.

```markdown
## Workflows

**Implementing a feature:**
1. Use `plan` to break down the ticket
2. Build the feature
3. Run `review` to catch issues before pushing
4. Run `commit` to generate a commit message

**Debugging a production issue:**
1. Run `debug` to start a structured investigation
2. Use `research:deep-dive` if you need to understand unfamiliar code
3. Fix and run `verify-work` to confirm the fix holds
```

Workflow sections are the highest-value content in a collection README. They transform "here are some tools" into "here is how your day gets better."

---

## Common Pitfalls

1. **Wall of text at the top.** If the first three paragraphs are prose, most readers are gone. Lead with a one-liner, then a table or code block.

2. **Feature lists without context.** "Supports X, Y, Z" means nothing without showing when and why to use each. Pair features with situational triggers.

3. **Making the reader infer value.** Internal colleagues trust direct statements. "This automates X so you don't have to do Y" is more respectful of their time than an example they have to decode.

4. **Burying the quick start.** If the reader scrolls past a table of contents, feature matrix, philosophy section, and architecture diagram before finding how to install, the README has failed.

5. **Using "simply" or "just."** These words imply the step is trivial. If it were, the reader wouldn't need documentation. Drop them entirely.

6. **Stale content.** Outdated installation commands or broken links erode trust faster than anything. Keep installation instructions tested.

7. **Marketing language.** Developers have finely tuned BS detectors. State what the tool does concretely.

8. **Not saying when NOT to use it.** Honest scoping builds trust. "If you need X, check out Y" makes people trust your recommendations for when your tool *is* appropriate.

9. **Listing tools without showing composition.** A collection of independent tools is less compelling than a system of tools that work together. Always show workflows.

10. **Missing prerequisites.** A reader who hits a dependency error during installation will abandon the process. Document shared dependencies once at the top.
