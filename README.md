# claude-code-toolkit

> A skills repository for Claude Code: commands, mental frameworks, and prompt engineering resources grounded in LLM research

## What This Is

A curated collection of slash commands, skills, decision-making frameworks, and reference guides that extend Claude Code. The toolkit covers three areas: automating common development workflows (commits, PRs, handoffs, verification), applying structured thinking to problems (12 mental frameworks), and writing effective LLM instructions (research-backed prompt quality principles).

Built for developers using Claude Code who want ready-made tools rather than building everything from scratch, and for LLM practitioners interested in the prompt engineering research that underpins the toolkit.

## What's Included

### Commands

Slash commands you invoke directly in Claude Code (e.g., `/verify-work`).

#### Workflow Commands

| Command | What it does | When to use it |
|---------|-------------|----------------|
| `/work-ticket` | Fetches a Linear ticket, explores context, plans, implements, and commits | Starting work on an existing ticket |
| `/verify-work` | Checks that code changes achieve requirements using goal-backward analysis | After implementing a feature or fix |
| `/verify-refactor` | Confirms refactored code preserves behavior and handles edge cases | After restructuring code |
| `/handoff` | Generates a handoff document with full context for a fresh session | When a conversation is getting long or you need to continue elsewhere |
| `/work-report` | Generates a time-tracked work report from git commit history | Reporting what you worked on during a period |
| `/find-conversation` | Searches previous Claude Code conversations by description | Locating a past conversation you need to revisit |

#### Documentation Commands

| Command | What it does | When to use it |
|---------|-------------|----------------|
| `/generate-readme` | Generates a README following proven developer communication patterns | Creating or rewriting a project README |
| `/heal-docs` | Restructures Markdown docs for effective LLM consumption | Optimizing reference docs, skills, or guides |
| `/heal-claude-md` | Applies priority hierarchy and self-verification patterns to CLAUDE.md files | Improving project instructions for Claude Code |
| `/extract-pattern` | Pulls reusable patterns from project code into portable reference docs | Capturing implementation conventions as documentation |
| `/prime-prompt-quality` | Loads the prompt quality guide into context | Before writing or reviewing prompts |

#### Mental Frameworks (`/consider:*`)

Twelve decision-making frameworks, each guiding you through a structured analysis.

| Framework | What it does | When to use it |
|-----------|-------------|----------------|
| `/consider:first-principles` | Breaks a problem down to fundamentals and rebuilds | Tackling something where conventional wisdom may be wrong |
| `/consider:5-whys` | Drills to root cause by asking "why" repeatedly | Debugging or diagnosing recurring issues |
| `/consider:inversion` | Identifies what would guarantee failure, then avoids it | Planning where risks are unclear |
| `/consider:second-order` | Maps consequences of consequences | Evaluating a decision with non-obvious downstream effects |
| `/consider:pareto` | Applies the 80/20 rule to find highest-impact actions | Prioritizing when everything feels important |
| `/consider:eisenhower-matrix` | Sorts tasks by urgency and importance | Managing a backlog or deciding what to work on next |
| `/consider:10-10-10` | Evaluates impact across three time horizons | Making a decision you'll need to live with |
| `/consider:swot` | Maps strengths, weaknesses, opportunities, and threats | Strategic planning or competitive analysis |
| `/consider:occams-razor` | Finds the explanation that fits all facts with fewest assumptions | Choosing between competing hypotheses |
| `/consider:one-thing` | Identifies the single highest-leverage action | When you're spread too thin |
| `/consider:opportunity-cost` | Analyzes what you give up by choosing each option | Comparing mutually exclusive alternatives |
| `/consider:via-negativa` | Improves by removing rather than adding | When complexity is the problem |

Use `/analyze-problem` to describe your situation and get a recommendation for which framework fits best.

### Skills

Modular capabilities with domain expertise, workflows, and templates. Claude Code activates these automatically based on what you're doing.

| Skill | What it does | When it activates |
|-------|-------------|-------------------|
| `create-slash-command` | Generates slash command files with proper YAML frontmatter and structure | Creating custom `/commands` for Claude Code |
| `create-agent-skill` | Produces SKILL.md files following the router pattern with workflows and references | Building new skills for Claude Code |
| `create-subagent` | Configures subagent specs with tool restrictions and orchestration patterns | Defining specialized agents for the Task tool |
| `create-hook` | Writes hook configurations for PreToolUse, PostToolUse, and other events | Adding event-driven automation or safety guardrails |
| `create-prompt` | Creates standalone prompt files with effective instruction patterns | Writing reusable prompts for any LLM task |
| `audit-prompt` | Checks prompts for wasted tokens, poor positioning, and vague instructions | Reviewing prompt quality before shipping |
| `linear` | Manages Linear issues through a conversational interface | Working with Linear tickets from Claude Code |

### Reference Guides

| Guide | What it covers |
|-------|---------------|
| `prompt-quality-guide.md` | How LLMs process instructions: finite capacity, interference, positional bias, context depletion |
| `docs/prompt-engineering-research-2025.md` | Academic research on instruction-following capacity and degradation patterns |
| `docs/readme-guide.md` | Writing effective READMEs (the principles behind `/generate-readme`) |
| `docs/skill-description-guide.md` | Writing YAML skill descriptions that Claude Code reliably discovers |
| `docs/hooks-official-reference.md` | Complete reference for the Claude Code hooks system |
| `docs/skills-official-reference.md` | Complete reference for the Claude Code skills system |

### How These Fit Together

A typical workflow might look like:

1. `/work-ticket` to pull in a Linear issue and plan the implementation
2. `/consider:first-principles` to think through the approach
3. Build the feature with Claude Code (skills like `create-hook` or `create-slash-command` activate as needed)
4. `/verify-work` to confirm the implementation meets the requirements
5. `/handoff` if you need to continue in a fresh session

The mental frameworks help you think; the workflow commands automate the routine parts; the skills provide domain expertise when you're building Claude Code extensions.

## Quick Start

Requires Node.js 16.7+ and [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

**Install globally** (available in all projects):

```bash
git clone https://github.com/rolandtolnay/llm-toolkit.git
cd llm-toolkit
node install.js --global
```

**Install locally** (scoped to one project):

```bash
git clone https://github.com/rolandtolnay/llm-toolkit.git
cd llm-toolkit
node install.js --local
```

<details>
<summary>Development setup (auto-updates with git pull)</summary>

```bash
git clone https://github.com/rolandtolnay/llm-toolkit.git
cd llm-toolkit
node install.js --global --link
```

This symlinks files into `~/.claude/` instead of copying them, so a `git pull` in the repo updates your installation automatically. Not supported on Windows.

</details>

After installation, open Claude Code and use any command (e.g., `/verify-work`) or start working on a task that matches a skill.

## Usage Examples

**Verify that your changes actually work:**

```
/verify-work
```

Claude reads your recent changes, traces them back to the original requirement, and reports whether the implementation achieves what was asked — catching gaps that tests alone miss.

**Pick the right mental framework for a decision:**

```
/analyze-problem
```

Describe your situation and Claude recommends which of the 12 frameworks fits best, then walks you through the analysis.

**Generate a README for a project:**

```
/generate-readme
```

Claude explores the codebase, asks clarifying questions, and produces a README following research-backed communication patterns.

## Not Included

This toolkit does not replace Claude Code's built-in capabilities. It does not provide general-purpose coding assistance, test generation, or CI/CD integration. The mental frameworks are thinking aids, not automated decision-makers — they structure your reasoning but require your judgment.

## License

[MIT](LICENSE)
