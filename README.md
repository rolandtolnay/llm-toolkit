# llm-toolkit

> A skills repository for Claude Code: commands, mental frameworks, and prompt engineering resources grounded in LLM research

## What This Is

A curated collection of slash commands, skills, decision-making frameworks, and reference guides that extend Claude Code. The toolkit covers three areas: automating common development workflows (commits, PRs, handoffs, verification), applying structured thinking to problems (12 mental frameworks), and writing effective LLM instructions (research-backed prompt quality principles).

Built for developers using Claude Code who want ready-made tools rather than building everything from scratch, and for LLM practitioners interested in the prompt engineering research that underpins the toolkit.

## What's Included

### Commands

Slash commands you invoke directly in Claude Code (e.g., `/verify-work`).

#### Workflow Commands

- **`/work-ticket`** — Fetch a Linear ticket, explore context, plan, implement, and commit.
  - Use when: starting work on an existing ticket.
- **`/verify-work`** — Check that changes satisfy the requirement using goal-backward analysis.
  - Use when: after implementing a feature or fix — catches gaps tests alone miss.
- **`/verify-refactor`** — Confirm a refactor preserves behavior and covers edge cases.
  - Use when: after restructuring code, before committing.
- **`/handoff`** — Generate a handoff doc with full context for a fresh session.
  - Use when: the conversation is long or you need to continue elsewhere.
- **`/work-report`** — Generate a time-tracked report from git commit history.
  - Use when: reporting work done during a period.
- **`/find-conversation`** — Search prior Claude Code conversations by description.
  - Use when: you need to locate a past discussion quickly.

#### Documentation Commands

- **`/generate-readme`** — Generate a README following proven developer communication patterns.
  - Use when: creating or rewriting a project README.
- **`/heal-docs`** — Restructure Markdown docs for effective LLM consumption.
  - Use when: optimizing reference docs, skills, or guides.
- **`/heal-claude-md`** — Apply priority hierarchy and self-verification patterns to CLAUDE.md files.
  - Use when: improving project instructions for Claude Code.
- **`/extract-pattern`** — Pull reusable patterns from project code into portable reference docs.
  - Use when: capturing implementation conventions as documentation.
- **`/prime-prompt-quality`** — Load the prompt quality guide into context.
  - Use when: before writing or reviewing prompts.

#### Mental Frameworks (`/consider:*`)

Twelve decision-making frameworks, each guiding you through a structured analysis. Use `/analyze-problem` to describe your situation and get a recommendation for which framework fits best.

- **`/consider:first-principles`** — Break a problem down to fundamentals and rebuild.
  - Use when: designing a new system or redesigning one from multiple inputs and constraints.
- **`/consider:5-whys`** — Drill to root cause by asking "why" repeatedly.
  - Use when: a bug keeps resurfacing or CI keeps breaking in different ways.
- **`/consider:inversion`** — Identify what would guarantee failure, then avoid it.
  - Use when: planning a migration, major refactor, or production rollout.
- **`/consider:second-order`** — Map consequences of consequences.
  - Use when: choosing between architectural approaches that both work today but diverge long-term.
- **`/consider:pareto`** — Apply the 80/20 rule to find highest-impact actions.
  - Use when: an audit surfaces many issues but you can only address a few.
- **`/consider:eisenhower-matrix`** — Sort tasks by urgency and importance.
  - Use when: sprint planning with a mix of bugs, tech debt, features, and infra work.
- **`/consider:10-10-10`** — Evaluate impact across three time horizons.
  - Use when: tempted to take a shortcut — hardcode a value, skip tests, merge without review.
- **`/consider:swot`** — Map strengths, weaknesses, opportunities, and threats.
  - Use when: evaluating whether to adopt a new framework, library, or tool.
- **`/consider:occams-razor`** — Find the explanation that fits all facts with fewest assumptions.
  - Use when: a bug has multiple plausible causes and you're tempted to chase the exotic one.
- **`/consider:one-thing`** — Identify the single highest-leverage action.
  - Use when: a large project has stalled with too many open threads.
- **`/consider:opportunity-cost`** — Analyze what you give up by choosing each option.
  - Use when: deciding between building in-house vs. using a third-party service.
- **`/consider:via-negativa`** — Improve by removing rather than adding.
  - Use when: a prompt, config, or module feels bloated but you're unsure what to cut.

### Linear Integration

A conversational interface to Linear, built as a Claude Code skill. Describe what you're working on and it handles the rest — creating tickets, assigning work, updating status, and querying issues without leaving your terminal.

What sets it apart from a basic API wrapper:

- **Effort and impact estimation** — infers priority (user impact) and estimate (implementation effort) from your description, calibrated for AI-assisted development
- **Project and label discovery** — fetches available projects and labels, matches them to your ticket's domain, and suggests assignments
- **Scope-change awareness** — when a comment or description update changes the scope of work, automatically re-evaluates priority and estimate

The skill activates when you mention creating tickets, updating issues, or checking assignments. Configure with a `.linear.json` in your project root and a `LINEAR_API_KEY` in `.claude/settings.local.json`.

### Skills

Modular capabilities with domain expertise, workflows, and templates. Claude Code activates these automatically based on what you're doing.

- **`create-slash-command`** — Generate slash command files with proper YAML frontmatter and structure.
  - Activates when: creating custom `/commands` for Claude Code.
- **`create-agent-skill`** — Produce SKILL.md files following the router pattern with workflows and references.
  - Activates when: building new skills for Claude Code.
- **`create-subagent`** — Configure subagent specs with tool restrictions and orchestration patterns.
  - Activates when: defining specialized agents for the Task tool.
- **`create-hook`** — Write hook configurations for PreToolUse, PostToolUse, and other events.
  - Activates when: adding event-driven automation or safety guardrails.
- **`create-prompt`** — Create standalone prompt files with effective instruction patterns.
  - Activates when: writing reusable prompts for any LLM task.
- **`audit-prompt`** — Check prompts for wasted tokens, poor positioning, and vague instructions.
  - Activates when: reviewing prompt quality before shipping.

### Reference Guides

- **`prompt-quality-guide.md`** — How LLMs process instructions: finite capacity, interference, positional bias, context depletion.
- **`docs/prompt-engineering-research-2025.md`** — Academic research on instruction-following capacity and degradation patterns.
- **`docs/readme-guide.md`** — Writing effective READMEs (the principles behind `/generate-readme`).
- **`docs/skill-description-guide.md`** — Writing YAML skill descriptions that Claude Code reliably discovers.
- **`docs/hooks-official-reference.md`** — Complete reference for the Claude Code hooks system.
- **`docs/skills-official-reference.md`** — Complete reference for the Claude Code skills system.

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

**Create a Linear ticket from a description:**

```
Users lose their draft when the app goes to background — save it to local storage
```

Claude infers priority (High — degraded core flow), estimate (S — 1-2 files, known approach), matches the right project and labels, asks you to confirm, and creates the ticket.

**Generate a README for a project:**

```
/generate-readme
```

Claude explores the codebase, asks clarifying questions, and produces a README following research-backed communication patterns.

## Not Included

This toolkit does not replace Claude Code's built-in capabilities. It does not provide general-purpose coding assistance, test generation, or CI/CD integration. The mental frameworks are thinking aids, not automated decision-makers — they structure your reasoning but require your judgment.

## License

[MIT](LICENSE)
