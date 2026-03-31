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

--site: a real domain name like stripe.com or pay.uk (NOT topics/phrases). Repeatable.
--recency: preset window — hour | day | week | month | year. For custom ranges use --after/--before with YYYY-MM-DD dates.
Cost: search ~$0.005 | ask/reason ~$0.02 | docs free | map/scrape 1 FC credit each

Also available: WebSearch (free, broad), WebFetch (free, page summary)
All CLI calls and WebSearch/WebFetch usage are logged to ~/.cache/research/logs/YYYY-MM-DD.jsonl
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

**Angles checklist** (not rigid — pick what's relevant):
- Does this question have an **official tooling/docs** dimension?
- Does it have a **community experience** dimension?
- Does it have an **ecosystem/third-party** dimension?
- Does it have an **implementation/how-to** dimension?

**Mandatory source rules:**
- At least one subagent must run **WebSearch** (broad discovery, free)
- Any finding about official features must be **verified against the canonical source**
- Each subagent must use **2+ independent sources**
- Trust hierarchy: **primary sources** (official docs, source code, author's post) > **secondary** (well-known blogs, curated lists) > **tertiary** (Perplexity synthesis, random forum posts)

## STEP 2: SPAWN SUBAGENTS

One **research-subagent** per sub-question, launched in **parallel** (use `subagent_type: "research-subagent"`). This agent type has PostToolUse hooks that log WebSearch/WebFetch calls for audit.

Each subagent prompt must include:

```
You are a research subagent investigating: [specific sub-question]

First, read ~/.claude/skills/research/references/cli-reference.md for full CLI details.

SOURCE STRATEGY: [which commands + built-in tools to use for THIS sub-question]

RULES:
- Use at least 2 independent sources
- Verify claims about official features against canonical sources (WebFetch or research scrape)
- If a CLI call fails, retry once with --no-cache, then note the failure and continue
- Return findings with sources cited
- Note confidence level: verified (checked against primary source), likely (multiple secondary sources agree), unverified (single source)
```

**Cost escalation ladder** for assigning source strategies:

| Tier | Tools | When to use |
|------|-------|-------------|
| FREE | WebSearch, WebFetch, `research docs` | Always start here. Sufficient for well-documented topics. |
| CHEAP | `research search` ($0.005), `research map` (1 FC credit), `research ask` (~$0.02) | When free sources lack depth or specificity. |
| MEDIUM | `research reason` (~$0.02), `research scrape` (1 FC credit) | For complex comparisons, when you need the full page content. |

Start subagents at the lowest cost tier that covers their sub-question. Escalate within the subagent only if cheaper sources are insufficient.

## STEP 3: SYNTHESIZE

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

## STEP 4: PERSIST

After synthesis, persist the research to disk. **First run `research config`** — if `persistence` is `false`, skip this step. Read `~/.claude/skills/research/references/persistence-format.md` for full format details.

1. **Write the research file** to `~/Documents/Research/YYYY-MM-DD-<slug>.md` containing:
   - Header with topic, date, and original query
   - One section per sub-question with its findings as-is from the sub-agent return
   - Final synthesis section with the orchestrator's combined answer
2. **Prepend an entry to `~/Documents/Research/INDEX.md`** with one line per sub-question linking to the file with anchor

If the write fails, still return the research results to the user — persistence is best-effort, never blocking.
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

# Settings
RESEARCH_NO_PERSIST=0    # Set to 1 to disable research output persistence
```

Run `research config` to see resolved configuration (which keys are set, persistence status, which env files loaded).
</configuration>

<success_criteria>
- [ ] Contradictions between sources are flagged, not silently resolved
- [ ] Findings cite their sources
- [ ] Official tooling claims are verified against primary sources
- [ ] Every research run includes at least one WebSearch call (broad discovery)
- [ ] Standard/deep runs are persisted to `~/Documents/Research/` with INDEX.md updated
- [ ] Quick lookups resolve without subagents when answer is clear
- [ ] Graceful degradation when API keys are missing
</success_criteria>
