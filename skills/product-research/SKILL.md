---
name: product-research
description: Run staged buying-decision research for a household or personal product (microwave, mattress, vacuum, dishwasher, appliance, furniture, electronics). Use when picking what to buy and wanting ranked picks with tradeoffs, not just information.
---

<objective>
Produce a trustworthy buying decision for a single product category through a staged pipeline that resists SEO/affiliate noise. The output is a synthesis with two parts: a master class on what actually matters for this category, and three tiers of recommendations (primary + runner-up per tier) grounded in owner voice, expert voice, and current EU/RO retailer availability.

Run persists to `~/Documents/Research/` in the same format as the generic research skill, with a product-specific synthesis structure.
</objective>

<core_rules>
1. **One product per run.** If the invocation mentions multiple products, push back — do not silently pick one.
2. **Research-derived criteria supersede user priorities.** User priorities are input signal + tiebreaker only. Contradictions with 2+ quality sources become master-class teaching moments.
3. **No `--recency` flags on CLI calls.** Mature products have valid older reviews. Use verification scrape instead.
4. **Availability tiering:** Green (RO retailer) → full recommend. Yellow (EU retailer, Amazon DE / Bol.nl / etc.) → recommend, flag import. Red (US-only / non-EU) → exclude.
5. **Never invent a tier** to fill a slot. Substitute the tier name with a use-case axis, or omit the tier.
6. **Scrape-only verification.** Flag recommendations — never rewrite them based on verification result.
7. **Stage order is sequential.** Preliminary (Stage 2) must finish before Product phase (Stage 3) spawns — product subagents consume the ranked criteria.
</core_rules>

<shared_infrastructure>
This skill reuses the research skill's infrastructure via cross-reference. Do not duplicate these:

- **CLI commands** — see `../research/references/cli-reference.md` for `ask`, `search`, `reason`, `scrape`, `docs`, `youtube`, `social reddit` invocations
- **Angle file frontmatter + run directory layout** — see `../research/references/persistence-format.md`
- **Subagent spawning** — use the `Task` tool with `subagent_type: "research-subagent"` (has API logging hooks). Same pattern as the research skill.
- **Output directory** — `~/Documents/Research/`

Differences from generic research:
- Staged pipeline (5 sequential stages) instead of single parallel spawn
- Slug convention: `YYYY-MM-DD-<category>-product-research` (e.g., `2026-04-23-microwave-product-research`)
- Synthesis file uses product-specific structure (see `references/synthesis-template.md`)
</shared_infrastructure>

<trigger_and_routing>
This skill runs only via explicit invocation (`/product-research`).

If the invocation message mentions multiple products, respond:

> Product research runs one product at a time so we can go deep on criteria, market, and availability. You mentioned [X] and [Y] — which one should we start with? I'd suggest running the second in a fresh session when you're ready, so each gets full focus and its own persisted research folder.

If the invocation is ambiguous about which product is the subject (e.g., user discussed several in conversation), ask once via AskUserQuestion which category to research.

Out of scope — redirect to generic `/research`:
- "Should I keep my current X or replace it?" (replacement analysis — different pipeline)
- "Tell me about X" / "how does X work" (educational, not buying)
- "Compare X and Y" where the user already has a shortlist and wants analysis (not discovery)
</trigger_and_routing>

<pipeline>

## Stage 1: Interview

**Read `references/interview-calibration.md` before composing questions.**

Generate 4-6 category-specific questions using the frame in that reference. Fire them via AskUserQuestion in a single round.

Fire a second AskUserQuestion round only if one of:
- Answers reveal contradictory constraints (e.g., "quiet + cheap + powerful") — ask user to rank top 2
- Budget absent AND category has wide price range (10x+ between entry and premium)
- A critical category-specific variable was missed (rare; orchestrator judgment)

Build the interview handoff block (see `<handoff_contracts>`). Write full Q&A and the structured block to `01-interview.md` with angle-file frontmatter (`role: angle`, `sub_question: "interview"`).

## Stage 2: Preliminary phase — 2 subagents in parallel

Spawn both with `Task` tool, `subagent_type: "research-subagent"`. Both receive the full interview handoff block.

### Criteria subagent
**Goal:** Build the ranked-criteria list that Stage 3 uses to score candidates.

**Prompt skeleton:**
> Research what actually matters when buying a [category]. Draw from expert reviews, non-affiliate YouTube long-form reviewers, and Reddit owner threads (r/BuyItForLife, category-specific subs). Explicitly identify marketing myths and spec theater.
>
> Produce:
> 1. Ranked criteria list, 5-10 items, most important first, with 1-sentence rationale each.
> 2. Marketing myths to ignore, 2-5 items with source basis.
> 3. Contradictions with user's stated priorities (from interview block) — only if 2+ independent quality sources push back on a priority. List each as: `{user_priority, research_finding, sources: [url1, url2]}`.
>
> Do NOT use `--recency` flags. Mature products have valid older reviews.
>
> Write to `02-criteria.md` with angle-file frontmatter.

