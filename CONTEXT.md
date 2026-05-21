# LLM Toolkit

LLM Toolkit provides reusable agent skills and supporting CLIs for research workflows.

## Language

**Research Skill**:
A reusable skill that gathers, verifies, and structures online information from multiple source types.
_Avoid_: Search script, web wrapper

**Product Research Skill**:
A staged buying-decision workflow that uses the Research Skill's source tools to produce product recommendations.
_Avoid_: Shopping search, product scraper

**YouTube Research CLI**:
The command-line source tool that turns a YouTube query into selected video evidence with transcripts or extracted findings.
_Avoid_: YouTube scraper, transcript script

**Primary Backend**:
The backend attempted first by a source tool during normal operation.
_Avoid_: Default provider when describing fallback behavior

**Free Fallback Backend**:
The existing no-key YouTube path used when the Primary Backend is unavailable or fails.
_Avoid_: Legacy backend, old backend

**Public CLI Contract**:
The caller-facing command, flags, JSON envelope, and documented output fields that skills rely on.
_Avoid_: API when referring to the shell command contract

**Upload-Date Filter**:
A coarse freshness window for YouTube search results chosen from `today`, `this_week`, `this_month`, or `this_year`.
_Avoid_: After date, exact date filter

## Relationships

- The **Product Research Skill** uses the **Research Skill** source tools.
- The **Research Skill** exposes the **YouTube Research CLI**.
- The **YouTube Research CLI** has exactly one **Public CLI Contract**.
- The **YouTube Research CLI** attempts the **Primary Backend** before the **Free Fallback Backend**.

## Example dialogue

> **Dev:** "Can product research call a new YouTube command for ScrapeCreators?"
> **Domain expert:** "No — preserve the **Public CLI Contract** of the **YouTube Research CLI** so the **Product Research Skill** keeps working unchanged. ScrapeCreators should be the **Primary Backend**, with the **Free Fallback Backend** hidden inside the tool."

## Flagged ambiguities

- "YouTube API" can mean the public YouTube Data API, ScrapeCreators' YouTube endpoints, or this toolkit's **YouTube Research CLI**. Resolved: use **YouTube Research CLI** for the caller-facing command and backend-specific names for providers.
