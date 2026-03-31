---
name: research
description: >
  Gather current information from the web using multiple sources in parallel.
  Use when the user needs facts, tools, best practices, or community opinions
  that may not be in training data. Triggers on: "search for", "look up",
  "find out", "what's the latest", "research".
---

<objective>
Web research orchestration — find, verify, and structure information from online sources. Scales from quick single-source lookups to comprehensive multi-subagent investigations.

This skill handles **web research only**. Claude handles codebase exploration natively — don't use this skill for questions answerable from the local project.
</objective>

<cli_reference>
**CLI script:** `~/.claude/skills/research/scripts/research.py`

Run with: `uv run ~/.claude/skills/research/scripts/research.py <command> [options]`

All commands output JSON with a consistent envelope: `{ success, command, query, ..., metadata: { backend, cache_hit, ... } }`.

---

### `ask "<query>"` — Synthesized answer (~$0.02)

Perplexity sonar-pro. Returns a synthesized answer with inline citations.

| Flag | Default | Purpose |
|------|---------|---------|
| `--domain` / `-d` | none | Filter to specific domains (repeatable) |
| `--recency` / `-r` | none | Recency filter: `day`, `week`, `month`, `year` |
| `--context` / `-c` | `high` | Search context size: `low`, `medium`, `high` |
| `--after` | none | Only results after date (YYYY-MM-DD) |
| `--before` | none | Only results before date (YYYY-MM-DD) |
| `--no-cache` | false | Bypass cache |

**Output fields:** `answer` (string), `citations` (list of URLs)

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/research.py ask "what is the latest version of React"
```

---

### `search "<query>"` — Raw search results (~$0.005)

Perplexity Search API. Returns URLs + titles + snippets. Best for broad discovery.

| Flag | Default | Purpose |
|------|---------|---------|
| `--domain` / `-d` | none | Filter to specific domains (repeatable) |
| `--recency` / `-r` | none | Recency filter: `day`, `week`, `month`, `year` |
| `--limit` / `-l` | 10 | Max results |
| `--no-cache` | false | Bypass cache |

**Output fields:** `results` (list of `{ url, title, snippet }`)

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/research.py search "shadcn claude code skill"
```

---

### `reason "<query>"` — Deep reasoning (~$0.02)

Perplexity sonar-reasoning-pro. Chain-of-thought reasoning with web search. Use for complex comparisons, evaluations, and multi-step questions.

| Flag | Default | Purpose |
|------|---------|---------|
| `--domain` / `-d` | none | Filter to specific domains (repeatable) |
| `--recency` / `-r` | none | Recency filter: `day`, `week`, `month`, `year` |
| `--context` / `-c` | `high` | Search context size: `low`, `medium`, `high` |
| `--effort` / `-e` | `high` | Reasoning effort: `low`, `medium`, `high` |
| `--no-cache` | false | Bypass cache |

**Output fields:** `answer` (string), `citations` (list of URLs)

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/research.py reason "compare Redis vs DragonflyDB for caching"
```

---

### `docs <library> "<query>"` — Library documentation (free)

Context7 API. Version-aware, authoritative documentation. Use for API signatures, config options, usage patterns.

| Flag | Default | Purpose |
|------|---------|---------|
| `--max-tokens` / `-t` | 5000 | Max response tokens |
| `--no-cache` | false | Bypass cache |

**Output fields:** `results` (list of `{ title, content, source_url, type }`)

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/research.py docs react "useCallback signature"
```

---

### `map <url>` — Discover URLs on a site (1 Firecrawl credit)

Firecrawl map. Discover all pages on a site, optionally filtered by keyword. Use to find specific pages before scraping.

| Flag | Default | Purpose |
|------|---------|---------|
| `--search` / `-s` | none | Filter URLs by keyword |
| `--limit` / `-l` | 100 | Max URLs to return |
| `--no-cache` | false | Bypass cache |

**Output fields:** `discovered_urls` (list of `{ url, title }`)

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/research.py map https://ui.shadcn.com --search "claude"
```

---

### `scrape <url>` — Extract page content (1 Firecrawl credit)

Firecrawl scrape. Extracts page content as clean markdown. Use to verify claims against primary sources.

| Flag | Default | Purpose |
|------|---------|---------|
| `--no-cache` | false | Bypass cache |

**Output fields:** `content` (markdown string), `url`, `title`

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/research.py scrape https://ui.shadcn.com/docs/skills
```

---

### `credits` — Check Firecrawl balance

No flags. Returns remaining credits and plan info.

**Output fields:** `remaining`, `plan`

---

### `config` — Show resolved configuration

No flags. Returns resolved API key status, persistence setting, and which env files were loaded.

**Output fields:** `persistence` (bool), `keys` (object with bool per service), `env_files` (list of paths with status)

</cli_reference>

<cli_cheatsheet>
Quick reference for subagent prompts — all commands on one line each.

