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

### `credits` — Check Firecrawl balance

No flags. Returns remaining credits and plan info.

**Output fields:** `remaining`, `plan`

---

### `config` — Show resolved configuration

No flags. Returns resolved API key status, persistence setting, and which env files were loaded.

**Output fields:** `persistence` (bool), `keys` (object with bool per service), `env_files` (list of paths with status)

---

## Important notes

- `--site`: a real domain name like `stripe.com` or `pay.uk` (NOT topics/phrases). Repeatable.
- `--recency`: preset window — `hour` | `day` | `week` | `month` | `year`. For custom ranges use `--after`/`--before` with YYYY-MM-DD dates.
- Also available as built-in tools: **WebSearch** (free, broad) and **WebFetch** (free, page summary).
