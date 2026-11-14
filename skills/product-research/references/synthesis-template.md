# Synthesis Template

Load this before writing Stage 5. The synthesis file (`00-synthesis.md`) follows this structure; the rules below say when a section is renamed or omitted.

## Frontmatter

Use the standard research synthesis frontmatter (`references/persistence-format.md` in the research skill), with:
- `role: synthesis`
- `query`: the user's original product request, verbatim if short, paraphrased if long
- `tags`: product category + 3-5 criteria-relevant nouns + `product-research`

## Structure

```markdown
# {{Product Category}} — Product Research

**Query:** {{user's question}}
**Context:** {{1 line, e.g. "Replacing a 10-year-old unit. Primary use: reheating + occasional cooking. Counter placement."}}

## Master class

> For the full buying guide covering all aspects in depth, see [the complete masterclass](02-masterclass.md).

### What actually matters

{{3-6 ranked criteria, each with 1-2 sentences of why. Condensed from the masterclass's "What matters most for your situation" section.}}

1. **{{Criterion 1}}** — {{Why it matters, in plain language}}
2. **{{Criterion 2}}** — {{Why}}
3. **{{Criterion 3}}** — {{Why}}
4. **{{Criterion 4}}** — {{Why}}

### What people think matters but doesn't

{{2-4 marketing myths or spec theater items. Each a short bullet with a reason. Condensed from the masterclass's "Marketing vs Reality" section.}}

- **{{Myth 1}}** — {{Why it doesn't matter as much as marketed}}
- **{{Myth 2}}** — {{Why}}
- **{{Myth 3}}** — {{Why}}

### What we learned vs your initial assumptions

{{Include only for contradictions supported by 2+ independent quality sources.}}

{{Per contradiction — 1 short paragraph. Frame as "what we learned", not "you were wrong".}}

- You mentioned {{user priority}} was important. Research surfaced that {{finding}} — {{source 1}} and {{source 2}} both emphasize {{counter-signal}}. This means {{implication for your decision}}.

### Decision framework

{{One paragraph. Practical guide: "lean budget if X, go overall if Y, stretch to premium only when Z".}}

## Market reality

Entry at **~{{X}} RON** · Sweet spot around **~{{Y}} RON** · Premium starts **~{{Z}} RON**.
{{Optional 1-line anchor note if prices are currency-mixed, e.g. "(EU imports quoted in EUR are 1 EUR ≈ 5 RON)".}}
{{If the user gave a ceiling: "Your ceiling: {{amount}}. Every pick below sits inside it." If nothing credible exists under it, say that here instead.}}
{{Only if research found something material above the ceiling: one line on what the next step up buys and for how much. It is information, not a pick.}}

## Recommendations

### Best overall — {{Model name}}

**Price:** {{X}} RON {{for an EU import: landed cost, price + shipping}} · **Availability:** {{Green/Yellow + retailer}} · **Confidence:** {{high/medium/low}} — {{one-line reason}}

{{1-2 sentence tier framing: "why this is the default pick".}}

**Key specs (that matter):** {{criterion 1 value}}, {{criterion 2 value}}, {{criterion 3 value}}

**Pros:**
- {{Pro 1}}
- {{Pro 2}}

**Cons:**
- {{Con 1}}
- {{Con 2}}

**Where to buy:** [{{Retailer}}]({{URL}}) · {{flag in plain words if stock could not be confirmed}}

**Runner-up: {{Model name}}** ({{price}} RON) — {{2-3 line why-this}}. Pick this instead if {{specific condition}}.

---

### Best budget — {{Model name}}

{{Same card structure as above.}}

**Runner-up: {{Model}}** — {{line}}. Pick this instead if {{condition}}.

---

### Best premium — {{Model name}}

{{Same card structure.}}

**Runner-up: {{Model}}** — {{line}}. Pick this instead if {{condition}}.

## Tradeoffs between tiers

{{One paragraph per gap — not a table. Keep it decision-oriented.}}

**Budget → Overall:** {{What you gain when you jump up. Typically 1-2 of the ranked criteria that the budget pick under-delivers on.}}

**Overall → Premium:** {{What you gain. Often diminishing returns — be explicit if premium is only worth it for specific use cases.}}

## Considered and discarded

{{1-3 items. Each a short paragraph.}}

- **{{Model name}}** — {{Why the user might have heard of it / why it seemed plausible}}. Discarded because {{specific finding from which source}}. {{Optional: when this would actually be the right pick}}.

- **{{Model 2}}** — {{Same pattern}}.

## All candidates

{{Every model any stage evaluated, one row each: picks first, then runner-ups, considered, ruled out.}}

| Model | Role | Price | Availability | Verdict | Evidence |
|---|---|---|---|---|---|
| {{EU model name/number}} | {{pick / runner-up / considered / ruled out}} | {{price or "not found"}} | {{Green / Yellow / Red / not verified + seller}} | {{one line: why it is where it is}} | {{04 / 05 / 06 / 07}} |

## Evidence

See angle files in this directory for full findings, source URLs, and verbatim quotes:
- [Interview](01-interview.md) — Q&A + priorities
- [Masterclass](02-masterclass.md) — comprehensive buying guide covering all product dimensions
- [Availability](03-availability.md) — RO/EU retailer universe and starting platforms
- [Owner voice](04-owner-voice.md) — Reddit + YouTube owner synthesis
- [Expert voice](05-expert-voice.md) — expert/trade comparative
- [Retailer voice](06-retailer-voice.md) — what is sold in Romania and at what prices
- [Finalist sweep](07-finalist-sweep.md) — best deal, stock and price for each pick, read from seller pages
- [Aspect research](aspects/) — deep-dive research files per aspect cluster

## Verification

{{Only include if a pick is unconfirmed or was replaced, or if a source gap lowers confidence.}}

- {{Model}} at {{retailer URL}}: stock not confirmed — {{what was tried and why it failed}}
- {{Tier}}: {{original model}} was replaced by {{model}} because {{out of stock at every seller found / fails the {{limit}} limit}}
- Coverage: {{source that could not be reached, and what the affected finding rests on instead}}
```

