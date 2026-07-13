# LLM Toolkit

LLM Toolkit provides reusable agent skills and supporting CLIs for research workflows.

## Language

**Research Skill**:
A reusable skill that gathers, verifies, and structures online information from multiple source types.
_Avoid_: Search script, web wrapper

**Product Research Skill**:
A staged buying-decision workflow that uses the Research Skill's source tools to produce product recommendations.
_Avoid_: Shopping search, product scraper

**Publish Research Skill**:
A reusable skill that transforms one completed Product Research Skill run into a reviewed static article and optionally deploys it from an explicit site profile.
_Avoid_: Site-specific publisher, Markdown converter

**Published Research Page**:
The static HTML article produced by the Publish Research Skill from one Product Research Skill run.
_Avoid_: Research dump, generated landing page

**YouTube Research CLI**:
The command-line source tool that turns a YouTube query into selected video evidence with transcripts or extracted findings.
_Avoid_: YouTube scraper, transcript script

**Gmail Skill**:
A reusable skill that lets an agent find and read the user's Gmail messages through a narrow, structured, read-only command surface.
_Avoid_: Gmail scraper, email bot

**Gmail Read CLI**:
The command-line source tool that turns email search instructions into bounded message metadata, snippets, and selected message bodies for agent use.
_Avoid_: Gmail API when referring to the caller-facing command contract, mailbox dump

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
- The **Publish Research Skill** transforms one Product Research Skill run into one **Published Research Page**.
- The **Publish Research Skill** reads site identity, paths, image policy, audience defaults, and optional deployment behavior from the target project's `.publish-research.json`.
- The **Research Skill** exposes the **YouTube Research CLI**.
- The **YouTube Research CLI** has exactly one **Public CLI Contract**.
- The **YouTube Research CLI** attempts the **Primary Backend** before the **Free Fallback Backend**.
- The **Gmail Skill** exposes the **Gmail Read CLI**.
- The **Gmail Read CLI** has exactly one **Public CLI Contract**.

## Example dialogue

> **Dev:** "Can product research call a new YouTube command for ScrapeCreators?"
> **Domain expert:** "No — preserve the **Public CLI Contract** of the **YouTube Research CLI** so the **Product Research Skill** keeps working unchanged. ScrapeCreators should be the **Primary Backend**, with the **Free Fallback Backend** hidden inside the tool."

## Flagged ambiguities

- "YouTube API" can mean the public YouTube Data API, ScrapeCreators' YouTube endpoints, or this toolkit's **YouTube Research CLI**. Resolved: use **YouTube Research CLI** for the caller-facing command and backend-specific names for providers.