Script path: `~/.claude/skills/research/scripts/research.py`

```
uv run <script> ask "<query>"       [--domain D] [--recency R] [--context C] [--after D] [--before D] [--no-cache]
uv run <script> search "<query>"    [--domain D] [--recency R] [--limit N] [--no-cache]
uv run <script> reason "<query>"    [--domain D] [--recency R] [--context C] [--effort E] [--no-cache]
uv run <script> docs <lib> "<query>" [--max-tokens N] [--no-cache]
uv run <script> map <url>           [--search KW] [--limit N] [--no-cache]
uv run <script> scrape <url>        [--no-cache]
uv run <script> credits
uv run <script> config

--recency values: day | week | month | year (no other formats accepted)
Cost: search ~$0.005 | ask/reason ~$0.02 | docs free | map/scrape 1 FC credit each

Also available: WebSearch (free, broad), WebFetch (free, page summary)
```
</cli_cheatsheet>

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
- Full source diversity + verification.
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

One **general-purpose subagent** per sub-question, launched in **parallel**.

Each subagent prompt must include:

```
You are a research subagent investigating: [specific sub-question]

[CLI cheatsheet from <cli_cheatsheet>]

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

After synthesis, persist the research to disk. **First run `research config`** — if `persistence` is `false`, skip this step. See `<persistence>` for full format details:

1. **Write the research file** to `~/.claude/research/YYYY-MM-DD-<slug>.md` containing:
   - Header with topic, date, and original query
   - One section per sub-question with its findings as-is from the sub-agent return
   - Final synthesis section with the orchestrator's combined answer
2. **Prepend an entry to `~/.claude/research/INDEX.md`** with one line per sub-question linking to the file with anchor

If the write fails, still return the research results to the user — persistence is best-effort, never blocking.
</research_mode>

<persistence>
## Output persistence

STANDARD and DEEP research runs are persisted to `~/.claude/research/` so paid API results are never lost. QUICK lookups are NOT persisted.

**Opt-out:** Set `RESEARCH_NO_PERSIST=1` in an env file (see `<configuration>`) or shell to disable persistence.

### File structure

```
~/.claude/research/
  INDEX.md                              # Scannable topic index
  2026-03-30-bank-account-verification.md
  2026-03-31-nextjs-auth-patterns.md
```

**File naming:** `YYYY-MM-DD-<slug>.md` — slug is a short kebab-case summary of the query (3-5 words max).

### Research file format

```markdown
# <Research Topic>
**Date:** YYYY-MM-DD
**Query:** <original user question>

---

## <Sub-question 1 heading>
**Source strategy:** <commands used>
**Confidence:** <verified | likely | unverified>

<sub-agent findings with citations — written as-is from the sub-agent return>

---

## <Sub-question 2 heading>
...

---

## Synthesis

<orchestrator's final synthesized answer with citations>
```

Sub-question headings should be descriptive topic labels (e.g., "Compliance Requirements & Regulations"), not generic names like "Sub-agent 1". These headings become anchor targets for the index.

### INDEX.md format

Each research run gets a heading with its sub-questions listed individually. This makes the index a topic discovery tool — readers can scan all angles covered across all past research.

```markdown
# Research Index

### Bank Account Verification Best Practices — 2026-03-30
- [Compliance requirements & regulations](2026-03-30-bank-account-verification.md#compliance-requirements--regulations)
- [Backend architecture & implementation patterns](2026-03-30-bank-account-verification.md#backend-architecture--implementation-patterns)
- [Competitor approaches to verification](2026-03-30-bank-account-verification.md#competitor-approaches-to-verification)

### Next.js Auth Patterns — 2026-03-28
- [Official Next.js auth support](2026-03-28-nextjs-auth-patterns.md#official-nextjs-auth-support)
- [Community patterns & libraries](2026-03-28-nextjs-auth-patterns.md#community-patterns--libraries)
```

**Anchor format:** GitHub-style — lowercase, spaces→hyphens, strip special chars except hyphens. E.g., heading `## Compliance Requirements & Regulations` → anchor `#compliance-requirements--regulations`.

Prepend new entries at the top of INDEX.md (most recent first). Create `~/.claude/research/` and `INDEX.md` if they don't exist.
</persistence>

<success_criteria>
- [ ] Quick lookups resolve without subagents when answer is clear
- [ ] Standard/deep research spawns parallel subagents
- [ ] Every research run includes at least one WebSearch call (broad discovery)
- [ ] Official tooling claims are verified against primary sources
- [ ] Contradictions between sources are flagged, not silently resolved
- [ ] Findings cite their sources
- [ ] Graceful degradation when API keys are missing
- [ ] Standard/deep runs are persisted to `~/.claude/research/` with INDEX.md updated
- [ ] Quick lookups are NOT persisted
</success_criteria>
