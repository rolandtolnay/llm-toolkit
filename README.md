# llm-toolkit

> Skills and commands I use for research, coding-agent workflows, integrations, and projects that need to outlive one chat session.

`llm-toolkit` is my working collection of resources for coding agents. Some are small, like a command for explaining a difficult change. Others run full research, naming, buying, review, or project-memory workflows. I keep them together because they solve jobs I run into repeatedly, and because their dependencies and awkward edges are worth documenting.

The source format is Claude Code. The install prompt below can adapt selected resources to Pi or another agent with comparable skills, prompts, hooks, and subagents. That adaptation is a port, and some Claude-specific paths or tools will need translation.

## Quickstart

> [!TIP]
> Expand the prompt, copy it into a fresh session of the coding agent you want to install into, and let that agent inspect the repository before you choose resources.

<details>
<summary><strong>Install prompt: click to expand</strong></summary>

```text
Install selected resources from the llm-toolkit repository into this coding agent.

Repository: https://github.com/rolandtolnay/llm-toolkit.git

# Goal

Give me a working, selective installation that follows THIS agent's discovery conventions and THIS operating system. Preserve each installed resource's behavior while adapting Claude-specific paths, tool names, hooks, prompts, and subagent references where this agent has an equivalent.

# Success criteria

- I choose the scope (project or user), resources, and install mode (copy or symlink) before files are installed.
- Every installed skill, command/prompt, agent, script, hook, and local reference resolves from its final location.
- Cross-resource dependencies are installed with the selected resource or reported as unmet.
- No installed file points at a temporary checkout or an unavailable agent tool.
- Existing unmanaged files and local modifications are preserved unless I approve a specific overwrite or removal.
- A local manifest records the source URL and revision, stable checkout path when applicable, selected resources, source and destination paths, install mode, rewrites, and checksums where practical.
- The final report names installed resources, destinations, invocation names, rewrites, runtime dependencies, API keys and expected config paths, validation performed, and remaining limitations. Never print secret values.

# Installation decisions

Inspect the repository and this agent's local documentation or conventions first. Then ask one compact round of questions for any decision not already known:

- project scope or user/global scope
- the resources or groups I want
- copy or symlink mode

Present the repository by use case: research and buying decisions; autonomous project foundations; engineering quality and delivery; integrations; creative workflows; commands and decision frameworks; the optional hobby and business bundles. Recommend a small starting set based on my intended use rather than installing everything by default.

Use a stable checkout for symlinks, never a temporary clone. Prefer copy mode for project/team installs, resources that need path rewrites, and Windows environments where symlinks are unavailable or impractical. Install whole skill directories so bundled references, scripts, assets, and agent metadata stay together.

# Constraints and approval boundaries

Adapt to this agent instead of assuming `~/.claude`, `.claude/`, Claude slash commands, `AskUserQuestion`, `Task`, or Claude hook syntax. Keep relative references intact when possible. Rewrite hardcoded paths only in installed copies; do not modify a shared source checkout to make a symlink work. If faithful adaptation is impossible, leave that resource uninstalled and explain the missing host capability.

Inspect selected resources for hardcoded paths and dependencies before installing. In particular, account for the shared research infrastructure, the `research-subagent`, `bootstrap-goal-project` companions, GitHub/Linear dependencies in delivery workflows, and the `humanizer` dependency used by `create-pr`.

Do not install system packages, create provider accounts, write secrets, overwrite conflicts, delete prior installs, or wire externally mutating hooks without showing the action and getting confirmation. A request to install authorizes the selected local resource files and non-destructive validation; it does not authorize unrelated configuration changes.

# Validation and stop rules

Use the minimum checks that prove the selected installation works: inspect final paths, search for stale checkout and host-specific references, verify discovery names, and run one safe `--help`, `config`, or dry-run command for script-backed resources when its runtime is available. Do not make paid API calls or send external messages as a test.

When enough information is available, perform the installation rather than continuing to survey options. Stop when the selected resources are installed and verified, or when a missing host capability, dependency, credential, or user decision blocks safe progress.
```

</details>

The prompt is intentional. Claude Code, Pi, and other agents put skills, prompts, hooks, and secrets in different places. They also use different names for interactive questions and subagents. A guided install can account for those differences while still handling selection, dependencies, conflicts, path changes, and verification.

