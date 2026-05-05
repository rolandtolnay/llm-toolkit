---
name: research
description: >
  Gather current information from the web using multiple sources in parallel.
  Use when the user needs facts, tools, best practices, or community opinions
  that may not be in training data. Triggers on: "search for", "look up",
  "find out", "what's the latest", "research".
hooks:
  PostToolUse:
    - matcher: "WebSearch|WebFetch"
      hooks:
        - type: command
          command: "uv run ~/.claude/skills/research/scripts/log-hook.py"
          timeout: 5
---

<objective>
Web research orchestration — find, verify, and structure information from online sources. Scales from quick single-source lookups to comprehensive multi-subagent investigations.

This skill handles **web research only**. Claude handles codebase exploration natively — don't use this skill for questions answerable from the local project.
</objective>

<cli_cheatsheet>
Quick syntax reference — all commands on one line each.

Script path: `~/.claude/skills/research/scripts/research.py`

```
uv run <script> ask "<query>"       [--site S] [--recency R] [--context C] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--no-cache]
uv run <script> search "<query>"    [--site S] [--recency R] [--limit N] [--no-cache]
uv run <script> reason "<query>"    [--site S] [--recency R] [--context C] [--effort E] [--no-cache]
uv run <script> docs <lib> "<query>" [--max-tokens N] [--no-cache]
uv run <script> map <url>           [--search KW] [--limit N] [--no-cache]
uv run <script> scrape <url>        [--no-cache]
uv run <script> credits
uv run <script> config
uv run <script> audit              [--days N] [--session S] [--detail]
uv run <script> prior "<query>"    [--since S] [--limit N] [--min-score N]

--site: a real domain name like stripe.com or pay.uk (NOT topics/phrases). Repeatable.
--recency: preset window — hour | day | week | month | year. For custom ranges use --after/--before with YYYY-MM-DD dates.
Cost: search ~$0.005 | ask/reason ~$0.02 | docs free | map/scrape 1 FC credit each | prior free (local)

Also available: WebSearch (free, broad), WebFetch (free, page summary)
All CLI calls and WebSearch/WebFetch usage are logged to ~/.cache/research/logs/YYYY-MM-DD.jsonl

YouTube script: `~/.claude/skills/research/scripts/youtube.py`

uv run <yt-script> search "<query>" [--question Q] [--max-videos N] [--after YYYY-MM-DD] [--no-preprocess] [--no-select]

Cost: free (yt-dlp + youtube-transcript-api, no API keys). Pre-processing uses Claude subscription (claude -p).
Requires: yt-dlp installed (brew install yt-dlp)

Social script: `~/.claude/skills/research/scripts/social.py`

uv run <social-script> reddit "<query>" [--question Q] [--subreddit S] [--no-cache]
uv run <social-script> shortform "<query>" [--no-cache]

Cost: ScrapeCreators PAYG (100 free calls, then pay-as-you-go). Condensing uses Claude subscription (claude -p).
Requires: SCRAPECREATORS_API_KEY in ~/.claude/research/.env
```
</cli_cheatsheet>

<complexity_assessment>
Before executing, assess query complexity:

**QUICK** — Simple factual question, single clear answer expected.
Examples: "what version of X is latest?", "does Y support Z?", "what's the URL for X?"
- No subagents. Run WebSearch directly (+ maybe one CLI call if WebSearch is insufficient).
- Single authoritative source is sufficient.

**STANDARD** — Moderate question, 2-3 information angles.
Examples: "how do I set up X?", "what tools exist for Y?", "how are people handling X?"
- 2-3 subagents in parallel.
- Source diversity rule applies (2+ sources per subagent).

**DEEP** — Complex multi-faceted question, many angles.
Examples: "best practices for X + Y", "evaluate X vs Y for our use case", "comprehensive guide to X"
- 3-4 subagents in parallel.
- Source diversity rule applies (2+ sources per subagent).

**YouTube availability**: When yt-dlp is installed, subagents can search YouTube for video content. Assign YouTube to subagents when the sub-question involves tutorials, demos, conference talks, developer workflows, product reviews, or practitioner opinions. Skip YouTube for API specs, pricing lookups, legal/compliance questions, or purely factual reference queries.

**Social availability**: When SCRAPECREATORS_API_KEY is configured, subagents can search Reddit (`social reddit`) and short-form video (`social shortform`). Assign Reddit when community opinions or real-world experiences add value. Assign shortform when trending/viral/consumer content is relevant. Skip for official docs, compliance questions, or purely factual lookups.
</complexity_assessment>

<quick_mode>
For QUICK complexity queries:

1. Run **WebSearch** with a well-crafted query
2. If the answer is clear and from an authoritative source (official docs, GitHub repo, well-known blog), **respond directly** — no subagents, no paid API calls
3. If WebSearch result is ambiguous or the source isn't authoritative:
   - Try `research search` for more targeted results
   - Or `research ask` for a synthesized answer
4. Verify any specific claims (version numbers, feature availability) against the primary source using WebFetch if needed

