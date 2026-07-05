---
name: brand-naming
description: Run a full brand-naming pipeline — strategy interview, competitor landscape research, isolated name-generation teams, sound-symbolism scoring, screening, proof of concept — ending in 3-5 vetted candidates with 1-2 recommendations. Use when naming or renaming a company, product, app, or feature.
---

<objective>
Produce 3-5 vetted name candidates — with 1-2 strongly argued recommendations — for a company,
product, app, or feature, following the playbook of Lexicon Branding (Swiffer, BlackBerry,
Pentium, Sonos, Impossible, Azure, Windsurf). The pipeline alternates user interviews with
autonomous research and generation, and translates Lexicon's core structural insight — small
teams working in isolation with deliberately different briefs — into isolated subagent contexts
with different information diets.

The run persists to `~/Documents/Research/YYYY-MM-DD-<subject-slug>-naming/` following the
research skill's persistence format (`../research/references/persistence-format.md`), including
an INDEX.md entry.
</objective>

<core_principles>
Distilled from the playbook — these govern every stage:

1. **The right name, not a good name.** It must be (a) original within the category, (b)
   processing fluent — pronounceable, spellable, with something in it you can grasp — and (c)
   unexpected *in context* (Azure is surprising for Microsoft; the same name from a design
   studio is not). Creative strategy in two words: **surprisingly familiar**.
2. **Quantity leads to quality.** Clients get stuck at 50-100 names; the answer lives around
   2,000. Teams generate volume ("trash") without evaluating. Never let judgment into the
   generation phase — speculate first, evaluate later, in separate stages.
3. **The comfort trap.** Comfortable + familiar = invisible. Polarization is energy (Grove on
   Pentium). Safe consensus names are the failure mode this skill exists to prevent — surface
   this to the user at every judgment checkpoint, but the user always decides.
4. **Name the ultimate benefit, not the ingredient.** The category names the ingredient
   ("Fiber One"); the winner names the outcome ("Feather — you feel lighter"). Ladder up.
5. **The name has one job.** Packaging, copy, and product carry the rest. A short supporting
   line closes the gap — Swiffer never needed "mop" in its name.
6. **Judge names in the world, not in a list.** Proof-of-concept mockups + the sub-second
   believability test ("Is that believable?") gate the finalists.
7. **Park, don't delete.** Rejected names with real energy stay visible and can be brought
   back with evidence — that is how BlackBerry survived its first client meeting.
</core_principles>

<shared_infrastructure>
- **Research CLI** — landscape and screening subagents use it; full syntax in
  `../research/references/cli-reference.md`. Costs are minor (search ~$0.005, ask ~$0.02).
- **Persistence** — run directory + frontmatter + INDEX.md conventions in
  `../research/references/persistence-format.md`.
- **Subagent types** — `research-subagent` for landscape and screening (has API logging hooks);
  `general-purpose` for generation teams (no web access needed; generation is knowledge work).
- **Checkpoints** — stages 1, 2, 4, 7, and 10 are interactive; stages 3, 5, 6, 8, 9 run
  autonomously. Announce before each autonomous stretch what is about to happen and roughly how
  long it takes. If the user asks to minimize check-ins, collapse checkpoints 4 and 7 into brief
  confirm-or-redirect messages, but never skip the longlist reaction round entirely — user
  energy data is an input the pipeline cannot fabricate.
</shared_infrastructure>

<pipeline>

## Stage 0: Setup

Create the run directory `~/Documents/Research/YYYY-MM-DD-<subject-slug>-naming/`. Check for
PROJECT.md / CONTEXT.md in the working directory — they often pre-answer half the intake.

File layout for the run:

```
00-recommendation.md   01-intake.md          02-strategy.md
03-landscape.md        04-creative-framework.md
05-team-product.md     06-team-twist.md      07-team-outside.md
08-shortlist.md        09-screening.md       10-proof-of-concept.md
```

## Stage 1-2: Intake and strategy interview (interactive)

**Read `references/interview-guide.md` before composing questions.**

Round 1 (intake): subject, type, category, audience, markets/languages, constraints, existing
candidates. Handles the rename branch when applicable. Round 2 (strategy): the four questions —
define winning / what do you have to win / what do you need to win / what must the name say —
asked one at a time, conversationally, then the benefit ladder to the ultimate benefit.

Write `01-intake.md` and `02-strategy.md` with the handoff YAML from the guide.

## Stage 3: Landscape research (autonomous — 2 parallel research-subagents)

### Subagent L1 — Category naming audit
> Collect the names of 20-40 companies/products competing in or adjacent to [category]
> (WebSearch + `research.py search`; include the competitors the user listed). Bucket them by
> naming pattern (descriptive compounds, ingredient names, coined, mythic, etc.), identify the
> dominant patterns — the "sea of sameness" — and any outliers that stand out and why. Note
> tired metaphors and overused morphemes in this category. Do NOT propose names.
> Write to `03-landscape.md` (section: audit) with angle-file frontmatter.

