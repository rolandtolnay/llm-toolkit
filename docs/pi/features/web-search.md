# Web Search

## What This Replaces

Claude Code's `WebSearch` and `WebFetch` tools — the ability to search the web and fetch page content during a task. Used for looking up documentation, verifying API behavior, finding current information.

## Why I Need It

Many tasks require current information: checking library APIs, finding error solutions, verifying behavior that may have changed since the model's training cutoff. Without this, the model either hallucinates or asks me to look things up manually.

Key behaviors:
- Search query → list of results with titles, URLs, snippets
- Fetch a specific URL → page content (text extracted from HTML)
- Reasonable result truncation (don't dump entire pages into context)

## Pi API Surface

Pi ships with only 4 core tools: `read`, `write`, `edit`, `bash`. There is no built-in web search. Three implementation approaches exist:

**Extension registering a custom tool:**
- `pi.registerTool()` with name, parameters (TypeBox schema), and async execute function
- The execute function can shell out, call APIs, or do anything Node.js can do
- Returns `{ content: [{ type: "text", text: "..." }], details: {} }`

**MCP server (native support):**
- Pi has native MCP support via `.mcp.json` in project root or `~/.pi/agent/mcp.json` globally
- MCP tools appear as regular tools to the model — no extension code needed
- Config is just a JSON file pointing at MCP server commands

**Skill wrapping a CLI tool:**
- SKILL.md instructs the model to use `bash` with a CLI search tool (`ddgr`, `curl`, etc.)
- No code at all, but the model must parse raw output and results are less structured

## Research Findings

### Recommended: Codex CLI Delegation (~15 lines)

Delegates web search to OpenAI's Codex CLI built-in search tool. When authenticated via `codex login` (ChatGPT OAuth), search is included in the subscription quota — no separate API keys or credits.

**How Codex search works:**
- Codex has a first-party web search tool baked into its agent loop
- Default mode (`cached`) serves results from an OpenAI-maintained web index — fast, lower prompt injection risk
- Live mode (`--search` flag) fetches real-time results from the web
- `codex exec` runs non-interactive: streams activity to stderr, final answer to stdout
- `--full-auto` skips approval prompts (safe here since we only ask for search, no file writes)
- `--json` gives JSONL events including `web_search` tool calls with queries and snippets

**Tradeoffs:**
- ~3-8s latency per search (spawns Codex process, runs full agent loop with GPT model call)
- Consumes subscription tokens (input + search context + output) — effectively free if not hitting quota ceiling
- Returns synthesized text, not raw search results — Codex reasons over the results before responding
- No way to get raw search results only; `codex exec` always runs the full agent loop

**Implementation:** See [onboarding.md §8](../onboarding.md#8-features-to-install) for the full extension code.

```typescript
// .pi/extensions/codex-search.ts — core pattern
const result = execSync(
  `codex exec --search --full-auto "Search the web for: ${query}. Return only factual findings with source URLs. Do not write any code."`,
  { timeout: 30000, encoding: "utf-8" }
);
```

### Alternative: MCP-Direct (Brave, Perplexity, Exa)

Pi's native MCP support means you can connect any MCP search server with zero extension code — just a `.mcp.json` config file. The MCP tools appear as regular tools to the model.

**Brave Search MCP:**
- Requires Brave Search API key (free tier: 2000 queries/month)
- Returns structured search results with titles, URLs, snippets
- Lowest latency (~1-2s), most predictable

**Perplexity MCP:**
- Requires Perplexity API key (pay-per-query, ~$0.005/search, ~$0.02/ask)
- Returns AI-synthesized answers with citations — similar quality to Codex delegation
- Also provides `perplexity_reason` for complex analysis

**Exa MCP:**
- Exa is what Codex itself uses under the hood for cached search mode
- Zero-config if using Exa's hosted MCP server
- Neural search (semantic, not keyword) — good for conceptual queries, less precise for exact lookups

**When to prefer MCP-direct over Codex delegation:**
- Hitting Codex subscription quota limits
- Need lower latency (<2s vs 3-8s)
- Need raw search results (not synthesized)
- Need structured output (JSON with URLs, snippets, metadata)

### Evaluated and Not Recommended: `pi-web-access` (nicobailon)

378 stars · 16K downloads/wk · v0.10.6 (Apr 2026) · [GitHub](https://github.com/nicobailon/pi-web-access)

Feature-rich: 4 tools (`web_search`, `code_search`, `fetch_content`, `get_search_content`), cascading provider fallback (Exa → Perplexity → Gemini), YouTube video understanding, PDF extraction, GitHub repo cloning.

**Why not recommended:**
- 32 open issues as of Apr 2026 — high for a package at this maturity level
- macOS Keychain popups from browser cookie access (issues #9, #37) — persistent annoyance, multiple reports
- Exa MCP's generate-summary step constantly timing out (issue #43)
- `code_search` breaks because hosted Exa MCP no longer exposes `get_code_context_exa` by default (issue #24)
- PDF extraction crashes on Node 22 (issue #41)
- Gemini Web falsely reported unavailable under Bun runtime (issue #15)
- LLM can ignore configured provider and use a different one (issue #17)

**When it might still be worth it:** If you specifically need video understanding, PDF extraction, or GitHub repo cloning — features that neither Codex delegation nor MCP-direct provide. Accept the rough edges.

### Other Alternatives Evaluated

**`badlogic/pi-skills/brave-search`** — Official skill by Pi's creator. Skill-only (no extension code), requires Brave API key. Safest and most transparent option if you want a skill-based approach. The model uses `bash` to call the Brave API via curl.

**`pi-amplike`** (pasky, 190 stars) — Jina-based, works without any API key. Lower search quality than Brave/Perplexity. Good as a zero-config fallback.

**`pi-smart-fetch`** (4.8K dl/wk) — Smart `web_fetch` with desktop-browser TLS impersonation and defuddle extraction. Fetch only, no search. Useful as a complement to a search-only solution.

## Decision

**Primary: Codex CLI delegation.** Zero marginal cost (included in ChatGPT subscription), high quality (GPT 5.5 synthesis), ~15 lines of extension code. The 3-8s latency is acceptable for a few searches per session.

**Fallback: MCP-direct with Brave Search.** If Codex quota becomes a bottleneck, switch to Brave Search MCP via `.mcp.json`. Free tier covers 2000 queries/month. This is a config-only change, no extension code needed.

**Not using: `pi-web-access`.** Too many open issues and macOS-specific pain points. The Codex approach is simpler and more reliable.

## Status: Researched — Build on Day 1
