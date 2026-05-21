# Research CLI Reference

**CLI script:** `~/.claude/skills/research/scripts/research.py`

Run with: `uv run ~/.claude/skills/research/scripts/research.py <command> [options]`

All commands output JSON with a consistent envelope: `{ success, command, query, ..., metadata: { backend, cache_hit, ... } }`.

---

### `ask "<query>"` — Synthesized answer (~$0.02)

Perplexity sonar-pro. Returns a synthesized answer with inline citations.

| Flag | Default | Purpose |
|------|---------|---------|
| `--site` / `-s` | none | Filter to specific websites, e.g. `stripe.com` (repeatable) |
| `--recency` / `-r` | none | Preset window: `hour`, `day`, `week`, `month`, `year` |
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
| `--site` / `-s` | none | Filter to specific websites, e.g. `stripe.com` (repeatable) |
| `--recency` / `-r` | none | Preset window: `hour`, `day`, `week`, `month`, `year` |
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
| `--site` / `-s` | none | Filter to specific websites, e.g. `stripe.com` (repeatable) |
| `--recency` / `-r` | none | Preset window: `hour`, `day`, `week`, `month`, `year` |
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
| `--search` / `-k` | none | Filter URLs by keyword |
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

### `prior "<query>"` — Search prior research (free, local)

File-level token-overlap search across persisted research markdown files in the configured research directory (default: `~/Documents/Research/`; override with `RESEARCH_DIR`). Scans markdown frontmatter directly and enriches results with `INDEX.md` bullets when available. Searches tags, file titles, sub-questions, synthesis queries, run titles, and index bullets with normalized 0-1 scoring and compound-tag bonuses. `role: synthesis` files are included but slightly demoted so angle files remain the primary evidence layer.

| Flag | Default | Purpose |
|------|---------|---------|
| `--since` / `-s` | none | Date filter: `30d`, `6m`, `1y` |
| `--limit` / `-l` | 5 | Max results to return |
| `--min-score` | `0.15` | Minimum normalized relevance score. Use `0` for broad recall. |