### Availability subagent
**Goal:** Identify the 3-4 best retail platforms for this category in RO (first) + EU (fallback).

**Prompt skeleton:**
> Find the 3-4 best retail platforms for buying [category] with delivery to Romania. Priority:
> 1. Romanian retailers (eMAG, Altex, Dedeman, Flanco, Cel.ro, plus specialty stores — e.g. etbm.ro for lights, avstore for audio, coffeegear.ro for coffee)
> 2. EU retailers shipping to RO (Amazon DE, Bol.nl, category-specific EU specialty) when RO coverage is thin
>
> Per platform produce: name, base URL for this category, short note on strength for this category (selection breadth, pricing, warranty handling), any caveats (slow delivery, poor customer service for this category, etc.).
>
> Write to `03-availability.md` with angle-file frontmatter.

Wait for both to complete before proceeding. Check both files exist and have their expected content. If criteria subagent failed to produce a ranked list, fall back to user priorities and note the fallback in the synthesis.

## Stage 3: Product phase — 3 subagents in parallel

Each subagent receives: full interview handoff + ranked_criteria + myths_to_ignore + availability_shortlist. Spawn all three in parallel with `subagent_type: "research-subagent"`.

### Owner voice subagent
**Goal:** Real-world ownership signal.

**Prompt skeleton:**
> Find owner perspectives on [category] from Reddit long-form (r/BuyItForLife, r/[category], category-specific subs) and non-affiliate YouTube reviewers. Use `social.py reddit` and `youtube.py search`.
>
> Focus on: multi-year reliability, quirks not mentioned in expert reviews, deal-breakers that only surface with real use. Score candidates against the ranked criteria provided.
>
> Produce 5-8 candidate models with owner-voice summary per model (what owners love, what fails, deal-breakers).
>
> Write to `04-owner-voice.md`.

### Expert voice subagent
**Goal:** Comparative analysis against the ranked criteria.

**Prompt skeleton:**
> Compare top models in [category] using expert/trade sources. Use `research.py ask` with context=high, `research.py reason` for comparative analysis, and `research.py scrape` for 2-3 trusted expert/trade source pages.
>
> Avoid affiliate/SEO sites (generic "best of" roundups). Prefer named expert reviewers, trade publications, and specialized review sites.
>
> Score candidates against the ranked criteria. Produce 5-8 candidates with comparative notes per model and explicit criteria scoring.
>
> Write to `05-expert-voice.md`.

### Retailer voice subagent
**Goal:** Current availability and price for candidate models.

**Prompt skeleton:**
> For [category], identify 5-8 candidate models via WebSearch (owner/expert subagents run in parallel — do not read their outputs). Use the availability shortlist provided. Run `research.py scrape` on product pages from each platform for the identified candidates.
>
> Per candidate: availability per platform (in stock / out / not listed), current price (RON or EUR), warranty terms if visible, delivery window if visible.
>
> Write to `06-retailer-voice.md`.

## Stage 4: Verification

After all three product-phase subagents return, orchestrator identifies the 6 final recommendations (3 tiers × primary + runner-up). For each:

1. Scrape the primary retailer URL via `research.py scrape <url>` (no `--recency` flag).
2. Check for:
   - Out-of-stock signals: "out of stock", "discontinued", "not available", "indisponibil", "stoc epuizat", 404, redirect to category page
   - Current price
   - Title match (did we land on the right product?)
3. Tag each recommendation:
   - `verification: verified` (default; omit from output to reduce noise)
   - `verification: manual — link didn't confirm availability` (scrape ambiguous or failed)
   - `price-changed: was X, now Y` (>20% price delta from research-captured value)

**Do not rewrite recommendations based on verification results.** Flag only. The recommendation reflects quality; the flag reflects current stock state.

## Stage 5: Synthesis

**Read `references/synthesis-template.md` before writing.**

Write `00-synthesis.md` following the exact structure. Key reminders:
- Master class has 4 subsections. Omit the "what we learned vs your initial assumptions" subsection entirely if no contradictions cleared the 2-source threshold — do not write "no contradictions found".
- Market reality line is standard; include for every run.
- 3 tiers by default (overall / budget / premium). Substitute tier name with use-case axis if default doesn't fit the category. Omit a tier entirely if no strong candidate exists.
- Considered-and-discarded section: 2-3 items from (1) shortlist fallout, (2) SEO-popular but expert-rejected. Each MUST cite specific source/finding. Do not pad.
- Confidence tag per recommendation with a one-line reason.
- Verification flags go on "Where to buy" line, not on the recommendation itself.