### Subagent L2 — Customer language
> Research how real customers talk about [category] and the problem it solves — Reddit
> (`social.py reddit` when available), reviews, forums. Capture verbatim phrases for: the pain,
> the desired outcome, the moment of relief. Note words customers use that vendors never do,
> and vice versa. Do NOT propose names.
> Append to `03-landscape.md` (section: customer language).

## Stage 4: Creative framework (interactive checkpoint)

Synthesize `04-creative-framework.md` — a window to walk through, not a spec to conform to:

```yaml
creative_framework:
  name_must_say: <the one job>
  ultimate_benefit: <one sentence>
  category_antipatterns: [patterns from L1 the names must NOT follow]
  whitespace: [what nobody in the category is doing]
  sound_direction: <fit-to-strategy recipe row, from references/sound-symbolism.md>
  territories:
    - name: <e.g. lightness>
      description: <1-2 sentences>
    # 3-5 territories: the ultimate benefit is always one; add 2-4 from
    # customer language, whitespace, or a deliberate reframe
```

Present to the user: the anti-patterns (what we will not do), and the territories with a
one-line case for each. Ask the user to strike, add, or reweight territories. This is the last
cheap moment to redirect — say so.

## Stage 5: Generation — three isolated teams (autonomous — 3 parallel general-purpose subagents)

This is Lexicon's separated-teams structure. The teams MUST NOT share context, see each other's
briefs, or see each other's output — isolation is what produces three genuinely different lists.
Each prompt includes: the absolute path to `references/hunting-grounds.md` (instruct: read it
first), the creative framework territories, the output file path, and a **quantity mandate of
120+ names minimum** with the speculate-don't-evaluate and approximate-thinking rules (they are
in the hunting-grounds file). Names come with a 3-8 word gloss and ground tag.

The information diets differ deliberately:

- **Team Product** (`05-team-product.md`): knows everything — full intake + strategy YAML,
  landscape anti-patterns, all territories. Deepest context, most literal danger; the
  anti-patterns keep it honest.
- **Team Twist** (`06-team-twist.md`): gets the product brief PLUS a twist you invent that
  changes its perspective — an added capability, a different flagship audience, or the product
  reimagined one category over (fiber → "fiber that also gives you energy"). State the twist as
  fact in the brief. Purpose: shift the team's priors, not describe a real roadmap.
- **Team Outside** (`07-team-outside.md`): gets NO product details, no category, no landscape.
  Only: the ultimate benefit, the audience in one line, and 2-3 metaphor domains where that
  benefit is literally engineered (for lightness: aerodynamics, birds, weather). Brief: "name
  something that delivers <ultimate benefit> to <audience>" — it is naming the feeling, not
  the product.

## Stage 6: Convergence (main context)

**Read `references/sound-symbolism.md` before scoring.**

1. Read all three team files. Merge and dedup. Add the user's `existing_candidates` to the pool.
2. Your own generation pass (Placek still names every week): up to 15 additions, focusing on
   blends and cross-pollinations *between* team lists — connections no isolated team could see.
3. First cut against the creative framework — kill category-antipattern names and anything with
   zero connection to a territory. Target 40-60 survivors.
4. Score the survivors on the seven-axis rubric, mechanically. Weight originality, surprise,
   and strategic fit highest.
5. Select 12-20 for the longlist preserving diversity: every territory represented, no more
   than ~half from one construction pattern, and at least 2-3 names from the bizarre end of
   the approximate range — the user must see the edge of the map, not just the middle.

Write `08-shortlist.md`: funnel numbers (e.g., 410 generated → 62 framework-fit → 16 longlist),
the scored table, and the longlist.

## Stage 7: Longlist reaction round (interactive checkpoint)

**Read `references/presentation-formats.md` (longlist section) before presenting.**

Deliver the comfort-trap briefing, present the longlist grouped by territory with one-line
glosses, and collect love / intrigued / nothing / hate reactions plus free-form notes. Probe
energetic hates once ("what exactly triggers it?" — practical objections become problems to
solve). Park, don't delete. Advance 8-12 names carrying energy into screening.

If nothing gets a reaction, trigger the redial cycle (see edge cases) — do not push a dead
longlist forward.

## Stage 8: Screening (autonomous — parallel research-subagents)

**Pass `references/screening-guide.md` (absolute path) to each subagent; 3-4 names per
subagent.** Five layers: collision scan, trademark quick screen, domain/handles, SEO
ownability, linguistic/cultural check across target languages. Verdicts: clear-ish / caution /
kill, with evidence. Merge results into `09-screening.md`. When a strong name dies, attempt the
modify-the-word move (spelling variant, affixed form, sibling from the same territory) and note
the variant for the user.

## Stage 9: Proof of concept (main context)

**Read `references/presentation-formats.md` (proof-of-concept section).**