**Output fields:** `results` (list of `{ file, title, role, run_id, run_title, date, sub_question, query, tags, confidence, sources, index_bullet, run_synthesis, score, matched_on }`)

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/research.py prior "tap to pay onboarding friction"
```

Output:
```json
{
  "success": true,
  "command": "prior",
  "query": "tap to pay onboarding friction",
  "results": [
    {
      "file": "/Users/.../2026-04-29-tap-to-pay-onboarding-deep-dive/01-competitor-onboarding-ux-gotchas.md",
      "title": "Tap-to-pay competitor onboarding UX, gotchas, and developer pain points",
      "role": "angle",
      "run_id": "2026-04-29-tap-to-pay-onboarding-deep-dive",
      "run_title": "Tap-to-Pay Onboarding Deep Dive: Competitors, Friction, Sentiment & Unknowns",
      "date": "2026-04-29",
      "sub_question": "What are the specific onboarding and setup flows of major tap-to-pay / SoftPOS competitors?",
      "query": "",
      "tags": ["tap-to-pay-onboarding", "softpos-ux"],
      "confidence": "likely",
      "sources": [{"url": "https://docs.stripe.com/terminal", "role": "primary"}],
      "index_bullet": "SumUp/Square: minutes to first payment. Adyen/Worldline: days-weeks.",
      "run_synthesis": "/Users/.../2026-04-29-tap-to-pay-onboarding-deep-dive/00-synthesis.md",
      "score": 0.6401,
      "matched_on": ["tags:tap-to-pay-onboarding", "title:onboarding,pay,tap", "sub_question:onboarding,pay,tap"]
    }
  ],
  "metadata": {"backend": "local", "duration_ms": 45, "search_unit": "file", "total_files_indexed": 125, "min_score": 0.15}
}
```

---

## YouTube CLI

**CLI script:** `~/.claude/skills/research/scripts/youtube.py`

Run with: `uv run ~/.claude/skills/research/scripts/youtube.py <command> [options]`

**Prerequisite:** `SCRAPECREATORS_API_KEY` enables the Primary Backend. Install `yt-dlp` (`brew install yt-dlp`) to enable the Free Fallback Backend when the key is missing or ScrapeCreators fails.

---

### `search "<query>"` — YouTube search + transcript extraction

Search YouTube via ScrapeCreators when `SCRAPECREATORS_API_KEY` is configured, falling back to yt-dlp plus youtube-transcript-api when ScrapeCreators is unavailable or fails. Long transcripts can be pre-processed through `claude -p` for directed extraction. ScrapeCreators calls are cached by default: search for 24h and transcripts for 30d.

| Flag | Default | Purpose |
|------|---------|---------|
| `--question` / `-q` | none | Research sub-question for directed transcript extraction |
| `--max-videos` / `-v` | `10` | Max videos to inspect/return; under ScrapeCreators this caps first-page normalized results, not a guarantee |
| `--after` | none | Upload-date filter: `today`, `this_week`, `this_month`, `this_year` |
| `--no-preprocess` | false | Skip claude extraction, return raw transcripts only |
| `--no-select` | false | Skip LLM selection, use top videos by views |

**Intelligent selection:** When `--question` is provided and more than 3 videos are returned, an LLM (`claude -p`, Opus) evaluates search results and selects which videos to transcribe based on relevance, source quality, and unique value — rather than just picking by view count. With ≤3 results, all are fetched. Pass `--no-select` to skip LLM selection and use top-by-views fallback.

**Pre-processing:** Transcripts with 1500+ words are automatically extracted via `claude -p --model sonnet` using the `--question` to direct extraction. Below 1500 words, the raw transcript is returned. Up to 3 transcripts are pre-processed in parallel. Omit `--question` or pass `--no-preprocess` to skip.

**Output fields:**
- `videos` — list of video objects, each with:
  - `video_id`, `title`, `channel`, `upload_date` (YYYY-MM-DD), `url`, `view_count`, `like_count`, `duration` (seconds), `description_preview`
  - `selected` (bool) — whether this video was selected for transcription
  - `selection_reason` (string, only for LLM-selected videos) — why this video was chosen
  - `transcript_available` (bool)
  - `extraction` (string, if pre-processed) OR `raw_transcript` (string, if below threshold or `--no-preprocess`)
  - `word_count`, `preprocessed` (bool)
- `metadata` — `backend` (`scrapecreators` | `yt-dlp` | `mixed`), `videos_searched`, `videos_selected`, `transcripts_fetched`, `transcripts_preprocessed`, `selection_method` (`llm` | `top_by_views` | `all`), `warnings`, `cache_hit`

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/youtube.py search "SwiftUI navigation patterns 2026" --question "What navigation patterns are recommended for complex SwiftUI apps?" --max-videos 10 --after this_year
```

---

## Social CLI

**CLI script:** `~/.claude/skills/research/scripts/social.py`

Run with: `uv run ~/.claude/skills/research/scripts/social.py <command> [options]`

**Prerequisite:** `SCRAPECREATORS_API_KEY` must be set in `~/.claude/research/.env` or shell environment.

---

### `reddit "<query>"` — Reddit thread search + comments (ScrapeCreators PAYG)

Search Reddit globally or within a subreddit. Returns up to 7 top threads ranked by blended relevance + upvote score, each with up to 10 quality-filtered comments. Optionally condenses findings via `claude -p` when content exceeds 2500 words.

When no `--subreddit` is passed, a discovery pass scores which subreddits the global hits cluster into and runs targeted follow-up searches inside the top 3, merging the results before ranking. Costs 1 ScrapeCreators credit per discovered sub (so a typical call uses 4 search credits + 1 per thread enriched with comments).

| Flag | Default | Purpose |
|------|---------|---------|
| `--question` / `-q` | none | Research question — triggers condensing when comment volume is high |
| `--subreddit` / `-s` | none | Limit search to a specific subreddit (without `r/` prefix). Also disables the discovery pass. |
| `--no-cache` | false | Bypass cache |

