<div align="center">

# llm-toolkit

**Slash commands, skills, and decision frameworks for Claude Code.**

```bash
git clone https://github.com/rolandtolnay/llm-toolkit.git ~/toolkits/llm-toolkit
cd your-project && ~/toolkits/llm-toolkit/install.js
```

[What's included](#whats-included) · [Quick start](#quick-start) · [Usage examples](#usage-examples) · [Reference guides](#reference-guides)

</div>

---

## What this is

Slash commands, auto-activating skills, and reference guides for Claude Code. Workflow automation (commits, verification, handoffs), 12 mental frameworks for structured decisions, and guides for writing better prompts.

---

## What's included

### Commands

Slash commands you invoke directly in Claude Code (e.g., `/verify-work`).

#### Workflow

```
/work-ticket
```

Fetch a Linear ticket, explore context, plan, implement, and commit. Use when starting work on an existing ticket.

```
/finalize-ticket
```

Commit changes, post a summary comment, attach the commit, and mark a Linear ticket as done. Use when wrapping up a completed ticket.

```
/verify-work
```

Check that changes satisfy the requirement using goal-backward analysis. Catches gaps that tests alone miss. Use after finishing a feature or fix.

```
/verify-refactor
```

Confirm a refactor preserves behavior and covers edge cases. Use when you've restructured code and want to verify correctness before committing.

```
/handoff
```

Generate a handoff doc with full context for a fresh session. Use when the conversation is long or you need to continue elsewhere.

```
/tidy-commits
```

Analyze unpushed commits for squash and streamlining opportunities. Use when you're about to push a branch with messy commit history.

```
/reflect
```

Review recent work across commits, conversations, and project artifacts. Extract principles and learnings, then write them to a destination you choose. Use when starting a new session to build on recent work.

```
/work-report
```

Generate a time-tracked report from git commit history. Use when reporting work done during a period.

```
/find-conversation
```

Search prior Claude Code conversations by natural language description. Use when you need to locate a past discussion.

#### Documentation

```
/generate-readme
```

Walk through a codebase, ask clarifying questions, and produce a README. Use when creating or rewriting a project README.

```
/heal-docs
```

Restructure Markdown docs so LLMs can consume them more effectively. Use when optimizing reference docs, skills, or guides.

```
/heal-claude-md
```

Apply priority hierarchy and self-verification patterns to CLAUDE.md files. Use when improving project instructions for Claude Code.

```
/prime-prompt-quality
```

Load the prompt quality guide into context as a reference. Use before writing or reviewing prompts.

#### Mental frameworks (`/consider:*`)

Twelve decision-making frameworks for structured analysis. Run `/analyze-problem` to describe your situation and get a recommendation for which one fits.

```
/consider:first-principles
```

Break a problem down to fundamentals and rebuild. Use when designing a new system or redesigning one with multiple constraints.

```
/consider:5-whys
```

Drill to root cause by asking "why" repeatedly. Use when a bug keeps resurfacing or CI keeps breaking in different ways.

```
/consider:inversion
```

Identify what would guarantee failure, then avoid it. Use when planning a migration, major refactor, or production rollout.

```
/consider:second-order
```

Map consequences of consequences. Use when choosing between approaches that both work today but diverge long-term.

```
/consider:pareto
```

Apply the 80/20 rule to find highest-impact actions. Use when many issues surfaced but you can only address a few.

```
/consider:eisenhower-matrix
```

Sort tasks by urgency and importance. Use when sprint planning with a mix of bugs, tech debt, features, and infra work.

```
/consider:10-10-10
```

Evaluate impact across three time horizons. Use when tempted to take a shortcut, like hardcoding a value, skipping tests, or merging without review.

```
/consider:swot
```

Map strengths, weaknesses, opportunities, and threats. Use when evaluating whether to adopt a new framework, library, or tool.

```
/consider:occams-razor
```

Find the explanation that fits all facts with fewest assumptions. Use when a bug has multiple plausible causes and you're tempted to chase the exotic one.

```
/consider:one-thing
```

Identify the single highest-leverage action. Use when a large project has stalled with too many open threads.

```
/consider:opportunity-cost
```

Analyze what you give up by choosing each option. Use when deciding between building in-house vs. using a third-party service.

```
/consider:via-negativa
```

Improve by removing rather than adding. Use when a prompt, config, or module feels bloated but you're unsure what to cut.

### Linear integration

A conversational interface to Linear, built as a Claude Code skill. Describe what you're working on and it creates tickets, assigns work, updates status, and queries issues without leaving your terminal.

- **Effort and impact estimation** -- infers priority (user impact) and estimate (implementation effort) from your description, calibrated for AI-assisted development
- **Project and label discovery** -- fetches available projects and labels, matches them to your ticket's domain, and suggests assignments
- **Scope-change awareness** -- when a comment or description update changes the scope of work, automatically re-evaluates priority and estimate

Activates when you mention creating tickets, updating issues, or checking assignments. Configure with a `.linear.json` in your project root and a `LINEAR_API_KEY` in `.claude/settings.local.json`.

### Skills

Skills activate automatically based on what you're doing. Claude Code picks the right one for the task.

- **`create-skill`** -- Build new SKILL.md files through collaborative conversation.
- **`create-slash-command`** -- Generate slash command files with proper YAML frontmatter and structure.
- **`create-subagent`** -- Configure subagent specs with tool restrictions and orchestration patterns.
- **`create-hook`** -- Write hook configurations for PreToolUse, PostToolUse, and other events.
- **`create-prompt`** -- Create standalone prompt files.
- **`audit-prompt`** -- Check prompts for wasted tokens, poor positioning, and vague instructions.
- **`readme-best-practices`** -- Apply consistent structure, tone, and formatting to README files.
- **`clean-conversations`** -- Remove empty Claude Code conversations across all projects.

### Reference guides

- **`prompt-quality-guide.md`** -- How LLMs process instructions: finite capacity, interference, positional bias, context depletion.
- **`docs/prompt-engineering-research-2025.md`** -- Academic research on instruction-following capacity and degradation patterns.
- **`docs/claudemd-effectiveness-research.md`** -- Research on CLAUDE.md and AGENT.md file effectiveness.
- **`docs/readme-guide.md`** -- Writing effective READMEs (the principles behind `/generate-readme`).
- **`docs/building-skills-guide.md`** -- Guide to building Claude Code skills.
- **`docs/skill-description-guide.md`** -- Writing YAML skill descriptions that Claude Code reliably discovers.
- **`docs/skill-discovery-pattern.md`** -- Adding reliable skill loading to commands.
- **`docs/hooks-reference-official.md`** -- Reference for the Claude Code hooks system.
- **`docs/skills-reference-official.md`** -- Reference for the Claude Code skills system.

---

## Quick start

Requires Node.js 16.7+ and [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

**Clone once, install anywhere:**

```bash
git clone https://github.com/rolandtolnay/llm-toolkit.git ~/toolkits/llm-toolkit
```

**Install into a project** (default — symlinks into `./.claude/`):

```bash
cd your-project
~/toolkits/llm-toolkit/install.js
```

**Install globally** (available in all projects):

```bash
~/toolkits/llm-toolkit/install.js --global
```

**Copy mode** (for team sharing via git):

```bash
cd your-project
~/toolkits/llm-toolkit/install.js --copy
```

**Uninstall:**

```bash
cd your-project
~/toolkits/llm-toolkit/install.js --uninstall
```

Symlinks are the default — a `git pull` in the toolkit repo updates all installations automatically. Use `--copy` when you need to commit the files into your project. Not supported on Windows (use `--copy`).

After installation, open Claude Code and use any command (e.g., `/verify-work`) or start working on a task that matches a skill.

---

## Usage examples

**Verify that your changes actually work:**

```
/verify-work
```

Reads your recent changes, traces them back to the original requirement, and reports whether the implementation actually does what was asked.

**Pick the right mental framework for a decision:**

```
/analyze-problem
```

Describe your situation and get a recommendation for which of the 12 frameworks fits, then walk through the analysis.

**Create a Linear ticket from a description:**

```
Users lose their draft when the app goes to background -- save it to local storage
```

Infers priority (High, degraded core flow), estimate (S, 1-2 files, known approach), matches the right project and labels, asks you to confirm, and creates the ticket.

**Generate a README for a project:**

```
/generate-readme
```

Walks through the codebase, asks clarifying questions, and produces a README.

---

## Not included

This is not a replacement for Claude Code's built-in capabilities. No general-purpose coding assistance, test generation, or CI/CD. The mental frameworks structure your reasoning but still need your judgment.

## License

[MIT](LICENSE)
