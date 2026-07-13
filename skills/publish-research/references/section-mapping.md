# Section mapping: Product Research Skill output to HTML

`00-synthesis.md` is the primary article source. Use its prose verbatim for criteria, recommendations, tradeoffs, and rejection rationale. Angle files and `aspects/*.md` supply supporting detail for criterion cards, evidence drawers, product inventory, source links, tables, quotes, and videos.

## 1. Chip nav

**HTML:** `.chip-nav` with `.chip` links.

Use the stable section anchors: `#picks`, `#criteria`, `#compare`, `#all-products`, `#tradeoffs`, `#ruled-out`, `#evidence`. Keep labels short. The page-local script manages `.is-active`.

## 2. Hero and TL;DR

**Sources:** synthesis title/date/context + recommendation tiers.

- `.eyebrow`: category and research month.
- `.headline`: editorial headline, not necessarily the synthesis title.
- `.hero__lede`: 1–2 sentences about the research approach.
- `.tldr`: one `.tldr__row` per recommendation tier.
- Link rows to stable pick IDs: `#pick-best`, `#pick-budget`, `#pick-premium`.
- If the third tier is category-specific (terrain, ergonomic, compact, etc.), still use `#pick-premium` and show the real tier label visibly.
- `.brief`: context/source sentence from the synthesis.

## 3. Criteria and merged deep dives

**Sources:** synthesis “what matters” section + `02-masterclass.md` + `aspects/*.md` for support.

Use `#criteria` with `.criteria-stack`. Each `<details class="crit">` should represent one decision criterion or closely-related aspect group.

Recommended card content:
- summary: number, criterion title, one-sentence TL;DR from synthesis.
- body: verbatim criterion explanation, then relevant masterclass detail.
- preserve links, quotes, tables, and source-backed claims.
- use `.aside`, `.pull`, or `.crit__tradeoff` for short callouts when useful.

Cross-references from picks use `<a class="refer" data-deep-dive="crit-or-aspect-id">→ about topic</a>`. Every target must exist.

### Myths

Use `.myths` and one `.myth` per misconception. Preserve claim, tag, explanation, and order from the synthesis. Tags should be short: `Marketing`, `Gimmick`, `Overkill`, `Worse, actually`, `Not for us`.

## 4. Compare matrix

**Sources:** only facts already present in the synthesis and angle files.

Use `#compare` with `.matrix` plus `.matrix--1`, `.matrix--2`, or `.matrix--3` for the actual recommendation count. Generate one header and one value cell per recommendation in every row. Prefer 8–10 rows when supported, but omit rows where all picks are materially equal or the sources do not support a value.

Good rows: price, availability, dimensions/capacity, core spec, warranty, use window, strongest advantage, main caveat, local retailer, verification confidence.

Do not invent specifications. Use `Unknown`, `Not verified`, or omit the row when unsupported.

## 5. Picks

**Sources:** synthesis recommendations, market reality, verification status, runner-ups.

Use `#picks` and one `<article class="pick pick--best|budget|premium">` per recommendation.

Each pick should include:
- stable ID (`#pick-best`, `#pick-budget`, `#pick-premium`)
- tier label and price in `.pick__header`
- model name, specs, verbatim verdict
- `.pc` pros/cons grid
- buy/source buttons in `.btn-row`
- `.pick__meta` for price/stock verification status
- `.pick__warning` for traps, recalls, scams, or major caveats
- `.pick__runner` for runner-up links and rationale

Button mapping:
- `.btn--primary` for primary buy/monitor action.
- `.btn--ghost` for alternates, source links, or “see more”.

## 6. All products

**Sources:** full product inventory across synthesis and angle files.

Use `#all-products` with `.allp` / `.allp__track` / `.allp__card`.

Inventory rules:
1. Include recommendation-card products.
2. Include runner-ups.
3. Include credible alternatives from expert/owner/availability tables.
4. Include every product in considered/discarded sections.
5. Include retailer-only products only when the research treats them as candidates or price anchors.
6. Deduplicate obvious repeats; keep materially different configurations separate when the research does.

Ordering:
1. Picks.
2. Runner-ups and credible alternatives.
3. Mixed-fit/unverified candidates.
4. Ruled-out/deal-breaker candidates.

Card classes:
- `.allp__card--pick` — recommended, runner-up, or genuinely plausible alternative.
- `.allp__card--consider` — mixed fit, missing verification, limited stock, or “good but not for us”.
- `.allp__card--avoid` — explicitly ruled out.

Card copy must be source-grounded. Use `Price not found` or `Availability not verified` instead of guessing.

## 7. Tradeoffs

**Sources:** synthesis “tradeoffs between tiers” / “how to choose” section.

Use `#tradeoffs` with `.tradeoffs` and `.trade` cards. Each card compares one tier transition:
- `.trade__head`: from tier → to tier + price delta.
- `.trade__col--gain`: what improves.
- `.trade__col--lose`: what you give up.

End with `.bottom-line` using the existing summary advice. Do not write a new recommendation if the synthesis already has one.

## 8. Ruled out

**Sources:** synthesis considered/discarded section.

Use `#ruled-out` with `.ruled` and `.ruled-item`.

Each item preserves model name, severity tag, and rejection explanation.
- `.ruled-item__tag--red`: strong avoid, safety issue, recall, scam, clear deal-breaker.
- `.ruled-item__tag--amber`: not for this use case, unavailable, weak evidence, too risky.

## 9. Evidence drawers

**Sources:** `aspects/*.md`, `03-availability.md`, `04-owner-voice.md`, `05-expert-voice.md`, `06-retailer-voice.md`, and relevant material from `02-masterclass.md`.

Use `#evidence` with `.drawers` / `.drawer`.

Typical drawers:
1. Aspect research / how criteria were evaluated.
2. Real owner voice.
3. Expert testing and data.
4. Pricing, retailer, and availability evidence.

Drawer rules:
- Curate, do not dump raw markdown.
- Preserve source URLs as clickable links.
- Preserve tables when the source uses structured comparisons.
- Preserve blockquotes and citations.
- Reddit quotes should link `<cite>` to the source thread when available and preserve upvotes as `· N↑`.
- Keep retailer/source links `target="_blank" rel="noopener"`.

### YouTube embeds

Embed only primary/secondary YouTube sources that directly support visible criteria or findings. Use `.video-embed` with `.video-embed__thumb data-video-id="..."`, `mqdefault.jpg`, and a one-line annotation explaining relevance.

## 10. Interview brief

**Source:** `01-interview.md`.

Put the interview Q&A in the final `.drawer` inside `#evidence`. Do not create a separate interview section.

Render each question as a bold label and each answer as a blockquote. Use the configured `audience.intervieweeName` when present; otherwise preserve a source-grounded attribution or use the neutral label `Interview response`. Include the context/handoff summary as `.aside` when present.

## 11. Footer

Include:
- research date and price/stock disclaimer
- the configured affiliate disclosure
- the configured `.made-with` sign-off when non-empty

## Validation mapping

After generation, check for:
- new structure selectors: `.chip-nav`, `.tldr`, `.criteria-stack`, `.crit`, `.matrix`, `.pick`, `.allp`, `.tradeoffs`, `.trade`, `.ruled-item`, `.drawers`, `.drawer`
- stable anchors: `#picks`, `#criteria`, `#compare`, `#all-products`, `#tradeoffs`, `#ruled-out`, `#evidence`, applicable `#pick-*`
- no obsolete article markup: legacy quick-pick bars, legacy hero cards, legacy carousel/cards, old recommendation cards, old expandable-detail containers, old rejection tags, inline styles, or hard-coded carousel controls
