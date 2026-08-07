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

Script path: `~/.agents/skills/research/scripts/research.py`

```
uv run <script> ask "<query>"       [--site S] [--recency R] [--context C] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--no-cache]
uv run <script> search "<query>"    [--site S] [--recency R] [--limit N] [--no-cache]
uv run <script> google "<query>"    [--region CC] [--recency R] [--page N] [--no-cache]
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
Cost: search ~$0.005 | ask/reason ~$0.02 | google 1 SC credit | docs free | map/scrape 1 FC credit each | prior free (local)

Also available: WebSearch (free, broad), WebFetch (free, page summary)
All CLI calls and WebSearch/WebFetch usage are logged to ~/.cache/research/logs/YYYY-MM-DD.jsonl

YouTube script: `~/.agents/skills/research/scripts/youtube.py`

uv run <yt-script> search "<query>" [--question Q] [--max-videos N] [--after today|this_week|this_month|this_year] [--no-preprocess] [--no-select]
uv run <yt-script> transcript <url> [--no-cache]
uv run <yt-script> comments <url>   [--order top|newest] [--limit N] [--cursor C] [--no-cache]

Cost: ScrapeCreators PAYG when `SCRAPECREATORS_API_KEY` is configured (search cached 24h, transcripts 30d); otherwise free fallback via yt-dlp + youtube-transcript-api (`comments` has no free fallback). Pre-processing uses Claude subscription (claude -p).
Notes: `--after` only accepts `today`, `this_week`, `this_month`, `this_year`; `--max-videos` is a cap under ScrapeCreators first-page search; `metadata.backend` reports `scrapecreators`, `yt-dlp`, or `mixed`.

Social script: `~/.agents/skills/research/scripts/social.py`

uv run <social-script> reddit "<query>" [--question Q] [--subreddit S] [--timeframe all|day|week|month|year] [--sort relevance|new|top|comment_count] [--max-threads N] [--no-cache]
uv run <social-script> thread <url>     [--max-comments N] [--cursor C] [--no-cache]
uv run <social-script> shortform "<query>" [--no-cache]

Reddit search defaults to the full archive (--timeframe all); narrow only when recency matters. `thread` fetches one thread at full fidelity (post body + nested comments).
Requires: SCRAPECREATORS_API_KEY in ~/.claude/research/.env. ScrapeCreators credits are abundant — use SC-backed commands freely whenever they fit the question; every response reports actual credits used.
```
</cli_cheatsheet>

<complexity_assessment>
Before executing, assess query complexity:

**QUICK** — Simple factual question, single clear answer expected.
Examples: "what version of X is latest?", "does Y support Z?", "what's the URL for X?"
- No subagents. Answer from one or two direct lookups.

**STANDARD** — Moderate question, 2-3 information angles.
Examples: "how do I set up X?", "what tools exist for Y?", "how are people handling X?"
- 2-3 subagents in parallel.

**DEEP** — Complex multi-faceted question, many angles.
Examples: "best practices for X + Y", "evaluate X vs Y for our use case", "comprehensive guide to X"
- 3-4 subagents in parallel.
</complexity_assessment>

<quick_mode>
For QUICK complexity queries, resolve the lookup directly — no subagents, no run directory. Start with the tool that best fits the question (WebSearch or `research google` for discovery, `research docs` for library APIs, WebFetch/`research scrape` for a known page), and verify version numbers or feature claims against the primary source before answering. Done means: the answer comes from an authoritative source and specific claims are verified.
</quick_mode>

<research_mode>
For STANDARD and DEEP complexity queries:

## STEP 1: DECOMPOSE

Analyze the question and generate 2-4 specific sub-questions. For each, assign a source strategy by fit — which surfaces would a capable human researcher actually consult for this sub-question? Combine official and community surfaces when both carry signal (e.g. legal research: official sources for the rules, communities for how they play out in practice).

**Source menu** (cost is not a selection criterion — ScrapeCreators credits are abundant and Perplexity calls cost cents; pick whatever fits):

- **Broad discovery**: WebSearch, `research google` (real Google SERP; `--region` for country-specific topics), `research search` (Perplexity ranking). Different engines surface different results — use a second engine when the first pass looks thin.
- **Official/primary sources**: WebFetch a known page, `research scrape` when pages are JS-heavy or block fetching, `research map` to find pages on a site, `research docs` for library APIs.
- **Synthesis and reasoning**: `research ask` / `research reason` (Perplexity). Useful as a supplementary triangulation pass — treat output as tertiary evidence, never as the sole source for a claim.
- **YouTube**: `youtube search` when watching someone show, explain, or review would help (tutorials, talks, product reviews, "what is X actually like?"); `youtube transcript <url>` when a specific video is already known; `youtube comments <url>` for community corrections under a video you've used as evidence.
- **Reddit**: `social reddit` when real people's experiences and recommendations matter ("best X for Y", troubleshooting, local knowledge, "has anyone tried X?"). Defaults to all-time search; add `--timeframe` only when recency genuinely matters. Follow up with `social thread <url>` to read a promising thread in full.
- **Short-form video**: `social shortform` only when trends/viral consumer sentiment is clearly relevant.

**Evidence rules** (apply to every subagent):
- Use 2+ independent sources per sub-question; verify claims about official features, prices, or laws against the canonical source.
- Trust hierarchy: **primary sources** (official docs, source code, author's post) > **secondary** (well-known blogs, curated lists) > **tertiary** (Perplexity synthesis, random forum posts).
- Every run includes at least one broad discovery pass so unknown-unknowns can surface.

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

First, read ~/.agents/skills/research/references/cli-reference.md for full CLI details.

TARGET PATH: <absolute path, e.g. /Users/you/Documents/Research/<run-id>/0N-<angle-slug>.md>

SOURCE STRATEGY: [which commands + built-in tools fit THIS sub-question, and why]

WRITE PROTOCOL:
- Write your findings to TARGET PATH: YAML frontmatter (schema in
  ~/.agents/skills/research/references/persistence-format.md) followed by the findings
  body with inline citations, verbatim quotes where relevant, and 3-7 specific tags.
- Your RETURN MESSAGE is a short summary only: one-line key finding, tags, confidence
  level, source URLs. Do NOT paste the full findings body — it lives in the file.
```

Include relevant prior-research excerpts (from STEP 2) as verified context to extend. Source depth is not rationed — subagents should pull full transcripts, full threads, and scraped pages whenever that evidence fits the sub-question, and stop when the sub-question is answered with cited evidence, not when a budget runs out.

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

After synthesis, persist the run to disk. **First run `research config`** — if `persistence` is `false`, skip this step. Read `~/.agents/skills/research/references/persistence-format.md` for full format details.

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
- [ ] Findings cite their sources; official claims verified against primary sources
- [ ] Community surfaces (YouTube, Reddit) consulted wherever practitioner or owner experience adds value, not just web search
- [ ] Standard/deep runs are persisted as per-run directories under the configured research directory (default: `~/Documents/Research/`) with angle files written by sub-agents, a decision-focused `00-synthesis.md` written by the orchestrator, and INDEX.md updated
- [ ] Prior research consulted via `research.py prior` (when the configured research directory exists), with an explicit drop/keep/add mapping per sub-question before any subagent spawns
- [ ] Quick lookups resolve without subagents when the answer is clear
- [ ] Provider failures are reported as failures — an errored source is never presented as "no evidence found"
</success_criteria>
