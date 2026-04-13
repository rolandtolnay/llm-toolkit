<div align="center">

# llm-toolkit

**Slash commands, skills, and decision frameworks for Claude Code.**

```bash
git clone https://github.com/rolandtolnay/llm-toolkit.git ~/toolkits/llm-toolkit
cd your-project && ~/toolkits/llm-toolkit/install.js
```

[Integrations](#integrations) · [Quick start](#quick-start) · [Commands & skills](#also-included) · [Usage examples](#usage-examples)

</div>

---

## What this is

Slash commands, auto-activating skills, and reference guides for Claude Code. Workflow automation (commits, verification, handoffs), integrations with Linear, Slack, and the web for research, 12 mental frameworks for structured decisions, and guides for writing better prompts.

---

## Integrations

These three skills are the highlight of the toolkit. Each is complex enough to deserve its own repository — they live together here so one install gives you all of them. If you adopt nothing else from this repo, adopt these.

Each activates automatically based on what you mention in conversation — no slash command needed.

---

### Research

Web research that scales from quick lookups to deep multi-source investigations. Decomposes a question into sub-questions, runs them in parallel across web search, library docs, Reddit, YouTube, and short-form video, then synthesizes a cited answer and saves it for later runs.

- **Cost-conscious escalation** — starts with free tools (WebSearch, WebFetch, Context7 docs, YouTube via yt-dlp) and only spends API budget when free sources fall short
- **Parallel decomposition** — splits complex questions across subagents that investigate independently, with mandatory source diversity per subagent
- **Source verification** — cross-references findings across primary, secondary, and tertiary sources, flags contradictions, and signals confidence (verified, likely, unverified)
- **Compounding knowledge** — saves standard and deep runs to `~/Documents/Research/` with a scannable index, then consults that index before spending API budget on questions you've already researched
- **Audit trail** — every web call is logged so you can review what each subagent did and how much it cost

Activates on "search for", "look up", "find out", "what's the latest", or "research".

**Setup:**

The skill loads keys from three sources in increasing precedence: your shell environment (lowest), `~/.claude/research/.env` (skill-global), then `.claude/research.env` in the project root (highest). Already export `PERPLEXITY_API_KEY` in your shell? It just works — the env files only need to exist if you want to override or scope a key. Only Perplexity is required; the others unlock additional sources.

| Variable | Service | Powers | Required |
|----------|---------|--------|----------|
| `PERPLEXITY_API_KEY` | [Perplexity](https://docs.perplexity.ai/) | Synthesized answers, web search, reasoning | Yes |
| `CONTEXT7_API_KEY` | [Context7](https://context7.com/dashboard) | Version-aware library documentation | No |
| `FIRECRAWL_API_KEY` | [Firecrawl](https://firecrawl.dev/) | Site mapping and full page scraping | No |
| `SCRAPECREATORS_API_KEY` | [ScrapeCreators](https://scrapecreators.com/) | Reddit and short-form video search | No |

Example `~/.claude/research/.env`:

```bash
PERPLEXITY_API_KEY=pplx-...
CONTEXT7_API_KEY=...
FIRECRAWL_API_KEY=fc-...
SCRAPECREATORS_API_KEY=...
```

YouTube search additionally requires `yt-dlp` (`brew install yt-dlp` on macOS) — no API key.

Run `research config` to verify which keys are loaded and which env files were read.

---

### Linear

A conversational interface to Linear. Describe what you're working on and Claude infers priority and effort, picks the right project and labels, confirms once, and creates the ticket.

- **Effort and impact estimation calibrated for AI-assisted development** — infers priority from user impact and estimates implementation effort using values appropriate for working with Claude, not human-week sprints
- **Project and label discovery** — fetches available projects and labels and matches them to the ticket's domain
- **Scope-change awareness** — when a comment or description update changes scope, re-evaluates priority and estimate
- **Custom view management** — create, list, and delete Linear views from the conversation
- **Document and attachment support** — create native markdown documents on issues, attach files, and link git commits

Activates on phrases like "create a ticket", "mark done", "my issues", or any reference to an issue ID like `ABC-123`.

**Setup:**

1. Create a `.linear.json` in your project root:
   ```json
   {
     "teamId": "your-team-uuid",
     "projectId": "default-project-uuid",
     "defaultPriority": 3,
     "defaultLabels": ["mobile"]
   }
   ```
2. Add a Linear API key to `.claude/settings.local.json` (git-ignored):
   ```json
   {
     "env": {
       "LINEAR_API_KEY": "lin_api_..."
     }
   }
   ```
3. Generate a key at [linear.app/settings/api](https://linear.app/settings/api).

---

### Slack

A conversational interface to Slack that posts as your user, not a bot. Read-only commands run immediately; outbound messages always require explicit confirmation before posting.

- **Posts as you** — uses your User OAuth Token, so messages appear from your account and respect your DMs, channels, and workspace permissions
- **Confirmation gate on outbound** — every send, schedule, and edit is drafted and shown to you before it goes out, so you never ship a message you didn't approve
- **PR announcements** — `share the PR in #engineering-pr` reads the current branch's PR via `gh`, drafts an impact-focused message, and posts after confirmation
- **Search and history** — Slack search modifiers work (`from:me`, `in:#channel`, `before:2026-03-01`); channel history surfaces threads inline
- **Status and scheduling** — set status with auto-clear durations (`2h`, `1h30m`), schedule messages with `--at "in 30m"`

Activates on phrases like "message Roland", "post in #engineering", "search Slack for X", or "set my status to deep work".

**Setup:**

1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps) → "From scratch" → pick your workspace.
2. Under **OAuth & Permissions**, add these User Token Scopes: `chat:write`, `search:read`, `channels:history`, `channels:read`, `users:read`, `users.profile:write`, `groups:history`, `groups:read`, `reactions:write`, `im:history`.
3. Click **Install to Workspace** and copy the **User OAuth Token** (starts with `xoxp-`).
4. Add it to `.claude/settings.local.json` (git-ignored):
   ```json
   {
     "env": {
       "SLACK_USER_TOKEN": "xoxp-..."
     }
   }
   ```

Full reference: `skills/slack/references/setup-guide.md`.

---

## Also included

### Commands

Slash commands you invoke directly in Claude Code (e.g., `/verify`).

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
/verify
```

Second-opinion verification of completed work. Analyzes correctness, behavioral preservation, and completeness (blast-radius sweep for stale references) autonomously, then interrogates interactively before declaring issues. Use after finishing any feature, fix, or refactor.

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

### Skills

Skills activate automatically based on what you're doing — no slash command needed. Claude Code picks the right one for the task.

#### Authoring

```
create-skill
```

Build new SKILL.md files through collaborative conversation. Use when turning a workflow into a reusable skill.

```
create-slash-command
```

Generate slash command files with proper YAML frontmatter and structure. Use when building custom `/commands` or adding arguments and dynamic context.

```
create-subagent
```

Configure subagent specs with tool restrictions and orchestration patterns. Use when defining agent types or launching specialized agents with the Task tool.

```
create-hook
```

Write hook configurations for event-driven automation. Use when adding PreToolUse, PostToolUse, Stop, or other event hooks to validate commands or automate workflows.

```
create-prompt
```

Create standalone prompts that another Claude can execute. Use when writing reusable prompts for coding, analysis, or research tasks.

```
create-toolkit-installer
```

Generate `install.js` for Claude Code toolkit repos with manifest tracking, symlink/copy modes, and uninstall support. Use when creating a new distributable collection of commands, skills, agents, or references.

#### Quality

```
audit-prompt
```

Check prompt files for wasted tokens, poor positioning, and vague instructions. Use when reviewing changes to commands, skills, agents, or any file containing LLM instructions.

```
readme-best-practices
```

Apply consistent structure, tone, and formatting to README files. Use when drafting, rewriting, or reviewing a project README to make it scannable and developer-friendly.

#### Maintenance

```
clean-conversations
```

Remove empty Claude Code conversations across all projects. Use when cleaning up sessions that were opened then immediately closed.

### Reference guides

- **`prompt-quality-guide.md`** -- How LLMs process instructions: finite capacity, interference, positional bias, context depletion.
- **`docs/prompt-engineering-research-2025.md`** -- Academic research on instruction-following capacity and degradation patterns.
- **`docs/writing-effective-claude-md.md`** -- Reference guide for writing effective CLAUDE.md files.
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

After installation, open Claude Code and use any command (e.g., `/verify`) or start working on a task that matches a skill.

---

## Usage examples

**Verify completed work:**

```
/verify
```

Analyzes your changes across correctness, preservation, and completeness, then walks through findings interactively before declaring issues.

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