**Comment filter:** Comments shorter than 30 characters or matching low-value patterns (`this`, `agreed`, `lol`, `thanks`, etc.) are dropped before the top-10 selection, so returned `comments[]` slots aren't wasted on one-word reactions.

**Condensing:** When `--question` is provided and total comment text exceeds 2500 words, threads are condensed via `claude -p --model sonnet` to extract consensus views, contrarian opinions, specific mentions, and notable quotes.

**Output fields:**
- `threads` — list of thread objects, each with:
  - `title`, `url`, `subreddit`, `date` (YYYY-MM-DD), `score`, `num_comments`, `selftext` (first 500 chars)
  - `comments` — list of top 10 comments by score (after quality filter), each with:
    - `author`, `score`, `excerpt` (300 chars at word boundary)
    - `top_reply` — highest-scored reply (`{ author, score, excerpt }`) or `null`
- `condensed` — bulleted findings string (when condensing triggered) or `null`
- `metadata` — `backend`, `threads_found`, `threads_returned`, `discovered_subreddits` (list of sub names searched in the follow-up pass), `discovery_skipped` (bool — true when `--subreddit` was passed), `condensed` (bool), `cache_hit`

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/social.py reddit "best React navigation library" --question "What do developers recommend?" --subreddit reactjs
```

---

### `shortform "<query>"` — TikTok + Instagram Reels search (ScrapeCreators PAYG)

Search TikTok and Instagram Reels in parallel, interleave top 3 from each, and fetch transcripts/captions. Items with captions under 30 words are filtered as noise.

| Flag | Default | Purpose |
|------|---------|---------|
| `--no-cache` | false | Bypass cache |

**Output fields:**
- `items` — interleaved list (TT1/IG1/TT2/IG2/TT3/IG3), each with:
  - `platform` (`tiktok` | `instagram`), `video_id`, `text` (description), `url`, `author`
  - `views`, `likes`, `duration` (seconds)
  - `caption` — transcript or description, max 500 words
- `metadata` — `backend`, `tiktok_found`, `instagram_found`, `items_returned`, `captions_fetched`, `cache_hit`

**Example:**
```bash
uv run ~/.claude/skills/research/scripts/social.py shortform "trending AI tools"
```

---

### `credits` — Check Firecrawl balance

No flags. Returns remaining credits and plan info.

**Output fields:** `remaining`, `plan`

---

### `config` — Show resolved configuration

No flags. Returns resolved API key status, persistence setting, and which env files were loaded.

**Output fields:** `persistence` (bool), `keys` (object with bool per service), `env_files` (list of paths with status), `research_dir`

---

## Important notes

- `--site`: a real domain name like `stripe.com` or `pay.uk` (NOT topics/phrases). Repeatable.
- `--recency`: preset window — `hour` | `day` | `week` | `month` | `year`. For custom ranges use `--after`/`--before` with YYYY-MM-DD dates.
- Also available as built-in tools: **WebSearch** (free, broad) and **WebFetch** (free, page summary).
- YouTube search uses ScrapeCreators as the Primary Backend when `SCRAPECREATORS_API_KEY` is configured; install `yt-dlp` locally (`brew install yt-dlp`) for the Free Fallback Backend.
- YouTube `--after` accepts only `today`, `this_week`, `this_month`, or `this_year`; exact `YYYY-MM-DD` values are rejected.
- YouTube video selection uses `claude -p` (Opus, Claude subscription). Pass `--no-select` to skip.
- YouTube transcript pre-processing uses `claude -p --model sonnet` (Claude subscription, no API key). Pass `--no-preprocess` to skip.
- Social search, short-form search, and primary YouTube research use `SCRAPECREATORS_API_KEY` set in `~/.claude/research/.env`
- Reddit condensing uses `claude -p --model sonnet` (Claude subscription). Only triggers when `--question` provided and content exceeds 2500 words.