## Pick an entry point

| You want to… | Start with |
|---|---|
| Research a current topic with citations | [`research`](#research) |
| Make a grounded buying decision | [`product-research`](#product-research) |
| Name a company, product, app, or feature | [`brand-naming`](#brand-naming) |
| Generate and judge app icon candidates | [`app-icon-studio`](#app-icon-workflows) |
| Prepare a repository for independent agent runs | [`new-project` → `bootstrap-goal-project` → `write-loop`](#goal-driven-projects) |
| Verify finished code or triage review feedback | [`/verify`](#engineering-quality-and-delivery) or [`triage-pr-comments`](#engineering-quality-and-delivery) |
| Work from a Linear ticket | [`/work-ticket`](#commands) |
| Search Gmail or Slack from an agent | [`gmail`](#gmail), [`slack`](#slack), or [`linear`](#linear) |

Invocation examples below use Claude Code slash syntax. A port may expose the same resource through a different explicit command.

---

## Research

The [`research`](skills/research/SKILL.md) skill handles quick factual lookups without spinning up a team of agents. Broader questions get split into focused angles, with each subagent assigned the sources that fit its part of the problem. Standard and deep runs are saved under `~/Documents/Research/`.

A few details make it more useful than a one-shot search:

- It starts with built-in web search and reaches for paid providers only when their coverage is needed.
- It checks saved research before repeating work.
- It verifies official claims against primary sources.
- It leaves disagreements between sources visible and labels findings as verified, community-sourced, or unverified.

Example:

```text
Research how teams are using coding-agent subagents in production. Compare official guidance with practitioner reports, flag disagreements, and save the run.
```

This skill is for current web information. Local codebase questions belong with the coding agent's normal file tools. Provider-backed sources can fail, hit rate limits, or cost money, and saved research will age on fast-moving topics.

<details>
<summary><strong>Research setup, API keys, and source coverage</strong></summary>

The Python CLIs use [`uv`](https://docs.astral.sh/uv/) with inline dependencies; the repository does not maintain a root Python environment.

Basic lookups can use the host agent's built-in web search and fetch tools without provider keys. The bundled CLI capabilities are unlocked by these variables:

| Variable | Service | Unlocks |
|---|---|---|
| `PERPLEXITY_API_KEY` | [Perplexity](https://docs.perplexity.ai/) | `search`, `ask`, and `reason` |
| `CONTEXT7_API_KEY` | [Context7](https://context7.com/dashboard) | Version-aware library documentation |
| `FIRECRAWL_API_KEY` | [Firecrawl](https://firecrawl.dev/) | Site mapping and full-page scraping |
| `SCRAPECREATORS_API_KEY` | [ScrapeCreators](https://scrapecreators.com/) | Primary YouTube backend, Reddit, and short-form research |

Source defaults load from the shell, then `~/.claude/research/.env`, then project `.claude/research.env` (highest precedence). A cross-agent installation may adapt those paths.

```dotenv
PERPLEXITY_API_KEY=pplx-...
CONTEXT7_API_KEY=...
FIRECRAWL_API_KEY=fc-...
SCRAPECREATORS_API_KEY=...

RESEARCH_NO_PERSIST=0
RESEARCH_DIR=~/Documents/Research
```

YouTube uses ScrapeCreators first when configured. Install [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) for the Free Fallback Backend. Long transcript preprocessing, video selection, and Reddit condensation can use `claude -p`. Use both `--no-preprocess` and `--no-select` to avoid Claude CLI calls in the YouTube path; Reddit condensation must also be avoided or adapted when that CLI is unavailable.

The [`searchexa`](skills/searchexa/SKILL.md) companion uses `EXA_API_KEY` from `~/.claude/research/.env`. It returns page text with search results and has a documented free allowance of 1,000 searches per month; it does not synthesize or fully scrape pages.

```dotenv
EXA_API_KEY=...
```

Check the installed research CLI's `config` command before a real run. It reports key presence and resolved paths without printing secret values.

</details>

---

## Product research

```text
/product-research
```

This is for buying one thing well, whether that is a mattress, microwave, vacuum, or another household or personal product. The workflow asks only about constraints that could change the shortlist. It then researches the category before comparing models, so the final criteria come from evidence instead of mirroring the user's first assumptions.

Owner reports, expert reviews, and retailer data are gathered separately. Product quality and current stock also stay separate: an ambiguous retailer page adds a verification warning, but it does not quietly replace the better product with whatever happens to be available.

A completed run looks like this:

```text
~/Documents/Research/YYYY-MM-DD-<category>-product-research/
├── 00-synthesis.md
├── 01-interview.md
├── 02-masterclass.md
├── 03-availability.md
├── 04-owner-voice.md
├── 05-expert-voice.md
├── 06-retailer-voice.md
└── aspects/
```

Each run covers one product category. Availability research starts in Romania and the EU, and import options are flagged. Prices and stock can change after the report is written. The workflow filters out obvious affiliate noise, but it cannot remove every source bias or replace trying a product when comfort, sound, or fit matters.

<details>
<summary><strong>Product Research setup and dependencies</strong></summary>

Install `product-research`, `research`, and the `research-subagent` together.

A full run expects:

- `uv` for bundled Python CLIs
- `PERPLEXITY_API_KEY` for the research `ask` and `reason` paths
- `FIRECRAWL_API_KEY` for retailer-page scrape verification
- `SCRAPECREATORS_API_KEY` for richer Reddit and primary YouTube coverage, or `yt-dlp` for the YouTube fallback
- write access to the configured research directory, defaulting to `~/Documents/Research/`

Use the same env files as [Research](#research). Missing optional sources reduce coverage; missing Perplexity or Firecrawl prevents parts of the documented full pipeline and must be reported rather than hidden.

</details>

---

## Brand naming

```text
/brand-naming
```

[`brand-naming`](skills/brand-naming/SKILL.md) is for the naming job where a quick list of 50 plausible words will not cut it. It starts with strategy and category language, gives three isolated generation teams different briefs, and keeps evaluation out of the generation stage.

The raw list runs into the hundreds before it is narrowed. You react to a curated longlist, then the remaining names go through collision, trademark, domain, search, and language checks. Five to seven survivors are tested in headlines, taglines, app-store or shelf contexts, and spoken introductions. The final dossier recommends three to five.

Runs persist under `~/Documents/Research/YYYY-MM-DD-<subject>-naming/`, including the strategy, landscape, generation funnels, screening evidence, proof of concept, and final recommendation.

It is a long workflow with several user checkpoints, so it is overkill for a casual brainstorm. Its trademark and domain checks are screening, not legal clearance. A shortlisted name still needs qualified trademark review.

<details>
<summary><strong>Brand Naming setup and dependencies</strong></summary>

Install `brand-naming`, `research`, and the `research-subagent` together. The full workflow uses the shared research CLI for landscape and screening, so configure `uv` and `PERPLEXITY_API_KEY`. `SCRAPECREATORS_API_KEY` improves access to customer language from Reddit and video sources.

The agent host must support isolated subagents or an equivalent fresh-context mechanism. Without isolation, the three generation teams lose the deliberate diversity the pipeline relies on.

</details>

---

## App icon workflows

Pick the version based on who should run image generation: the skill itself, or you in the Gemini web app.

### `app-icon-studio`: generated and judged in one run

```text
/app-icon-studio
```

[`app-icon-studio`](skills/app-icon-studio/SKILL.md) starts by asking what the icon should communicate in half a second. It then proposes four genuinely different directions and generates each one through OpenAI and Gemini. Independent craft and brand judges review the candidates at 48px before one focused revision turn produces a contact sheet with 5-7 finalists.

A normal run produces about 16 first-round images and saves every prompt and output under `./icons/<app-slug>/`. Failed API calls stay in the funnel count. You approve the four design directions before the skill spends money.

A full run costs roughly **$2-4** in image API fees and takes several minutes. The finalists are raster candidates, so production may still need a high-resolution rerender or vector redraw. The documented thumbnail and contact-sheet steps use the macOS tools `sips` and `open`; other operating systems need replacements or a manual step.

<details>
<summary><strong>App Icon Studio setup and API keys</strong></summary>

Requirements for the documented dual-engine workflow:

- Node.js 18 or newer
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- an agent host capable of independent image-judging subagents
- optional macOS `sips` and `open` support for the documented presentation path

The dependency-free Node scripts load dedicated env files; the project file overrides the user file:

```dotenv
# ~/.claude/app-icon-studio/.env
# or ./.claude/app-icon-studio.env
OPENAI_API_KEY=...
GEMINI_API_KEY=...
```

Run each installed script's `config` command before generation. The scripts report whether keys are present without printing them. If one key is unavailable, the skill supports a reduced single-engine run with doubled candidate counts; disclose the lost cross-engine comparison before proceeding.

</details>

### `nano-banana-app-icon`: manual, no API client

```text
/nano-banana-app-icon
```

[`nano-banana-app-icon`](skills/nano-banana-app-icon/SKILL.md) runs the discovery and critique loop but leaves generation in `gemini.google.com`. It writes a JSON prompt, waits for you to return a PNG, scores the image against an eight-part rubric, and emits one-change refinement prompts until the 48×48 gate passes.

Use it when you want the same design discipline without API setup or automated batch generation. The tradeoff is manual work: you need Gemini web access, must paste each prompt and download each PNG, and should start a fresh Gemini chat after three failed refinements.

---

## Goal-driven projects

```text
/new-project
/bootstrap-goal-project
/write-loop
```

These three skills are for projects that will span independent agent runs. They keep product judgment and project language in the repository, alongside the decisions, execution rules, and run history a new session would otherwise have to reconstruct from chat.

### 1. `new-project`: capture product judgment

[`new-project`](skills/new-project/SKILL.md) interviews for information future runs cannot derive: core value, intended users, non-goals, constraints, and tradeoff preferences. It writes a compact `PROJECT.md`, then dry-runs that document against plausible product forks to check whether a cold agent would decide as you would.

The documented workflow initializes Git when needed and commits `PROJECT.md`. If that is not desired, tell the agent before invocation or adapt the installed skill's commit boundary.

### 2. `bootstrap-goal-project`: install repository memory

[`bootstrap-goal-project`](skills/bootstrap-goal-project/SKILL.md) creates or repairs the broader project-local system: `PROJECT.md`, `CONTEXT.md`, `AGENTS.md`, decision records, goal history, retained evidence, a stack-specific playbook, and fresh-context judging rules. It adapts templates to the actual repository instead of copying the web assumptions from [`hobby-bundle/`](hobby-bundle/).

### 3. `write-loop`: define the next destination

[`write-loop`](skills/write-loop/SKILL.md) turns a rough greenfield or brownfield idea into a short, gradeable `/goal`. It asks only for outcome, success, guardrails, regression boundaries, and other information the run cannot safely infer, then saves the prompt under `etc/loop/`.

The three fit together like this:

```text
PROJECT.md and domain decisions
  → repository-specific playbook
  → short outcome-focused goal
  → implementation and evidence
  → fresh-context judgment
  → GOAL MET or an explicit blocker
```

Skip the full foundation for disposable experiments and small scripts. The extra documentation earns its keep only when work spans sessions or unattended runs. Bootstrap preserves existing artifacts and does not commit unless requested. `new-project` has the separate commit behavior noted above.

<details>
<summary><strong>Goal-driven project setup</strong></summary>

No API key or third-party runtime is required for the three core skills. Install them together when you want the complete flow:

- `new-project`
- `bootstrap-goal-project`
- `write-loop`

The bootstrap skill includes project-foundation templates in its own `assets/` directory. Install the complete directory so those assets come with `SKILL.md`.

The optional [`hobby-bundle/`](hobby-bundle/) is a worked Next.js/Firebase/Vercel example. Treat it as source material or install only the bundled skills that match the target project; do not import its stack assumptions as general rules.

</details>

---

## Integrations

### Linear

[`linear`](skills/linear/SKILL.md) creates, updates, queries, relates, comments on, and organizes Linear issues, projects, cycles, milestones, labels, documents, attachments, and custom views. Single-team workspaces can often resolve the team automatically; multi-team setups can use a flag, environment variable, or `.linear.json`.

Direct update commands run immediately. Ticket creation asks for the smallest missing details first, but there is no universal confirmation gate. Delete and state-change commands mutate Linear as soon as they run.

<details>
<summary><strong>Linear setup</strong></summary>

Requirements: `uv`, a [Linear personal API key](https://linear.app/settings/account/security), and network access to Linear's GraphQL API.

Claude Code source configuration in `.claude/settings.local.json`:

```json
{
  "env": {
    "LINEAR_API_KEY": "lin_api_..."
  }
}
```

Optional project defaults in `.linear.json`:

```json
{
  "teamId": "team-uuid",
  "projectId": "default-project-uuid",
  "defaultPriority": 3,
  "defaultLabels": ["mobile"]
}
```

You can also set `LINEAR_TEAM` to a team key or UUID. The installing agent should adapt the secret location for non-Claude hosts while preserving the CLI's environment contract.

</details>

### Slack

[`slack`](skills/slack/SKILL.md) searches messages, reads channel history and threads, sends or schedules messages, edits posts, adds reactions, and manages status using a Slack **User OAuth Token**. Messages appear as the user, not a bot.

Read-only operations run immediately. Sends, DMs, replies, and schedules are drafted and shown for confirmation before posting. Edit, delete, reaction, and status commands currently mutate Slack immediately; deletion is destructive.

<details>
<summary><strong>Slack app, scopes, and token setup</strong></summary>

Requirements: `uv` and a Slack app installed to your workspace with these **User Token Scopes**:

`chat:write`, `search:read`, `channels:history`, `channels:read`, `users:read`, `users.profile:write`, `groups:history`, `groups:read`, `reactions:write`, `im:history`.

Create an app at [api.slack.com/apps](https://api.slack.com/apps), install it to the workspace, then store the `xoxp-...` User OAuth Token in `.claude/settings.local.json`:

```json
{
  "env": {
    "SLACK_USER_TOKEN": "xoxp-..."
  }
}
```

A cross-agent installation may use another secret store, but the CLI still needs `SLACK_USER_TOKEN` in its process environment. Workspace permissions and Slack rate limits remain in force.

</details>

### Gmail

[`gmail`](skills/gmail/SKILL.md) gives an agent a narrow, read-only Gmail retrieval surface. It searches metadata and bounded snippets first, then fetches only selected messages or threads. Message content is not cached or logged, and attachments remain metadata-only.

The Gmail integration is read-only. It cannot send, reply, delete, archive, change labels or read state, or download attachments. It also rejects broad mailbox dumps.

<details>
<summary><strong>Gmail setup and privacy boundaries</strong></summary>

Requirements: `uv`, Gmail IMAP access, `GMAIL_USER`, and a Google app password in `GMAIL_APP_PASSWORD`.

Supported source paths include:

```dotenv
# Project: .claude/gmail.env
# User: ~/.claude/gmail/.env
GMAIL_USER=you@example.com
GMAIL_APP_PASSWORD=...
```

The CLI can also read supported agent `env.json` locations or process environment variables. Run its `config` command to inspect credential sources, then `doctor` to test read-only IMAP connectivity without returning email content.

</details>

---

## Engineering quality and delivery

### Review and verification

- [`triage-pr-comments`](skills/triage-pr-comments/SKILL.md): Fetches unresolved GitHub review comments, checks each against actual code usage, domain docs, and linked tickets, then classifies it as act, defer, ignore, or investigate. It confirms decisions before replying, resolving, or creating follow-up work.
- [`pr-qa-browser`](skills/pr-qa-browser/SKILL.md): Derives 5-8 risk-focused browser stories from a PR, runs feasible Agent Browser flows, and stores screenshots under `etc/mine/test-<branch>/`.
  - This one is written specifically for `dashboard-web`, its `AGENTS.md`, local server, auth state, and fixtures. It needs adaptation before it can serve as generic browser QA.
- [`audit-prompt`](skills/audit-prompt/SKILL.md): Audits changed prompt-bearing Markdown and YAML for token waste, positioning, specificity, and structural problems.
- [`/verify`](commands/verify.md): Reconstructs intent, analyzes correctness and blast radius, runs tests, then resolves findings interactively before declaring issues.
- [`/ripple-check`](commands/ripple-check.md): Looks for other code locations where a lesson from the latest fix genuinely transfers; "checked, does not apply" is an acceptable result.

### Land the work

- [`create-pr`](skills/create-pr/SKILL.md): Builds a reviewer-oriented PR description from the diff, conversation, tickets, PRDs, and domain docs; confirms branch/commit/push actions and the final body; returns a reusable Slack or release-note summary.
- [`/tidy-commits`](commands/tidy-commits.md): Proposes squash and reorder groups for unpushed commits, confirms them, then compares the changed-file and line-count statistics with the pre-rebase baseline. That check is not content equivalence; inspect the final diff when the rewrite is sensitive.
- [`/finalize-ticket`](commands/finalize-ticket.md): Commits, comments on a Linear issue, attaches the commit, and moves the ticket to Done.
- [`/work-ticket`](commands/work-ticket.md): Runs diagnosis, design, implementation, and verification around a Linear ticket, with engineering checkpoints between phases. Before diagnosis, it moves the issue to In Progress and may create or check out a ticket branch.

<details>
<summary><strong>GitHub, browser, and delivery dependencies</strong></summary>

- `create-pr`, `triage-pr-comments`, and PR-aware commands require authenticated [`gh`](https://cli.github.com/).
- `create-pr` also references the `humanizer` skill from [`hobby-bundle/humanizer`](hobby-bundle/humanizer/). Install it and adapt the reference path with `create-pr`.
- `triage-pr-comments` requires `linear` and credentials when the PR references tickets or a decision is deferred; `create-pr` has the same requirement when a ticket ID appears in its context.
- `/work-ticket` and `/finalize-ticket` require the `linear` skill and its credentials.
- `/finalize-ticket` invokes an external `/commit-commands:commit` resource that is **not included in this repository**. The installing agent must map it to an available commit workflow or report it as unmet.
- `pr-qa-browser` requires `agent-browser`, authenticated `gh`, a running `dashboard-web`, appropriate auth/fixtures, and project-specific testing instructions.
- History rewriting in `/tidy-commits` is destructive to commit identities. The command requires confirmation and is intended for unshared commits.

</details>

---

## Complete skill index

The repository currently has 19 top-level skills. Use this collapsed list when you know the name and want the source file.

<details>
<summary><strong>Show all 19 skills</strong></summary>

### Create and maintain agent resources

- [`create-engineering-skill`](skills/create-engineering-skill/SKILL.md): Turns an engineering failure mode, practice, or workflow into a vocabulary-dense skill with canonical grounding and falsifiable judgment rules.
- [`readme-best-practices`](skills/readme-best-practices/SKILL.md): Supplies supporting guidance for scannable developer READMEs. It is not user-invocable by design.
- [`audit-prompt`](skills/audit-prompt/SKILL.md): Reviews prompt-bearing changes against prompt-quality principles.

### Search and evidence

- [`research`](skills/research/SKILL.md): Runs current web research with verification and optional persistence.
- [`product-research`](skills/product-research/SKILL.md): Produces a category masterclass and ranked buying recommendations.
- [`brand-naming`](skills/brand-naming/SKILL.md): Produces screened brand-name finalists through research and isolated generation.
- [`searchexa`](skills/searchexa/SKILL.md): Returns semantic search results with inline page text through EXA.
- [`gmail`](skills/gmail/SKILL.md): Retrieves narrow, read-only Gmail evidence.

### Project memory and delivery

- [`new-project`](skills/new-project/SKILL.md): Captures product intent and default judgments in `PROJECT.md`.
- [`bootstrap-goal-project`](skills/bootstrap-goal-project/SKILL.md): Creates or repairs the repository's durable autonomous-run foundation.
- [`write-loop`](skills/write-loop/SKILL.md): Writes short, gradeable `/goal` prompts.
- [`create-pr`](skills/create-pr/SKILL.md): Opens a PR with grounded motivation and verification notes.
- [`triage-pr-comments`](skills/triage-pr-comments/SKILL.md): Separates valid review work from deferrals and false positives.
- [`pr-qa-browser`](skills/pr-qa-browser/SKILL.md): Runs dashboard-web-specific browser QA.

### Integrations and deployment

- [`linear`](skills/linear/SKILL.md): Manages Linear work through a conversational CLI.
- [`slack`](skills/slack/SKILL.md): Reads and writes Slack through a user token; sends and schedules confirm first, while edit/delete/react/status paths are immediate.
- [`firebase-hosting-basics`](skills/firebase-hosting-basics/SKILL.md): Guides Firebase Hosting Classic configuration, emulation, previews, and deployment for static sites, SPAs, and simple microservices.
  - It does not cover Firebase App Hosting, SSR, or ISR. It requires Node/npm, `firebase.json`, Firebase authentication and project access, and `npx firebase-tools@latest`. A live deploy changes an external service.

### Creative workflows

- [`app-icon-studio`](skills/app-icon-studio/SKILL.md): Generates, judges, revises, and presents app icon candidates through OpenAI and Gemini APIs.
- [`nano-banana-app-icon`](skills/nano-banana-app-icon/SKILL.md): Writes and critiques app-icon prompts for a manual Gemini workflow.

</details>

---

## Commands

The repository contains 22 Claude-style command prompts. Another host may install them as prompt templates or agent-specific commands.

### Build, review, and ship

```text
/work-ticket ABC-123
```

Runs the full Linear-ticket workflow: orient, diagnose, choose a design, implement, and verify.

```text
/verify [commit range, plan path, or scope]
```

Provides an interactive second opinion on completed work.

```text
/ripple-check
```

Searches for other locations where the latest fix's underlying lesson applies.

```text
/tidy-commits
```

Cleans up unpushed history after showing and confirming the proposed rebase.

```text
/finalize-ticket ABC-123
```

Commits the solution, updates Linear, attaches the commit, and marks the issue Done.

### Understand and continue work

```text
/explain [topic]
```

Investigates and explains the issue, decision, severity, or architectural fit at the level needed to act.

```text
/handoff
```

Writes `handoff.md` so a fresh session can continue with the original task, completed work, remaining work, failed approaches, and current state.

```text
/reflect [timeframe]
```

Extracts durable principles from recent commits and Claude Code conversation history, then writes approved findings to memory or project instructions. Its history lookup is Claude Code-specific and needs adaptation on other hosts.

```text
/generate-readme [project path]
```

Explores a project, asks for missing audience or positioning decisions, and writes a storefront-style README.

### Choose a thinking framework

```text
/analyze-problem [situation]
```

Recommends the most relevant framework and whether external research would change the decision.

Twelve focused framework commands are available under [`commands/consider/`](commands/consider/):

- [`/consider:first-principles`](commands/consider/first-principles.md)
- [`/consider:5-whys`](commands/consider/5-whys.md)
- [`/consider:inversion`](commands/consider/inversion.md)
- [`/consider:second-order`](commands/consider/second-order.md)
- [`/consider:pareto`](commands/consider/pareto.md)
- [`/consider:eisenhower-matrix`](commands/consider/eisenhower-matrix.md)
- [`/consider:10-10-10`](commands/consider/10-10-10.md)
- [`/consider:swot`](commands/consider/swot.md)
- [`/consider:occams-razor`](commands/consider/occams-razor.md)
- [`/consider:one-thing`](commands/consider/one-thing.md)
- [`/consider:opportunity-cost`](commands/consider/opportunity-cost.md)
- [`/consider:via-negativa`](commands/consider/via-negativa.md)

---

## Optional bundles

### Hobby bundle

[`hobby-bundle/`](hobby-bundle/) is the original goal-driven web-project example. Its reusable worked artifacts include an agent-instructions template, the stack-specific playbook, a judged goal loop, and a goal-writing guide. It also contains 10 optional bundled skills:

- `agent-browser`
- `deploy-to-vercel`
- `diagnose`
- `grill-with-docs`
- `humanizer`
- `improve-codebase-architecture`
- `react-view-transitions`
- `vercel-composition-patterns`
- `vercel-react-best-practices`
- `web-design-guidelines`

Use [`bootstrap-goal-project`](#goal-driven-projects) to extract the general contracts for another stack. Install individual hobby skills only when their assumptions match the target project.

### Business bundle

[`business-bundle/`](business-bundle/) contains 12 offer and business-strategy lenses:

- `market-research`
- `business-model`
- `productize`
- `dfy-dwy-diy`
- `hormozi-offer`
- `audit-offer`
- `pricing-strategy`
- `landing-page-copy`
- `offer-angles`
- `objection-destroyer`
- `value-perception`
- `value-accelerator`

These are strategy lenses, not market evidence. Check pricing, demand, competitors, and channels against current research.

---

## Guides and repository layout

```text
skills/           19 primary skills, with bundled references, scripts, and assets
commands/         22 Claude-style command prompts, including 12 decision frameworks
agents/           the research-subagent definition used by research workflows
hobby-bundle/     goal-driven web-project example and optional web skills
business-bundle/  curated offer and business-strategy skills
docs/guides/      prompt, skill, agent, goal-loop, README, and web research guides
docs/pi/          Pi migration and feature notes; some runtime validation remains incomplete
site/             a small GitHub Pages/Jekyll reference site
```

### Prompting and agent design

- [Frontier LLM Prompting Guide](docs/guides/frontier-llm-prompting-guide.md): outcome-first prompting, approval boundaries, stop rules, grounding, validation, and legacy-prompt audit criteria.
- [GPT-5.5 Prompting Guide](docs/guides/gpt-5.5-prompting-guide.md)
- [GPT-5.6 Prompting Guide](docs/guides/gpt-5.6-prompting-guide.md)
- [Fable 5 Prompting Guide](docs/guides/fable-5-prompting-guide.md)
- [Prompt Quality Guide](docs/guides/prompt-quality-guide.md)
- [Skill Prompting Principles](docs/guides/skill-prompting-principles.md)
- [Subagent Prompting Guide](docs/guides/subagent-prompting-guide.md)
- [Building a Good Vertical Agent](docs/guides/building-good-vertical-agent.md)
- [Finding Your Unknowns](docs/guides/finding-your-unknowns.md)

### Skills, memory, and autonomous loops

- [Building Skills Guide](docs/guides/building-skills-guide.md)
- [Skill Description Guide](docs/guides/skill-description-guide.md)
- [Skill Discovery Pattern](docs/guides/skill-discovery-pattern.md)
- [Goal Loss Functions](docs/guides/goal-loss-functions.md)
- [Loop Guide](docs/guides/loop-guide.md)
- [Writing Effective CLAUDE.md](docs/guides/writing-effective-claude-md.md)

### Artifacts and web work

- [README Guide](docs/guides/readme-guide.md)
- [Nano Banana 2 Prompting Guide](docs/guides/nano-banana-2-prompting-guide.md)
- [The Unreasonable Effectiveness of HTML](docs/guides/the-unreasonable-effectiveness-of-html.md)
- [Website Scrape Consolidation Principles](docs/guides/website-scrape-consolidation-principles.md)

Additional official references, Pi notes, prompt snapshots, browser recording notes, and the YouTube upload-date ADR live under [`docs/`](docs/).

## Compatibility and known limitations

- Claude Code is the source format. Many skills refer to `~/.claude`, `.claude/settings.local.json`, Claude hooks, slash commands, `Task`, or `AskUserQuestion`. The install prompt asks the target agent to translate them, but some hosts will not have an equivalent.
- Pi support is not fully validated. [`docs/pi/`](docs/pi/) contains migration notes, and `package.json` contains Pi package metadata, but the declared root `prompts/` directory does not exist yet. Treat Pi installation as a guided port, not a verified package install.
- `install.js` remains for existing Claude Code setups. It needs Node 16.7 or newer and supports project or global scope, copy or symlink mode, conflict tracking, a manifest, and uninstall. It handles top-level agents, commands, skills, and a root `references/` directory when present. It does not install bundles, guides, or the site. This README uses the adaptive prompt instead.
- Confirmation rules vary by resource. Slack sends and schedules, and PR-comment triage, confirm before writing. Slack edit, delete, react, and status commands run immediately, as do some Linear mutations and Firebase deployment instructions.
- Research, image generation, Gmail, Linear, Slack, and EXA rely on credentials or external services. If an optional provider is missing, the skill should report reduced coverage instead of filling the gap with invented results.
- Most Python CLIs use `uv`. Some research paths also use `yt-dlp` or `claude -p`. App Icon Studio needs Node 18 or newer and uses macOS utilities for presentation. Browser QA needs `agent-browser` and suitable project fixtures.

## Updating

For symlink installs, pull from the stable checkout recorded in the installation manifest. Copied resources do not update automatically.

Run the installation prompt again and ask the agent to compare the recorded source revision and checksums with the installed files, preserve local edits, refresh the selected resources, update the manifest, and re-run path and dependency checks.

## License

[MIT](LICENSE)
