---
name: product-research
disable-model-invocation: true
description: Run staged buying-decision research for one household or personal product and produce ranked picks with tradeoffs. Use when deciding what to buy, not when asking how something works.
---

<objective>
Produce a buying decision for one product category that the user can act on without redoing the research. The result often becomes a page for someone else to read, through `/publish-research`. The research has to resist SEO and affiliate noise, and every pick has to be something a buyer in Romania can order today at a price this household would pay.

Two documents carry the result:

- A masterclass (`02-masterclass.md`) that teaches every dimension of the category well enough that the reader could judge products alone.
- A synthesis (`00-synthesis.md`) with ranked picks, a primary and a runner-up per tier, grounded in owner voice, expert voice and what is sold now.

The run is done when:

- every pick sits inside the user's hard limits and budget ceiling (the one exception is in `<edge_cases>`), with a seller link and a price read from the seller's page during this run, or a plain note that it could not be confirmed
- the masterclass covers every discovered aspect, not only the ones the user asked about
- every model that any stage evaluated appears in the synthesis's candidate table with a one-line verdict
- blocked sources, thin evidence and unconfirmed stock are stated in the synthesis and in the closing message
- the run is persisted and `INDEX.md` has its entry
</objective>

<rules>
1. **One product per run.** If the request names several, ask which to start with and suggest a fresh session for the next, so each gets its own depth and its own research folder.
2. **Research overrules preferences. It does not overrule hard limits.** Stated priorities are an input signal and a tiebreaker. A hard limit (budget ceiling, physical constraint, explicit dealbreaker) bounds the picks. When research suggests a limit is costing the user something, say so in the synthesis and keep the picks inside it.
3. **No recency filters on research calls.** Good products are often three or four years old and their best reviews are too. Current price and stock come from the finalist sweep.
4. **Availability tiers.** Green: a Romanian retailer, recommend fully. Yellow: an EU retailer that ships to Romania (Amazon DE, Bol.nl, a brand's EU store), recommend with the landed cost, price plus shipping. Red: outside the EU (UK, US), leave out. The exception is a thin market where nothing in the EU fills a tier: then include the import and state duty, VAT, shipping, plug and warranty caveats.
5. **Never invent a tier to fill a slot.** Rename the tier to a use-case axis ("best for small spaces") or omit it.
6. **Stages run in order.** Each consumes the previous one's output: the candidate stage needs the ranked criteria from the masterclass, and the finalist sweep needs the picks.
7. **Running this skill authorizes its research spending.** The paid search, scrape and social calls a run makes are expected; do not ask for cost confirmation.
8. **The user's instructions for this run win over this skill.** If they ask to skip the interview or want only the masterclass, do that. When asked to go faster, cut scope (fewer aspects, no product stages) and keep the source depth. A masterclass built from Perplexity answers alone does not teach much; its value comes from owner threads, long video reviews and expert sources.
</rules>

<shared_infrastructure>
This skill reuses the `research` skill's infrastructure. Install the two side by side; the research skill is then at `../research/` relative to this skill's directory.

- **CLI commands:** `references/cli-reference.md` in the research skill.
- **Angle-file frontmatter, run directory layout, INDEX.md format:** `references/persistence-format.md` in the research skill.
- **Subagents:** spawn with the `research-subagent` agent type where the harness has it; it logs API usage and already carries a sourcing policy (Perplexity answers are leads, failures are reported, claims are cited). Otherwise use a general subagent.
- **Run directory:** create `~/Documents/Research/YYYY-MM-DD-<category>-product-research/` at the start. Every file name in this skill is relative to it.

Subagents write their own files. Give each one the absolute path of its file. If one returns without writing it, write the file from the returned text and set `write_fallback: true`.
</shared_infrastructure>

<routing>
Redirect to `/research` when the request is not a buying decision from scratch: whether to keep or replace something, how a product works, or a comparison of a shortlist the user already has. If it is unclear which product the run is about, ask once.
</routing>

<pipeline>

## Stage 1: Interview

**Read `references/interview-calibration.md` before composing questions.**

**Outcome:** a filled interview handoff (see `<handoff_contracts>`) with enough signal to rank the criteria and bound the picks. A question earns its place when its answer could change the shortlist.

Before composing questions:

- Use what the project already records about the household (location, people, standing constraints) and what the user said in the request. Do not ask for it again.
- Look up the category's real price bands in Romania with one or two quick calls, so the budget question can show numbers.

Ask category-specific questions using the frame in the reference, and close with one budget question anchored on those bands. Use the harness's question tool; Claude Code's AskUserQuestion takes at most 4 questions per call, so send larger sets in batches.

Ask a follow-up round only when the answers would lead to a wrong shortlist; the reference lists the triggers.

An answer is a hard limit only when the user states it as one: a budget ceiling, a physical constraint, an explicit dealbreaker. Everything else is a preference, including a selected option that bundles several things. After the interview, tell the user in two or three lines what you are treating as hard limits and what as preferences, then continue without waiting. They can correct it while the research runs.

Write the full Q&A and the handoff block to `01-interview.md` with angle-file frontmatter (`role: angle`, `sub_question: "interview"`).

## Stage 2: Preliminary — aspects, retailers, masterclass

### 2a: Aspect discovery (main context)

**Outcome:** 8–12 fundamental dimensions that differentiate products in this category, clustered into 3–4 groups that each make a coherent research topic. For a stroller: `{wheels, suspension, terrain}`, `{fold, weight, portability}`, `{safety, materials, build}`, `{canopy, storage, ergonomics}`.

Discover them from the category alone. Leave the user's priorities out of these queries, so the masterclass teaches the whole category and can contradict an assumption. Two or three broad searches are enough, for example:

- `research.py ask "what are the most important factors to evaluate when buying a [category]? Cover performance, build quality, ergonomics, safety, materials, maintenance, durability, accessories"`
- `youtube.py search "[category] buying guide what to look for [current year]"`
- `research.py ask "[category] common buyer mistakes, things people overlook, biggest regrets after buying"`

### 2b: Aspect deep-dives and the retailer map (subagents in parallel)

Spawn one subagent per cluster plus one for the retailer map, all in one message.

**Aspect subagent brief.** Give it the category and the use case, without the user's stated priorities.

> You are researching [cluster name] for [category]. The findings go into a buying guide that teaches a first-time buyer what matters, so this is research about the aspects themselves. Do not rank or score specific products.
>
> Your aspects: [2–3 aspects]
>
> For each aspect, document:
> 1. What it is and why it matters, in plain language
> 2. What to look for: the specs, features or qualities that separate quality from cost-cutting, with numbers where they exist
> 3. What to avoid: red flags, misleading specs, marketing traps
> 4. What owners find out only after buying (Reddit, forums, long owner reviews on YouTube)
> 5. The engineering tradeoff: what improving this aspect costs elsewhere
>
> Three to five solid sources per aspect is typical; stop when new sources repeat what you have. Do not filter by recency. End the file with a "Coverage gaps" section naming any source you could not reach and what the finding rests on instead.
>
> Write to `aspects/[cluster-slug].md` with angle-file frontmatter.

**Retailer map brief.**

> Map where a buyer in Romania can buy [category]. Start with Romanian sellers and go past eMAG, Altex and Flanco, which are starting points and not the whole market. Cover:
> 1. Big-box and marketplace retailers (eMAG, Altex/Media Galaxy, Flanco, Cel.ro, Dedeman)
> 2. Official brand stores and local distributors (russellhobbs.ro, shop.tefal.ro, smeg.com.ro)
> 3. Specialty retailers for the category (etbm.ro for lights, avstore for audio, coffeegear.ro for coffee, KitchenShop-type stores)
> 4. Romanian price aggregators (Compari.ro, Price.ro, Pricy.ro) as a way to discover more seller domains
> 5. EU retailers that ship to Romania (Amazon DE, Bol.nl, category specialists), for when Romanian coverage is thin or a strong model is not sold domestically
>
> Produce:
> - `retailer_universe`: every valid seller or discovery domain found, grouped by seller type, each with name, base or category URL, seller type, strength, caveats, and whether to use it as primary, secondary or verify-only.
> - `availability_shortlist`: the 3–6 best starting platforms. This is a starting point for later stages, not a boundary.
> - `market_depth_judgment`: `broad`, `moderate` or `thin`, with a short rationale. Use judgment. If many Romanian sellers clearly carry the category, keep the universe broad. If it is sparse, document the dead ends and make the import options explicit.
>
> Write to `03-availability.md` with angle-file frontmatter.

Before moving on, confirm every aspect file and `03-availability.md` exists and has real content.

### 2c: Masterclass (main context)

**Read `references/masterclass-template.md` before writing.**

Read every file in `aspects/` and write `02-masterclass.md` to the template. The aspect sections are for any buyer. The interview shapes only the closing sections: the ranked criteria, the decision framework, and any "worth reconsidering" note. The interview changes how the criteria rank, never which aspects are covered.

A contradiction with a stated priority is reported only when two or more independent quality sources support it. Carry those forward to the synthesis. Extract the ranked criteria and the myths into the handoff for Stage 3.

## Stage 3: Candidates — three subagents in parallel

Each receives the full interview handoff, the ranked criteria, the myths and the retailer map. They work independently, and Stage 4 merges their files into one candidate table and picks from it; tell them so. Ask each to:

- identify each model by its EU or Romanian model number, and say when the reviews it relies on cover a different regional variant and whether that changes anything
- evaluate any model the user named in the interview
- search without recency filters
- end the file with a "Coverage gaps" section naming any source it could not reach and what the finding rests on instead

**Owner voice** → `04-owner-voice.md`

> Find what owners say about [category] after living with it: long Reddit threads (r/BuyItForLife, category subreddits) and non-affiliate YouTube reviewers. Look for multi-year reliability, quirks that expert reviews miss, and dealbreakers that only show up in daily use. Score candidates against the ranked criteria. Produce 5–8 candidate models, each with what owners love, what fails and what makes people return or regret it.

**Expert voice** → `05-expert-voice.md`

> Compare the leading models in [category] using named expert reviewers, trade publications and specialist review sites. Skip generic "best of" roundups from affiliate and SEO sites. Score candidates against the ranked criteria. Produce 5–8 candidates with comparative notes and explicit scores per criterion.

**Retailer voice** → `06-retailer-voice.md`

> Find out which [category] models are sold to buyers in Romania now and at what prices. Start from the availability shortlist and widen through the retailer universe, aggregators and web search. Cover each price band and each seller class before going deep on any one model; the per-model deal hunt happens later, for the final picks.
>
> Produce 5–8 candidate models that are well stocked and plausible on the ranked criteria, each with the sellers found, price (RON or EUR), stock state where visible, and the EU model number. Add the price bands for the market: entry, sweet spot, premium.
>
> Close with a `coverage_judgment`. If the category is broadly stocked, say which seller classes you covered. If it is thin, say which searches and sites you tried, why coverage looks thin, and which import options exist. Claim that only a few options exist only after aggregators, official stores and specialty sellers were checked or attempted.

## Stage 4: Picks and the finalist sweep

### 4a: Choose the picks (main context)

Merge the three candidate files into one candidate table: one row per model, with the voices that covered it, the price seen, the availability tier and its standing. This table goes into the synthesis.

Choose up to three tiers, each with a primary and a runner-up, from models inside the hard limits and the budget ceiling. Default tiers are overall, budget and premium. With a ceiling, "premium" means the best inside it.

When a model would make the picks on one voice alone, because the others never looked at it, run one targeted follow-up before picking: a subagent or a few calls for the missing owner, expert or seller evidence. One round is enough. A pick that still rests on one voice gets a `low` confidence tag.

### 4b: Finalist sweep (one subagent)

**Outcome:** for each chosen model, the best reputable deal available to a buyer in Romania today, confirmed on the seller's page.

> For each of these models: [the picks and runner-ups, with EU model numbers and the sellers already found]. The user's hard limits are: [hard limits]. The budget ceiling is: [ceiling, or none].
>
> 1. Sweep sellers for the exact model: `"<model>" pret`, `"<model>" site:.ro`, `"<model>" compari.ro OR price.ro OR pricy.ro`, the brand's Romanian store or distributor, and the sellers in the retailer universe. Follow aggregator results to the seller's own page.
> 2. Open the best candidate pages and read them. Use `research.py scrape` first. When a page blocks it or renders with JavaScript (Altex, Flanco, Trendyol, Bebe Tei), read it with the `agent-browser` skill.
> 3. On the page, confirm the title is this exact model, read the current price and the stock state, and check the specs against the hard limits. Note warranty, returns and delivery time when shown. For an EU import, work out the landed cost and use it as the price.
>
> Report one status per model:
> - `confirmed`: a seller page was read and shows this model, a price and stock
> - `unconfirmed`: no seller page could be read; say what was tried and why it failed
> - `unavailable`: pages were read, and the model is out of stock or discontinued at every seller found
> - `fails_limit`: the product page contradicts a hard limit, or the best price found is above the budget ceiling; say which
>
> For each model give the best reputable deal (seller, URL, price, stock, date read) and the other sellers checked. Stop sweeping a model when the main seller classes have been checked and further searches stop turning up a better reputable price. Do not change or re-rank the models.
>
> Write to `07-finalist-sweep.md` with angle-file frontmatter.

### 4c: Act on the sweep (main context)

- `confirmed`: use the sweep's seller, link and price in the synthesis.
- `unconfirmed`: keep the pick, and say next to the link that stock could not be confirmed and why. A blocked page says nothing about the product.
- `unavailable` or `fails_limit` on a primary: promote its runner-up, provided the runner-up came back `confirmed` or `unconfirmed`. Then fill the runner-up position as below.
- `unavailable` or `fails_limit` on a runner-up, or a runner-up position left open by a promotion: take the next-best model from the candidate table and sweep it. If it also fails, leave the tier without a runner-up.
- A tier whose primary and runner-up both failed: sweep the next-best model from the table once. If that fails too, omit the tier.

Say in the synthesis which model was replaced and why.

## Stage 5: Synthesis

**Read `references/synthesis-template.md` before writing.**

Write `00-synthesis.md` to the template. The template holds the structure, the length targets and the rules for tiers, discards, confidence and flags. Prepend the run entry to `~/Documents/Research/INDEX.md` in the format from `persistence-format.md`, with one bullet per numbered file (`00`–`07`).

Close the run with a short message to the user: the picks with price and where to buy, anything swapped or unconfirmed, coverage gaps that lower confidence, and that `/publish-research` turns the run into a page.

</pipeline>

<revising_a_finished_run>
When the user corrects a limit or adds candidates after the synthesis exists, rerun only what the change touches. For a new budget or constraint, re-pick from the candidate table. For new models, gather owner and expert evidence for them and add them to the table. In both cases run the finalist sweep on every pick that changed, then update `00-synthesis.md` in place and add a dated revision line under Context. Picks taken from search snippets without a sweep are not finished.
</revising_a_finished_run>

<handoff_contracts>

## Interview → Preliminary

`category`, `stated_priorities` and `budget` are required; the rest are filled when known.

```yaml
category: <product category>
use_case: <free-form summary>
stated_priorities: [ordered, top 2-3; preferences]
hard_limits: [only what the user stated as a must: physical constraints, explicit dealbreakers]
budget:
  ceiling: <amount and currency, or none>
  note: <e.g. "show me the spread", "would stretch for a quieter one">
constraints: [softer space, physical or environmental notes]
experience: first-time | replacing-known | upgrading | not-asked
named_models: [models the user mentioned]
raw_qa: [full Q&A for exact phrasing]
```

## Preliminary → Candidates

Added on top of the interview block. Criteria and myths come from the masterclass; retailer data from the retailer map.

```yaml
ranked_criteria:
  - criterion: <name>
    why_it_matters: <1 sentence>
myths_to_ignore:
  - myth: <name>
    source_basis: <short note>
contradictions_with_user_priorities:
  - user_priority: <what the user said>
    research_finding: <counter-signal>
    sources: [url1, url2]
retailer_universe:
  - platform: <name>
    url: <base or category URL>
    seller_type: big_box | marketplace | official_brand_store | specialty | aggregator | eu_import | other
    use_as: primary | secondary | verify_only
    strength: <short note for this category>
    caveats: <optional>
availability_shortlist:
  - platform: <name>
    url: <base or category URL>
    strength: <short note>
    caveats: <optional>
market_depth_judgment:
  level: broad | moderate | thin
  rationale: <why, and which import fallback to consider>
```

## Candidates → Synthesis

No separate contract. The orchestrator reads `04`–`06`, builds the candidate table, and reads `07-finalist-sweep.md` for prices, links and statuses.

</handoff_contracts>

<edge_cases>
- **Thin aspect research** for an obscure category: write the masterclass from what exists, name the thin aspects, and lower the confidence tags.
- **No ranked criteria come out of the masterclass:** score candidates on the user's priorities and say so in the synthesis.
- **Ceiling below the market's credible entry:** say so under Market reality and offer the cheapest credible option as the single pick, marked as above the ceiling. This is the only case where a pick exceeds the ceiling.
- **Whole category is sold only outside the EU:** say so, and produce what is available under the Red-tier exception.
- **Stated priorities fully agree with the research:** leave out the "what we learned" subsection.
- **A model the user named does not make the picks:** explain why under "Considered and discarded".
</edge_cases>

<reference_index>
Loaded at the stage that needs them:

- `references/interview-calibration.md` — Stage 1. The question-generation frame, the budget question and calibration examples.
- `references/masterclass-template.md` — Stage 2c. Document structure, voice and length.
- `references/synthesis-template.md` — Stage 5. Output structure, rules for tiers, discards, confidence and flags, and a worked example.

From the research skill: `references/cli-reference.md` (CLI commands) and `references/persistence-format.md` (frontmatter, run layout, INDEX.md).
</reference_index>