For the top 5-7 survivors: render the five contexts (press headline, tagline lockup, sponsor
line, app-store/shelf card next to real competitors, spoken introduction) and apply the
believability test per context. A name failing believability in 3+ contexts drops out
regardless of scores. Write `10-proof-of-concept.md`. Offer (don't assume) an HTML name-boards
artifact.

## Stage 10: Final recommendation (interactive)

**Follow the dossier template in `references/presentation-formats.md`.**

Write `00-recommendation.md`: 3-5 final candidates, 1-2 ranked recommendations with
justification tied to the four questions, the sound analysis, screening status, the strongest
supporting line, and the honest risk (who will hate it and why that's energy). Include the
parking lot and next steps (attorney review, domain acquisition, launch-with-a-story,
90-120-day window). Bring a parked name back with evidence if it outscores the survivors.

Prepend the INDEX.md entry. Deliver the dossier content as the final message — the user reads
the conversation, not the file.

</pipeline>

<edge_cases>
- **Redial cycle** (max one): if the longlist gets no reactions, or the user's notes reveal the
  territories were wrong, diagnose which brief failed — wrong ultimate benefit (redo the ladder,
  Stage 2), wrong territories (revise Stage 4), or wrong twist/metaphor domains (revise those
  briefs only) — and rerun ONLY the failed generation legs with corrected briefs. This mirrors
  Lexicon's two-cycle check ("were these assignments right?"). After one redial, present the
  best available honestly rather than looping.
- **All finalists killed in screening**: pull the parking lot, apply modify-the-word variants,
  and screen those. Tell the user which territory is legally crowded and why.
- **User's existing candidate wins**: fine — say so plainly. The pipeline validated it; that is
  a result, not a failure.
- **User keeps choosing the safest name**: name the pattern once, show the comfort-trap chart
  in words (tension zone vs invisible zone), score their pick honestly next to the recommended
  one — then respect their call. It is their name.
- **Company name vs product name**: company names must survive future products — penalize
  candidates that hard-encode the current feature set (a "fiber"-root name is fine for the
  product, a trap for the company).
- **Non-Latin-script primary market**: weight CVCV/pronounceability heavier in scoring; add
  transliteration checks to screening.
</edge_cases>

<anti_patterns>
- Do NOT let evaluation into generation: team prompts must not mention trademark, domains, or
  feasibility. Filtering during generation is how clients get stuck at 50 names.
- Do NOT give Team Outside any product or category details — its value is ignorance.
- Do NOT show the user raw team lists (hundreds of names). The funnel numbers, yes; the
  trash, no.
- Do NOT rank finalists by user comfort. When the energy ranking and the comfort ranking
  disagree, present both and say which the playbook favors.
- Do NOT claim or imply legal clearance — every surviving name carries the attorney caveat.
- Do NOT pad: no filler names to hit longlist counts, no invented screening findings. Cite
  searches that came up empty.
- Do NOT skip the four questions and jump to generating names, even when the user opens with
  "just give me some name ideas" — the strategy stage is what separates this from asking a
  chatbot for 50 names. If the user truly wants a quick brainstorm, say this skill is
  overkill and offer both paths.
</anti_patterns>

<reference_index>
Lazy-loaded at stage boundaries:

- `references/interview-guide.md` — Stage 1-2: intake frame, rename branch, the four questions,
  benefit ladder, handoff YAML.
- `references/hunting-grounds.md` — Stage 5: passed to generation teams. Construction patterns,
  Latin/Greek root table, mythology, periodic table, natural-world lexicons, idiom/metaphor/
  synchronicity digs, coinage methods, output format.
- `references/sound-symbolism.md` — Stage 6: consonant/vowel semantics, CVCV, power letters,
  fit-to-strategy recipes, the seven-axis scoring rubric with calibration examples.
- `references/screening-guide.md` — Stage 8: passed to screening subagents. Five screening
  layers, verdict format, famous-failure calibration.
- `references/presentation-formats.md` — Stages 7, 9, 10: comfort-trap briefing, reaction
  protocol, proof-of-concept contexts, believability test, final dossier template.

Cross-references: `../research/references/cli-reference.md`,
`../research/references/persistence-format.md`.
</reference_index>

<success_criteria>
Ordered by skip risk (highest first).

- [ ] Four questions + benefit ladder completed conversationally BEFORE any name generation;
      ultimate benefit confirmed in one sentence by the user.
- [ ] Three generation teams spawned in parallel as isolated subagents with distinct
      information diets; Team Outside received no product/category details.
- [ ] Quantity mandate met: 300+ raw names across teams before any evaluation; funnel numbers
      reported in `08-shortlist.md`.
- [ ] Landscape anti-patterns derived from research and encoded in the creative framework
      before generation; user approved/adjusted territories at the Stage 4 checkpoint.
- [ ] Seven-axis scoring applied mechanically with the table shown for longlist names.
- [ ] Comfort-trap briefing delivered before the reaction round; hated-with-energy names
      parked, not deleted.
- [ ] Screening produced per-name verdicts with evidence and the attorney caveat; kills
      explained; modify-the-word attempted for strong kills.
- [ ] Proof of concept rendered in five contexts with believability pass/lean/fail per name.
- [ ] Final output: 3-5 candidates, 1-2 ranked recommendations justified against the four
      questions; parking lot and next steps included.
- [ ] Run persisted to `~/Documents/Research/YYYY-MM-DD-<subject-slug>-naming/` with all stage
      files; INDEX.md updated.
</success_criteria>
