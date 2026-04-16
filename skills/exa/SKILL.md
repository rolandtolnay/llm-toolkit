---
name: searchexa
description: >
  Semantic web search with inline page content via EXA API. Returns actual page
  text with results — search + fetch in one free call. Use for discovery when you
  need content, not just URLs. Free tier: 1000 searches/month.
  Triggers on: "exa search", "search with exa", "free web search", "searchexa".
---

<objective>
Free semantic web search that returns page content inline with results. Unlike Perplexity (which synthesizes answers) or Firecrawl (which scrapes single URLs), EXA combines discovery and content extraction in one call.

Use this when you need to find AND read pages — not when you need AI-synthesized answers (use research `ask` for that).
</objective>

<cli_cheatsheet>
Script path: `~/.claude/skills/searchexa/scripts/exa.py`

```
uv run <script> "<query>" [--limit N] [--site S] [--chars N] [--recency R]

--limit/-l:   Number of results (default 10)
--site/-s:    Restrict to domain, e.g. stripe.com (repeatable)
--chars/-c:   Max characters of page text per result (default 1500)
--recency/-r: Preset window — hour | day | week | month | year

Cost: Free (1000 searches/month)
```
</cli_cheatsheet>

<configuration>
Add `EXA_API_KEY=...` to `~/.claude/research/.env` (same file as Perplexity/Firecrawl keys).

Get a free key at https://exa.ai — no credit card required.
</configuration>

<when_to_use>
- Need page content, not just URLs or AI summaries
- Want search + fetch in a single call (faster than search → scrape)
- Free tier is sufficient (1000/month)
- Looking for blog posts, docs, tutorials, news articles

Do NOT use when:
- You need a synthesized answer → use research `ask`
- You need full-page markdown extraction → use research `scrape`
- You need library API docs → use research `docs`
</when_to_use>
