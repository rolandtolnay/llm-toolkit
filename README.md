<div align="center">

# llm-toolkit

**Slash commands, skills, and decision frameworks for Claude Code.**

```bash
git clone https://github.com/rolandtolnay/llm-toolkit.git ~/toolkits/llm-toolkit
cd your-project && ~/toolkits/llm-toolkit/install.js
```

[Quick start](#quick-start) · [Commands](#commands) · [Skills](#skills) · [Usage examples](#usage-examples) · [Product Research](#product-research)

</div>

---

## What this is

Slash commands, auto-activating skills, and reference guides for Claude Code. The four featured skills below — Research, Product Research, Linear, and Slack — are the toolkit's centerpiece, each substantial enough to stand alone. Other commands and skills (workflow automation, decision frameworks, prompt helpers) are grouped later under [Commands](#commands) and [Skills](#skills).

---

## Research

Web research that scales from quick lookups to deep multi-source investigations. Decomposes a question into sub-questions, runs them in parallel across web search, library docs, Reddit, YouTube, and short-form video, then synthesizes a cited answer and saves it for later runs.

- **Cost-conscious escalation** — starts with free tools (WebSearch, WebFetch, Context7 docs) and uses ScrapeCreators-backed sources such as Reddit, short-form video, and primary YouTube only when they add value; YouTube keeps a free yt-dlp fallback
- **Parallel decomposition** — splits complex questions across subagents that investigate independently, with mandatory source diversity per subagent
- **Source verification** — cross-references findings across primary, secondary, and tertiary sources, flags contradictions, and signals confidence (verified, likely, unverified)
- **Compounding knowledge** — saves standard and deep runs to `~/Documents/Research/` with a scannable index, then consults that index before spending API budget on questions you've already researched
- **Audit trail** — every web call is logged so you can review what each subagent did and how much it cost

Activates on "search for", "look up", "find out", "what's the latest", or "research".

**Example run:**

The skill mirrors how a careful person researches: split the question into angles, then actually check the right source for each — read the docs, scan Reddit threads, watch a YouTube review — instead of asking a single oracle. Each angle is its own sub-agent running in parallel, writing findings to its own file.

> "How is Opus 4.7 landing with developers?"

| Angle | Sources | One-line finding |
|-------|---------|------------------|
| Official release | WebSearch + WebFetch | SWE-bench Verified 87.6% (+6.8pp), CursorBench 70 vs 58; `budget_tokens` removed, `/ultrareview` added |
| Reddit/HN reaction | `social reddit` + `research ask` + WebFetch | ~55% skeptical; tokenizer change inflates cost 1.0-1.35×; MRCR v2 @ 1M flagged 78.3% → 32.2% (Craig_VG, 226 upvotes) |
| YouTube reviews | `youtube search` (ScrapeCreators primary, yt-dlp fallback) | CodeRabbit measures ~15% bug-finding recall gain; AI for Work's head-to-head shows 4.7 skipping mobile-responsive testing 4.6 did unprompted |

Three sub-agents ran in parallel, each writing a findings file to `~/Documents/Research/2026-04-16-opus-4-7-community-reception/` alongside a `00-synthesis.md` verdict. Tagged in `INDEX.md` so future "Opus 4.7" questions reuse this run instead of re-spending API budget.

**Setup:**

The skill loads keys from three sources in increasing precedence: your shell environment (lowest), `~/.claude/research/.env` (skill-global), then `.claude/research.env` in the project root (highest). Already export `PERPLEXITY_API_KEY` in your shell? It just works — the env files only need to exist if you want to override or scope a key. Only Perplexity is required; the others unlock additional sources.

| Variable | Service | Powers | Required |
|----------|---------|--------|----------|
| `PERPLEXITY_API_KEY` | [Perplexity](https://docs.perplexity.ai/) | Synthesized answers, web search, reasoning | Yes |
| `CONTEXT7_API_KEY` | [Context7](https://context7.com/dashboard) | Version-aware library documentation | No |
| `FIRECRAWL_API_KEY` | [Firecrawl](https://firecrawl.dev/) | Site mapping and full page scraping | No |
| `SCRAPECREATORS_API_KEY` | [ScrapeCreators](https://scrapecreators.com/) | Reddit, short-form video, and primary YouTube research | No |

Example `~/.claude/research/.env`:

```bash
PERPLEXITY_API_KEY=pplx-...
CONTEXT7_API_KEY=...
FIRECRAWL_API_KEY=fc-...
SCRAPECREATORS_API_KEY=...
```

YouTube research uses ScrapeCreators first when `SCRAPECREATORS_API_KEY` is configured. Install `yt-dlp` (`brew install yt-dlp` on macOS) to enable the Free Fallback Backend when the key is missing or ScrapeCreators fails. ScrapeCreators YouTube search is cached for 24h, transcripts for 30d; `--after` accepts `today`, `this_week`, `this_month`, or `this_year`.

Run `research config` to verify which keys are loaded and which env files were read.

---

## Product Research

Staged buying-decision research for household and personal products (appliances, furniture, electronics). Runs a 5-stage pipeline — interview, preliminary research, product evaluation, verification, synthesis — that resists SEO/affiliate noise and produces a ranked recommendation grounded in real owner and expert voices.

- **Structured interview** — generates 4-6 category-specific questions using a calibration frame (not a generic template), surfacing the constraints that actually change the recommendation
- **Research-derived criteria** — builds a ranked criteria list from expert reviews, non-affiliate YouTube, and Reddit owner threads; user priorities become input signal and tiebreaker, not gospel
- **Three independent voices** — parallel subagents gather owner voice (Reddit, YouTube long-form), expert voice (trade publications, specialized reviewers), and retailer voice (current availability and pricing in RO/EU)
- **Verification pass** — scrapes retailer URLs for the final 6 recommendations to flag out-of-stock, price changes, or ambiguous listings without rewriting the quality-based recommendation
- **Master-class synthesis** — output teaches you what actually matters for the category, calls out marketing myths, and presents 3 tiers (overall / budget / premium) with primary + runner-up per tier, tradeoff analysis, and a considered-and-discarded section

Invoked via `/product-research`. One product per run — deep focus over breadth.

**Availability tiering:** Green (RO retailer, full recommend) → Yellow (EU retailer, recommend with import flag) → Red (US-only, excluded).

**Setup:** Uses the same infrastructure as [Research](#research) — CLI tools, API keys, output directory (`~/Documents/Research/`), and persistence format. No additional configuration needed beyond what Research requires.

---

## Linear

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
3. Generate a key at [linear.app/settings/account/security](https://linear.app/settings/account/security).

---

## Slack

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

## Commands

Slash commands you invoke directly in Claude Code.

### `/work-ticket`

Runs the full Linear-ticket loop end-to-end: diagnose → design → execute, with checkpoints where engineer judgment matters most.

Use it when you want:

- to start implementation on a known Linear ticket
- a structured pass that separates "what's the root cause" from "which approach fits" from "is the change correct"
- the LLM to handle information gathering between checkpoints while you stay in control of decisions

Takes a ticket ID as its one argument. Fetches the ticket (including comments and parent) via the Linear CLI, moves it to **In Progress**, loads any matching domain skill, and runs three checkpoints: diagnosis, solution spectrum, and verification-before-commit. On final approval, hands off to [`/finalize-ticket`](#finalize-ticket).

Examples:

```bash
/work-ticket MIN-42
```

Requires the [Linear](#linear) skill configured with `.linear.json` and `LINEAR_API_KEY`.

### `/explain`

Deeper, clearer explanation of the current issue, options, or behavior so you can make a confident decision.

Use it when you want:

- to understand *why* something is happening before picking a fix
- to evaluate consequences of two or three alternatives Claude just proposed
- to gauge whether an issue is worth addressing or is noise
- architectural context on how a component fits into the larger system

Takes an optional topic. If omitted, uses the current conversation context. Detects which shape of confusion is active (what's happening, which option, is this important, how does this fit), then explains in layers: plain-language summary, familiar-ground anchor, specifics, confidence check.

Examples:

```bash
/explain why the middleware is rejecting the request
/explain the difference between these two caching approaches
```

Ends with an interactive confidence check — does not assume you're satisfied with the first pass.

### `/verify`

Second-opinion verification on completed work. Analyzes correctness, behavioral preservation, and completeness, then interrogates interactively before declaring anything an issue.

Use it when you want:

- a final pass after finishing a feature, fix, or refactor
- a blast-radius sweep that greps the whole codebase for stale references the diff alone can't find
- a structured conversation to distinguish real bugs from intentional omissions

> [!NOTE]
> Every finding is confirmed with you before being declared an issue. Nothing is fixed without explicit approval.

Takes an optional scope argument: commit range, plan path, or a prose description. If omitted, asks once. Uses parallel Explore agents for analysis and runs tests when present. Ends with one of: **CLEAN**, **ISSUES FOUND**, or **NEEDS MANUAL TEST**.

Examples:

```bash
/verify abc123..HEAD
/verify .planning/0042-rate-limiter.md
/verify the session timeout refactor
```

Pairs well with [`/ripple-check`](#ripple-check) when a fix might apply in more places than you touched.

### `/ripple-check`

After a fix or improvement, probes the codebase for other places where the same learning might apply.

Use it when you want:

- to check whether a bug pattern exists elsewhere (copy-paste lineage, same wrong assumption)
- to propagate a better approach learned from a reference implementation
- an honest assessment — not forced findings

No arguments. Uses session context to extract the abstract pattern behind the recent change, then launches parallel Explore agents to find candidates. For each candidate, states explicitly whether the pattern transfers and why.

"Checked X, Y, Z and the pattern doesn't apply because…" is a valid outcome — the command will not invent findings.

### `/finalize-ticket`

Commits pending changes, posts a solution summary comment, attaches the commit, and marks a Linear ticket as Done.

Use it when you want:

- to close out a completed ticket in one step instead of four manual Linear actions
- the commit message to carry the `[TICKET-ID]` suffix automatically

Takes a ticket ID. Commits using the repo's existing commit style (adds `[TICKET-ID]` to the first line), then runs the Linear CLI for comment, attach-commit, and state transition.

Examples:

```bash
/finalize-ticket MIN-42
```

Usually invoked by [`/work-ticket`](#work-ticket) at the end of its execute phase, but safe to call directly.

### `/tidy-commits`

Analyzes unpushed commits on the current branch and proposes squash/reorder groupings before executing an interactive rebase.

Use it when you want:

- to clean up "add X / fix X typo / refactor X" chains before pushing
- to fold fixup commits into their originals
- a safety-checked rebase that verifies the diff stat before and after

> [!WARNING]
> This rewrites history. The command captures a pre-rebase `git diff --stat` and confirms it matches post-rebase — but only run on branches you haven't shared yet.

No arguments. Uses the upstream tracking branch, falling back to `origin/main`. Bails early if fewer than two unpushed commits exist. Identifies cross-cutting commits that might need splitting before folding, and warns about reorder conflicts based on file overlap.

### `/create-pr`

Creates a pull request against `main` with a summary that combines diff analysis, conversation context, and any referenced Linear ticket.

Use it when you want:

- a PR whose summary explains *why* — not just *what* — the changes happened
- Linear ticket links woven into the narrative (primary, parent, related)
- an optional auto-post to `#engineering-pr` after you confirm the message

Takes optional extra context as an argument ("use the last 3 commits", "cherry-pick abc123"). Auto-detects whether to PR from the current branch, isolate uncommitted changes onto a new branch, or both. Every git operation (mode, branch name, push) confirms before running.

Examples:

```bash
/create-pr use the last 2 commits only
/create-pr this relates to ENG-1234
```

Posts to Slack via the [Slack](#slack) skill if configured; skips silently otherwise.

### `/reflect`

Reviews recent work across commits and past conversations, extracts principles, and writes them to a destination you choose.

Use it when you want:

- to compound learnings from the past week into durable memory
- to refresh CLAUDE.md with patterns that have proved out in practice
- to start a new session with recent context already loaded

Takes an optional timeframe (defaults to "past week"). Reads CHANGELOG, README, CLAUDE.md, and git log. Uses parallel Explore subagents to search JSONL conversation history for user-voiced principles (never loads JSONL into main context). Presents candidates tagged **NEW / UPDATE / STALE** before writing anywhere.

Examples:

```bash
/reflect past 3 days
/reflect past month
```

Asks before writing whether to target auto-memory, CLAUDE.md, or a custom path.

### `/handoff`

Writes a `handoff.md` in the current directory capturing everything a fresh Claude Code session needs to continue this work.

Use it when you want:

- to bail out of a long conversation without losing context
- to hand work to another session, machine, or collaborator
- a structured snapshot of what's done, what's left, what was tried, and what's in-flight

No arguments. Produces an XML-structured document with: `original_task`, `work_completed`, `work_remaining`, `attempted_approaches`, `critical_context`, `current_state`.

### `/generate-readme`

Walks through the codebase, asks clarifying questions, and writes a README that works as a standalone pitch.

Use it when you want:

- a README for a project that doesn't have one
- to rewrite an existing README that has drifted from reality
- structure tuned for scannability — top 20% pitches, below that is reference material

Takes an optional path argument (defaults to the current directory). Uses parallel Explore agents to investigate project identity, core functionality, and existing docs, then uses AskUserQuestion to fill gaps (target audience, install method, features to highlight). Shows a summary of key changes before overwriting an existing README.

Examples:

```bash
/generate-readme ./packages/api
```

Enforces a banned-word list ("streamline", "seamlessly", "simply", "leverage"…) so output doesn't read as AI-generated.

### `/analyze-problem`

Describe your situation and get a recommended framework to apply before diving into analysis.

Use it when you want:

- to pick the right lens for a decision rather than defaulting to one
- a quick diagnostic before running a `/consider:*` command
- guidance on whether to gather external information (via `/research`) before thinking it through

Takes an optional problem description. If omitted, deduces the problem from conversation context. Matches signal words across 12 frameworks covering decision-making, problem-solving, focus, and strategy. Also recommends `/research` when external facts would change the analysis.

Examples:

```bash
/analyze-problem should I migrate from Redux to Zustand now or after the launch
/analyze-problem the backfill job keeps failing with different errors each time
```

### `/consider:*`

Twelve frameworks for structured analysis. Pick directly when you already know which lens fits, or run [`/analyze-problem`](#analyze-problem) for a recommendation.

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

## Skills

### `create-skill`

Build new SKILL.md files through collaborative conversation. Use when turning a workflow into a reusable skill.

### `create-slash-command`

Generate slash command files with YAML frontmatter, argument hints, and dynamic context. Use when building custom `/commands`.

### `create-subagent`

Configure subagent specs with tool restrictions and orchestration patterns. Use when defining agent types or launching specialized agents with the Task tool.

### `create-hook`

Write hook configurations for event-driven automation. Use when adding PreToolUse, PostToolUse, Stop, or other Claude Code lifecycle hooks.

### `create-prompt`

Create standalone prompts that another Claude can execute. Saves to `./prompts/` as numbered `.md` files.

### `create-toolkit-installer`

Generate `install.js` for Claude Code toolkit repos with manifest tracking, symlink/copy modes, and uninstall support.

### `audit-prompt`

Check prompt files for wasted tokens, poor positioning, and vague instructions. Use when reviewing changes to commands, skills, agents, or any file containing LLM instructions.

### `readme-best-practices`

Apply consistent structure, tone, and formatting to README files. Pairs with [`/generate-readme`](#generate-readme) — the command drafts, this skill polishes. Use when rewriting or reviewing a project README.

### `triage-pr-comments`

Fetches PR comments from GitHub, applies a fix-vs-ignore framework to each, resolves dismissed threads, and plans fixes. Deferred items log as tickets via the [Linear](#linear) skill. Use when addressing PR feedback or following up on code review.

### `pr-qa-browser`

Derives risk-focused browser QA stories from a dashboard-web PR, runs feasible Agent Browser checks, saves screenshots, and reports remaining manual follow-ups.

### `nano-banana-app-icon`

Interactive iOS/Android app icon design with Nano Banana 2. Runs a discovery brief, writes a JSON prompt you paste into gemini.google.com, then critiques the resulting PNG and outputs a refinement prompt.

> [!NOTE]
> This skill does not generate images itself. It produces prompts you paste into Gemini, then iterates based on the downloaded PNG.

Use when making, replacing, or refining an app icon.

### `searchexa`

Semantic web search via EXA API that returns actual page content inline — search and fetch in one call. A cheaper alternative to the [Research](#research) skill when you want raw content rather than AI-synthesized answers.

> [!NOTE]
> Free tier is 1000 searches/month. Requires `EXA_API_KEY` in the same env-file chain as Research.

Use when you need to find and read pages in one pass, and synthesis isn't required.

## Reference guides

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

```bash
git clone https://github.com/rolandtolnay/llm-toolkit.git ~/toolkits/llm-toolkit
cd your-project && ~/toolkits/llm-toolkit/install.js
```

Requires Node.js 16.7+ and [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Open Claude Code and try `/verify`, or describe a Linear ticket to see the integrations auto-activate.

For global install, copy mode, or uninstall, see [Install options](#install-options).

---

## Install options

The default install symlinks the toolkit into `./.claude/` of the current project. A `git pull` in `~/toolkits/llm-toolkit` then updates every project that points at it.

```bash
~/toolkits/llm-toolkit/install.js
```

**Global** — available in every project, installed into `~/.claude/`:

```bash
~/toolkits/llm-toolkit/install.js --global
```

**Copy mode** — copies files instead of symlinking, so they can be committed and shared with a team via git. Required on Windows since symlinks aren't supported.

```bash
cd your-project
~/toolkits/llm-toolkit/install.js --copy
```

**Uninstall** — removes every toolkit file from the target scope (add `--global` to uninstall the global install):

```bash
cd your-project
~/toolkits/llm-toolkit/install.js --uninstall
```

---

## Updating

Symlink installs (the default) update automatically when you pull the toolkit repo:

```bash
cd ~/toolkits/llm-toolkit && git pull
```

Copy installs need to be re-run after pulling:

```bash
cd ~/toolkits/llm-toolkit && git pull
cd your-project && ~/toolkits/llm-toolkit/install.js --copy
```

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

## License

[MIT](LICENSE)
