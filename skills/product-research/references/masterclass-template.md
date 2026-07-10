# Masterclass Template

Load this at Stage 2c before assembling `02-masterclass.md`. The masterclass is a standalone educational document — the user should be able to read it cold and understand every dimension that matters for this product category, independent of specific model recommendations.

## Frontmatter

Use the standard research angle-file frontmatter (see `../../research/references/persistence-format.md`), with:
- `role: angle`
- `sub_question`: "What should a first-time buyer understand about [category]?"
- `tags`: product category + aspect-related nouns + `masterclass` + `product-research`

## Structure

```markdown
# {{Product Category}} — Buying Guide

> A comprehensive guide to what actually matters when choosing a {{category}}, built from expert reviews, owner experiences, and engineering fundamentals.

## {{Aspect Cluster 1: e.g., Wheels, Suspension & Terrain}}

### {{Aspect 1a: e.g., Wheel size and material}}

**Why it matters:** {{1-2 sentences — the engineering or design reason this dimension exists and affects your experience}}

**What to look for:**
- {{Specific spec, feature, or quality indicator — with concrete numbers/thresholds when they exist}}
- {{Another indicator}}

**What to avoid:**
- {{Red flag or misleading spec — explain WHY it's misleading}}

**Real-world experience:** {{What owners report after 6-12 months that you won't find in spec sheets. Cite source type (Reddit, YouTube owner review, forum) without full URLs — those live in the aspect angle files.}}

**Key tradeoff:** {{The thing this aspect competes with — e.g., "bigger wheels = harder fold" — so the reader understands this isn't a free lunch}}

### {{Aspect 1b: e.g., Suspension systems}}

{{Same subsection structure as above}}

---

## {{Aspect Cluster 2: e.g., Fold Mechanism & Portability}}

### {{Aspect 2a}}

{{Same structure}}

---

## {{Aspect Cluster 3}}

{{Continue for all clusters}}

---

## Marketing vs Reality

Common claims that sound important but don't hold up under scrutiny.

- **{{Myth 1}}** — {{What's claimed → what's actually true. Cite source type.}}
- **{{Myth 2}}** — {{Same pattern}}
- **{{Myth 3}}** — {{Same pattern}}

## What matters most for your situation

Based on your use case ({{1-line summary from interview}}), here's how these aspects rank:

1. **{{Criterion 1}}** — {{1 sentence: why this ranks highest for YOUR context, referencing the aspect section above}}
2. **{{Criterion 2}}** — {{Why}}
3. **{{Criterion 3}}** — {{Why}}
4. **{{Criterion 4}}** — {{Why}}
5. **{{Criterion 5}}** — {{Why}}

{{Continue to 7-10 if the category warrants it. Stop when additional criteria wouldn't meaningfully change a buying decision.}}

{{IF contradictions exist with user priorities (2+ independent sources):}}

**Worth reconsidering:** You mentioned {{user priority}}. Research from {{source type 1}} and {{source type 2}} suggests that {{finding}}. This means {{implication for your decision}}.

## Decision framework

{{One practical paragraph. What makes category X worth spending more on, where diminishing returns kick in, and which aspects are the real differentiators vs. noise.}}
```

## Voice and Tone

Write as if explaining to a smart friend who's buying this category for the first time. Assume intelligence but not domain knowledge.

- **Concrete over abstract.** "25cm+ rear wheels" beats "large wheels." "170-180° recline" beats "good recline."
- **Explain the WHY.** Don't just list specs — explain the engineering or design reason something matters.
- **Owner voice over expert voice.** When owners and experts disagree, lead with what owners actually experience daily.
- **Tradeoffs are mandatory.** Every aspect that matters competes with something else. Never present an aspect as pure upside.
- **No product recommendations.** The masterclass educates on dimensions, not models. Specific products belong in Stages 3-5.

## Length Targets

- Each aspect subsection: 100-200 words
- Each aspect cluster: 300-600 words (2-3 aspects per cluster)
- Marketing vs Reality: 150-300 words
- Ranked criteria: 200-400 words
- Decision framework: 50-100 words
- **Total document: 2000-3000 words**

If it runs much shorter, aspects are too shallow — the reader won't learn enough to evaluate products independently. If much longer, trim the "what to look for" lists and fold edge cases into the aspect angle files.

## Assembling from Aspect Files

The masterclass is a synthesis of the `aspects/*.md` deep-dive files, not a copy-paste. When assembling:

1. Read all aspect files from `aspects/`
2. Identify cross-aspect tradeoffs that individual subagents may not have surfaced (e.g., wheel size vs fold size is a tradeoff between two different clusters)
3. Consolidate overlapping findings — if two clusters both mention the same myth, merge into one Marketing vs Reality entry
4. Apply interview context ONLY to the "What matters most for your situation" and "Decision framework" sections — the rest of the document should be universally useful regardless of the buyer's priorities

## Relationship to Synthesis

The synthesis (Stage 5) contains a condensed 400-800 word master class section that highlights the most decision-relevant criteria and myths, with a link:

```markdown
> For the full buying guide covering all aspects in depth, see [the complete masterclass](02-masterclass.md).
```

The synthesis master class is a summary, not a replacement. It should make sense standalone for quick reading but defer to the full document for education.