Prepend a run entry to `~/Documents/Research/INDEX.md` following the format in `../research/references/persistence-format.md`.

</pipeline>

<handoff_contracts>

## Interview → Preliminary

Adaptive YAML. `category` and `stated_priorities` are required. Others optional:

```yaml
category: <product category>
use_case: <free-form summary>
stated_priorities: [ordered list, top 2-3]
stated_dealbreakers: [list]
budget_signal:
  type: fixed | range | flexible | none_given
  value: <if applicable>
constraints: [space/physical/environmental notes captured]
experience: first-time | replacing-known | upgrading | not-asked
raw_qa: [full Q&A for exact phrasing reference]
```

## Preliminary → Product phase

Adds the following on top of the interview block:

```yaml
ranked_criteria:
  - criterion: <name>
    why_it_matters: <1 sentence>
myths_to_ignore:
  - myth: <name>
    source_basis: <short note>
contradictions_with_user_priorities:
  - user_priority: <what user said>
    research_finding: <counter-signal>
    sources: [url1, url2]
availability_shortlist:
  - platform: <name>
    url: <base URL>
    strength: <short note for this category>
    caveats: <optional>
```

## Product phase → Synthesis

No separate contract. Orchestrator reads `04-owner-voice.md`, `05-expert-voice.md`, `06-retailer-voice.md` and composes the synthesis.

</handoff_contracts>

<edge_cases>
- **Thin preliminary results** (sparse sources for obscure category) → proceed with best judgment; flag lower confidence in synthesis
- **Criteria subagent fails to produce ranked list** → fall back to user priorities; note the fallback in synthesis
- **Unrealistic budget** (user says 1500, market starts at 3000) → no explicit warning; the market-reality line in synthesis does the educating naturally
- **Tier with no strong candidate** → substitute tier name with use-case axis (e.g., "best for small spaces"), or omit tier entirely. Never invent.
- **Whole category is US-only** → flag in synthesis that no EU-available options exist at meaningful tiers; still produce what's available
- **Verification fails for a recommendation** → tag `verification: manual`, keep recommendation in the output
- **User's stated priorities fully align with research** → omit "what we learned vs your initial assumptions" subsection; don't pad
- **User named specific models in interview** → ensure product-phase subagents evaluate those models. If they don't make the shortlist, address them in the considered-and-discarded section regardless of the 2-item minimum.
</edge_cases>

<anti_patterns>
- Do NOT surface single-source contradictions in the master class. Only 2+ independent quality sources trigger the "what we learned" subsection.
- Do NOT pad the considered-and-discarded section to hit 3 items. One well-justified discard beats three padded.
- Do NOT write "no contradictions found" or "no myths to note" filler. Omit those subsections entirely when empty.
- Do NOT use a generic interview question list. Generate per-category questions using the interview-calibration frame.
</anti_patterns>

<reference_index>
Lazy-loaded during specific stages:

- `references/interview-calibration.md` — load at **Stage 1 (Interview)** before composing questions. Contains the question-generation frame and 3 calibration examples (microwave, mattress, vacuum).
- `references/synthesis-template.md` — load at **Stage 5 (Synthesis)** before writing `00-synthesis.md`. Contains the exact output structure and a worked example.

Cross-references to the research skill (same project):
- `../research/references/cli-reference.md` — CLI invocations for `research.py`, `youtube.py`, `social.py`
- `../research/references/persistence-format.md` — angle-file frontmatter, run directory conventions, INDEX.md format
</reference_index>

<success_criteria>
Ordered by skip risk (highest first).

- [ ] Pipeline runs all 5 stages in order. Preliminary (Stage 2) completed before Product phase (Stage 3) spawned.
- [ ] Interview questions generated per-category using the interview-calibration frame, not from a generic template.
- [ ] Ranked criteria (not user priorities) used to score and order candidates in product phase.
- [ ] "What we learned vs your initial assumptions" subsection appears ONLY when 2+ quality sources contradict a user priority; omitted entirely otherwise.
- [ ] Synthesis follows synthesis-template.md structure: master class + market reality line + 3 tiers × (primary + runner-up) + tradeoffs + considered-and-discarded.
- [ ] Verification flags ambiguous recommendations with `verification: manual` — never rewrites them.
- [ ] Run persisted to `~/Documents/Research/<slug>/` with slug `YYYY-MM-DD-<category>-product-research`, 7 files total (`00-synthesis.md` + 6 angle files); INDEX.md updated with a single run entry.
- [ ] No `--recency` flags used on any CLI call during the run.
</success_criteria>