**Goal:** Resolve simple lookups fast and free. Don't spin up subagents for questions that are one Google search away.
</quick_mode>

<research_mode>
For STANDARD and DEEP complexity queries:

## STEP 1: DECOMPOSE

Analyze the question and generate 2-4 specific sub-questions. For each, assign a source strategy.

**Source assignment** — for each sub-question, consider which sources add unique value:

- **YouTube** (free): Would watching someone show, explain, or review this help?
  Tutorials, reviews, travel vlogs, cooking demos, talks, product walkthroughs, "what is X actually like?"
  Skip when: the answer is a fact, number, URL, or specification.
- **Reddit** (ScrapeCreators): Would hearing what real people experienced or recommend help?
  "Best X for Y", troubleshooting, honest opinions, local knowledge, community recommendations, "has anyone tried X?"
  Skip when: you need official/authoritative info, or the topic is too niche for active communities.
- **Short-form video** (ScrapeCreators): Is this about current trends, viral content, or quick visual takes?
  Trending products, consumer sentiment, cultural moments, "what are people saying about X right now?"
  Skip when: depth or nuance matters more than recency.

Priority: YouTube ≥ WebSearch > Reddit > short-form.
YouTube and WebSearch are free — prefer them when they cover the sub-question.
Use Reddit when community perspective adds value beyond what WebSearch captures.
Short-form is supplementary — assign only when trends/viral dimension is clearly relevant.

