# Web Search

## What This Replaces

Claude Code's `WebSearch` and `WebFetch` tools — the ability to search the web and fetch page content during a task. Used for looking up documentation, verifying API behavior, finding current information.

## Why I Need It

Many tasks require current information: checking library APIs, finding error solutions, verifying behavior that may have changed since the model's training cutoff. Without this, the model either hallucinates or asks me to look things up manually.

Key behaviors:
- Search query → list of results with titles, URLs, snippets
- Fetch a specific URL → page content (text extracted from HTML)
- Reasonable result truncation (don't dump entire pages into context)

## Pi API Surface (Known)

Three implementation approaches:

**Skill wrapping a CLI tool:**
- Write a SKILL.md that instructs the model to use `ddgr`, `googler`, or similar CLI search tools
- Pros: No extension code, just a markdown file
- Cons: Depends on external CLI tool, model must know how to parse output

**Extension registering a custom tool:**
- `pi.registerTool()` with a search API call (Brave Search, SerpAPI, etc.)
- Pros: Clean tool interface, structured results
- Cons: Requires API key, TypeScript code

**Skill + Extension combo:**
- Skill provides workflow guidance, extension provides the tool capability
- Most flexible but more moving parts

## Research

- [ ] Check if an existing Pi package provides web search
- [ ] Evaluate which search API to use (Brave, SerpAPI, Perplexity, DuckDuckGo)
- [ ] Check if `ddgr` or similar CLI tools work well enough as a skill-only approach
- [ ] Determine if a page-fetch tool is needed separately from search
- [ ] Consider whether Perplexity MCP could be wrapped as a Pi extension

## Implementation

_To be filled after research._

## Status: Not Started