## Length targets

- Master class: 400-800 words total across the four subsections
- Each primary recommendation card: 80-120 words
- Runner-up: 30-50 words
- Tradeoffs: 50-100 words per gap
- Considered-and-discarded entries: 40-80 words each

Total synthesis target: 1500-2500 words. If it runs much longer, the decision signal is being diluted by detail — trim pros/cons or fold into angle files.

## Rules for tier substitution

Default tiers: **best overall / best budget / best premium**.

Substitute tier names when the default doesn't fit:
- If "premium" has no meaningful candidates (e.g., niche category where top-tier options don't exist), replace with a use-case axis: "best for heavy use", "best for small spaces", "best for specific feature".
- If "budget" and "overall" collapse into the same shortlist (category has no meaningful budget differentiation), rename one to a use-case axis or omit.
- Omitting a tier with honest framing is better than padded content.

## Rules for the discarded section

This section explains the discards a reader would wonder about. The candidate table lists the rest. Sources, in priority order:
1. **User-anchored** — every model the user named in the interview that did not make the picks.
2. **Shortlist fallout** — models that appeared in 04/05/06 research but didn't make the picks, including any model a voice ranked first. Strongest signal because you have specific findings to cite.
3. **SEO-popular but expert-rejected** — models that top affiliate/SEO sites push but that the expert-voice or owner-voice research disagrees with. Adds anti-affiliate trust signal.

One well-justified discard beats three padded ones. Three is the usual ceiling; user-named models can take it higher. If there is nothing worth explaining, omit the section.

Each entry cites the specific source or finding that led to exclusion. "Didn't make the cut" is not acceptable. "Owner threads on r/Appliances consistently flagged compressor failure within 2 years — 04-owner-voice.md" is acceptable.

## Confidence tags

Per recommendation, assign one of:
- **high** — multiple independent quality sources converge on this pick (expert + owner voice both endorse)
- **medium** — signal is solid but thinner (one strong source, others neutral)
- **low** — limited coverage; recommending based on best available data, user should cross-check

Always include a one-line reason after the tag. `high — 3 independent expert reviews + Reddit BIFL consensus` is useful; `high` alone is not.

## Prices, links and flags

Prices, sellers and links on the recommendation cards come from the finalist sweep (`07-finalist-sweep.md`), which read them from seller pages during this run.

- `confirmed` picks carry no flag.
- `unconfirmed` picks keep their place and get a plain flag on the "Where to buy" line: "stock not confirmed, check before ordering". A blocked page says nothing about the product.
- A pick the sweep found `unavailable` or failing a hard limit has already been replaced in Stage 4. The Verification section says which model was replaced and why.

## Empty sections

Omit a subsection that has nothing to say ("What we learned vs your initial assumptions", Verification, Considered and discarded). Do not write "none found" in its place.

## Worked example: microwave research (excerpt)

```markdown
# Microwave — Product Research

**Query:** Looking for a microwave under 1500 RON for the kitchen, mostly reheating plus some defrosting
**Context:** Open-plan kitchen, replacing a 5-year-old noisy unit, counter placement, 1 adult + infant arriving soon

## Master class

> For the full buying guide covering all aspects in depth, see [the complete masterclass](02-masterclass.md).

### What actually matters

1. **Interior capacity vs exterior footprint** — Most 20L microwaves have similar external dimensions to 23-25L models. Going slightly bigger costs nothing in counter space and solves the "plate doesn't fit" problem that's the #1 regret in Reddit threads.
2. **Magnetron build quality** — The component that breaks. Cheap units die in 3-5 years; mid-tier units from Samsung, Panasonic, LG typically go 8-10+. The visible shell is irrelevant; the magnetron is the whole ballgame.
3. **Sensor reheat accuracy** — Not "does it have sensor cook" (marketing checkbox) but "does the sensor actually work". Many cheap sensor units fire the default time regardless of what the sensor reads. Only real reviews can tell you this.
4. **Sound level** — Rarely specified on the product page; measured by reviewers. Difference between 55dB and 65dB is substantial in an open-plan apartment.

### What people think matters but doesn't

- **Wattage above 800W** — Past 800W, heating time differences are marginal for reheating. Marketing pushes 900-1000W as superior; reality is 800W is sufficient for 95% of home use.
- **Inverter vs standard magnetron** — Panasonic's marketing makes this seem transformative. Owner threads find it's a small quality improvement for defrosting and negligible for reheating.
- **Preset buttons count** — 8 presets vs 12 presets is cosmetic. Almost nobody uses them.

### What we learned vs your initial assumptions

- You mentioned wattage was a priority. Research surfaced that 800W is the practical threshold — r/Appliances threads and Wirecutter both emphasize that magnetron reliability and sensor quality matter more than headline wattage. This means your budget is better spent on a 800W Panasonic than a 1000W no-name.

### Decision framework

For reheating + occasional defrosting in an open-plan kitchen, prioritize quietness and build quality over wattage and features. The budget pick is "good enough" for pure reheating; overall earns its premium on build reliability; premium adds convection/grill which is only worth it if you'll actually cook with it.

## Market reality

Entry at **~400 RON** · Sweet spot around **~900 RON** · Premium starts **~1800 RON**.

## Recommendations

### Best overall — Panasonic NN-SD27HSBPQ

**Price:** 900-1100 RON · **Availability:** Green — eMAG · **Confidence:** high — endorsed across 3 expert reviews and consistent BIFL mention

Inverter-based 800W unit with cyclonic inverter tech, 23L capacity, 55dB operational noise. Mid-tier build quality from a brand with a reliability track record.

**Key specs:** 800W, 23L, 55dB, stainless interior

**Pros:**
- Consistently quiet across owner reports (3-year timeframe)
- Magnetron reliability — multi-year owner threads report no failures
- Good sensor reheat (not just marketing)

**Cons:**
- No grill/convection — reheating only
- Stainless interior shows fingerprints

**Where to buy:** [eMAG](https://...)

**Runner-up: Samsung MS23K3513AS** (850 RON) — similar capacity, slightly louder. Pick this instead if the Panasonic is out of stock or if you prefer a cleaner exterior.

[... continues with budget and premium tiers ...]
```

The worked example shows the voice and density. Your synthesis should match this tone: decision-first, concrete, cites findings without dumping them.