**Mandatory source rules:**
- At least one subagent must run **WebSearch** (broad discovery, free)
- Any finding about official features must be **verified against the canonical source**
- Each subagent must use **2+ independent sources**
- Trust hierarchy: **primary sources** (official docs, source code, author's post) > **secondary** (well-known blogs, curated lists) > **tertiary** (Perplexity synthesis, random forum posts)

## STEP 2: CONSULT PRIOR RESEARCH

Skip if the configured research directory does not exist (default: `~/Documents/Research/`; override with `RESEARCH_DIR`). Otherwise mandatory.

1. Run `research.py prior "<sub-question>"` once per decomposed sub-question.
   Add `--since 6m` for fast-moving topics (frameworks, APIs, market data).
2. If results returned:
   a. Read the top-scoring `role: angle` files first — they are shorter and
      directly comparable to your sub-question.
   b. Read matching `role: synthesis` files only when you need a decision-level
      summary or the angle files point to broader run context.
   c. Treat weak/default-threshold matches as leads, not coverage, until you read
      the file. Use `--min-score 0` only when you intentionally want broad recall.
   d. Treat research older than ~6 months on fast-moving topics as context, not authority.
3. Produce an explicit per-sub-question mapping before proceeding:
   - SQ-A "X pricing" → covered by `2026-03-12-x/02-pricing.md` → **DROP**
   - SQ-B "X rate limits" → partial: free tier only → **KEEP, narrow to paid**
   - SQ-C "X webhooks" → no prior coverage → **KEEP**
   - SQ-D "X auth rotation" → new angle from `2026-03-12-x/03-auth.md` → **ADD**
4. If no results → state so and proceed to Step 3.
5. Branch on the mapping:
   - All DROPPED → synthesize from prior files. No subagents. Cite prior files.
   - Some KEPT/ADDED → spawn subagents only for those. Paste relevant prior
     angle-file excerpts into prompts as verified context to extend.

Without the explicit mapping, this step degenerates into a glance.

## STEP 3: SPAWN SUBAGENTS

One **research-subagent** per sub-question, launched in **parallel** (use `subagent_type: "research-subagent"`). This agent type has PostToolUse hooks that log WebSearch/WebFetch calls for audit.

Sub-agents write their findings directly to files you assign. Do path coordination BEFORE spawning:

1. Generate the run-id: `YYYY-MM-DD-<3-5-word-kebab-slug>`.
2. Create the run directory: `~/Documents/Research/<run-id>/`.
3. For each sub-question, derive an angle slug (3-5 word kebab of the sub-question). Assemble target paths `<run-dir>/0N-<angle-slug>.md` starting at `01`.

Each subagent prompt must include:

```
You are a research subagent investigating: [specific sub-question]

First, read ~/.claude/skills/research/references/cli-reference.md for full CLI details.

TARGET PATH: <absolute path, e.g. /Users/you/Documents/Research/<run-id>/0N-<angle-slug>.md>

SOURCE STRATEGY: [which commands + built-in tools to use for THIS sub-question]

WRITE PROTOCOL:
- After research is complete, WRITE your findings to TARGET PATH as a markdown file.
- File must start with YAML frontmatter (schema in
  ~/.claude/skills/research/references/persistence-format.md) and be followed by the
  findings body with inline source citations, verbatim quotes where relevant, and
  notes on searches that turned up empty.
- Choose 3-7 specific, free-form tags that reflect the content (prefer specific
  nouns like "google-pay-iframe" over generic categories like "web").
- Your RETURN MESSAGE is a short summary only: one-line key finding, the tags you
  chose, your confidence level, and the source URLs you relied on. Do NOT paste the
  full findings body into your return — it lives in the file.

RULES:
- Use at least 2 independent sources
- Verify claims about official features against canonical sources (WebFetch or research scrape)
- If a CLI call fails, retry once with --no-cache, then note the failure and continue
- Note confidence level: verified (checked against primary source), likely (multiple secondary sources agree), unverified (single source)
```

**Cost escalation ladder** for assigning source strategies:

| Tier | Tools | When to use |
|------|-------|-------------|
| FREE | WebSearch, WebFetch, `research docs` | Always start here. Sufficient for well-documented topics. |
| FREE | `youtube search` (yt-dlp, no API key) | Tutorials, demos, talks, practitioner workflows. Needs yt-dlp. |
| FREE | `social reddit`, `social shortform` (ScrapeCreators PAYG) | Community opinions, trending content. Needs SCRAPECREATORS_API_KEY. |
| CHEAP | `research search` ($0.005), `research map` (1 FC credit), `research ask` (~$0.02) | When free sources lack depth or specificity. |
| MEDIUM | `research reason` (~$0.02), `research scrape` (1 FC credit) | For complex comparisons, when you need the full page content. |

Start subagents at the lowest cost tier that covers their sub-question. Escalate within the subagent only if cheaper sources are insufficient.

## STEP 4: SYNTHESIZE

After all subagents return:

1. **Cross-reference findings:**
   - When sources conflict, primary sources override secondary/tertiary
   - Flag contradictions explicitly in the response
   - Findings from a single source get lower confidence

2. **Confidence signaling** (not numeric scores):
   - Verified against official docs → state the source
   - From community discussion → note it's community-sourced
   - Single unverified source → flag as unverified

3. **Auto-detect output format:**
   - Comparison questions → table format
   - "Does X exist?" → lead with yes/no answer
   - "How do people feel about X?" → include sentiment distribution
   - Implementation questions → actionable steps with code examples
   - Tool/library discovery → structured list with links

4. **Cite sources** throughout the response. Every non-obvious claim should have a source.

## STEP 5: PERSIST

After synthesis, persist the run to disk. **First run `research config`** — if `persistence` is `false`, skip this step. Read `~/.claude/skills/research/references/persistence-format.md` for full format details.

The run directory already exists (created in STEP 3) and sub-agents have already written their angle files. Your job here is verification, synthesis, and indexing.

1. **Verify angle files.** Read each expected angle path. For any that are missing or malformed, write the file yourself from the sub-agent's text return and set `write_fallback: true` in the frontmatter.
2. **Write the synthesis.** Create `<run-dir>/00-synthesis.md` with the decision-oriented style described in the persistence-format reference. Short. Links to angle files for evidence. Do NOT duplicate finding bodies. Tags = union of angle tags + any synthesis-level additions.
3. **Prepend to INDEX.md.** Add a new entry at the top: title + date line, `**Tags:**` line, one bullet per angle file + one for the synthesis, each with a one-line finding.
4. **Return the user-facing answer.** Can be the synthesis body verbatim or a tighter version of it.

If any write fails, still return the research results to the user — persistence is best-effort, never blocking.
</research_mode>

<configuration>
## Env file configuration

The CLI loads skill-specific env files before reading API keys. This lets users set dedicated keys for the research skill without polluting their shell environment.

**File locations** (loaded in order — later files override earlier ones, and all override shell env):

| Priority | Path | Scope |
|----------|------|-------|
| 1 (lowest) | Shell environment | Global |
| 2 | `~/.claude/research/.env` | Skill-global |
| 3 (highest) | `.claude/research.env` (in project root) | Project-specific |

**Supported variables:**

```bash
# API Keys
PERPLEXITY_API_KEY=pplx-...
CONTEXT7_API_KEY=...
FIRECRAWL_API_KEY=fc-...
SCRAPECREATORS_API_KEY=...

# Settings
RESEARCH_NO_PERSIST=0    # Set to 1 to disable research output persistence
RESEARCH_DIR=~/Documents/Research  # Optional override for persisted research
```

Run `research config` to see resolved configuration (which keys are set, persistence status, which env files loaded).
</configuration>

<success_criteria>
- [ ] Contradictions between sources are flagged, not silently resolved
- [ ] Findings cite their sources
- [ ] Official tooling claims are verified against primary sources
- [ ] Every research run includes at least one WebSearch call (broad discovery)
- [ ] Standard/deep runs are persisted as per-run directories under the configured research directory (default: `~/Documents/Research/`) with angle files written by sub-agents, a decision-focused `00-synthesis.md` written by the orchestrator, and INDEX.md updated
- [ ] Prior research consulted via `research.py prior` (when the configured research directory exists), with an explicit drop/keep/add mapping per sub-question before any subagent spawns
- [ ] Quick lookups resolve without subagents when answer is clear
- [ ] Graceful degradation when API keys are missing
- [ ] YouTube search assigned to subagents where video content adds value
- [ ] Reddit/shortform assigned to subagents where community/trending content adds value
</success_criteria>
