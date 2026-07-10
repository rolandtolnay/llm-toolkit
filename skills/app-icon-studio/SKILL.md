---
name: app-icon-studio
disable-model-invocation: true
description: Design and generate a vetted batch of app icon candidates end-to-end — designer interview, concept directions, parallel OpenAI + Nano Banana generation via bundled CLI scripts, independent vision-judge subagents, one surgical revision turn, and a final contact sheet with 5-7 finalists. Use when the user wants an app icon created/generated for them via API (requires OPENAI_API_KEY and GEMINI_API_KEY in the app-icon-studio env file).
---

<objective>
Produce 5-7 vetted app-icon candidates — with 1-2 argued recommendations — by emulating a full
icon-studio pipeline inside one session: a strategy interview, 4 deliberately different concept
directions, parallel generation on two image engines, independent judge subagents, one
surgical revision turn, and a contact sheet that proves each finalist at home-screen sizes.

This skill is standalone: its `scripts/` call the OpenAI and Gemini image APIs directly
(dependency-free Node ≥18), loading API keys from `~/.claude/app-icon-studio/.env` and then
`./.claude/app-icon-studio.env` (project file wins). Its `references/` and
`assets/exemplars/` carry all craft knowledge. All run artifacts live under
`./icons/<app-slug>/` in the working directory.

A full run costs roughly $2-4 in API fees (≈16 generations + ≈6 edits) and the autonomous
stretch takes several minutes of wall-clock generation time. Say both to the user before
Stage 3.
</objective>

<core_principles>
1. **The brief is the work.** Every downstream prompt, judgment, and edit traces back to the
   interview. The half-second feeling (what a stranger feels before thinking) is the single
   most load-bearing answer — every direction and every final recommendation must be argued
   against it.
2. **Directions, not variations.** The pipeline's edge over "ask a chatbot for an icon" is four
   genuinely different concept directions — different metaphors and style families, not four
   renders of one idea. At least one literal, one abstract, one unexpected-but-fitting.
3. **Two engines, same brief, different priors.** OpenAI and Nano Banana fail differently;
   running both doubles the chance a direction lands. Identical prompt content per direction
   (format differs), then let the judges decide — never pre-filter by engine expectations.
4. **Verify with fresh eyes at honest sizes.** The orchestrator wrote the prompts and is
   biased toward them. Judgment belongs to independent subagents who see 48px thumbnails
   before full-size renders and calibrate against the exemplar gallery.
5. **One revision turn, one change per image.** Surgical edits on the strongest candidates,
   each fixing the single highest-leverage flaw with invariants restated. Revisions can
   regress — the original always stays in contention.
6. **Present a funnel, not a dump.** The user sees the brief, the directions, and the
   finalists — never all raw candidates uninvited. Report honest funnel numbers, failures
   included.
</core_principles>

<pipeline>

## Stage 0: Preflight and setup

Resolve the app name to a kebab-case slug and create `./icons/<slug>/` with subdirectories
`prompts/`, `round-1/`, `round-2/`, `final/`. In one bash call, check: `node --version` (≥18),
`node <skill>/scripts/openai-image.mjs config`, and
`node <skill>/scripts/gemini-image.mjs config`. Report only env-file paths loaded and key
presence, never values. Keys should live in `~/.claude/app-icon-studio/.env` or
`./.claude/app-icon-studio.env`; do not ask the user to export them globally. If one key is
missing, offer to run single-engine with doubled counts; if node is missing, stop and say so.

If `icons/<slug>/brief.md` already exists, this is a resumption: read it plus the latest stage
artifacts, tell the user where the run stands, and continue from the first incomplete stage.

## Stage 1: Interview (interactive)

**Read `references/interview-guide.md` before composing questions.** Six questions — product
and audience, the half-second feeling, brand reality, home-screen neighbors, style appetite
(AskUserQuestion), hard rules — asked conversationally, probing per the guide. Check
PROJECT.md / CONTEXT.md in the working directory first; confirm rather than re-ask what they
answer. Write `icons/<slug>/brief.md` in the guide's format, including the famous-icon
collision list you compile yourself.

## Stage 2: Concept directions (interactive checkpoint)

**Read `references/icon-design-principles.md` before designing.** Think as a designer, not a
prompt writer: for each direction, decide the mark, its twist, the style family, the exact
palette (hex, respecting brand reality), and the composition — each obeying the ten principles
and justified against the half-second feeling.

Design exactly 4 directions: at least one literal (the obvious concept done excellently), one
abstract/geometric (the feeling without the object), and one wildcard (unexpected but fitting
— the direction the user wouldn't have asked for). If an existing logo was provided, one
direction adapts it. Write `icons/<slug>/directions.md`: per direction — slug, mark + twist,
style family, palette with roles, composition note, the 2-3 exemplar files it should be judged
against, and one line on why it serves the feeling.

Present the four directions compactly (name, one-line concept, palette swatch as hex, the
why). Ask the user to strike, adjust, or swap — this is the last cheap redirect point, say so.
One confirm-or-redirect round, then go autonomous: state the cost estimate and that the next
check-in comes with finalists.

## Stage 3: Generation round 1 (autonomous)

**Read `references/prompt-recipes.md` before writing prompts.** For each approved direction
write two prompt files under `prompts/` — `<direction>-oai.md` (prose) and `<direction>-nb.md`
(JSON) — identical in content, per the shared skeleton with the constraint block and the
do-not-resemble list.

Generate 2 candidates per direction per engine (16 total) into `round-1/`, naming
`<direction>-<oai|nb>` so provenance survives in filenames. Launch the two engines as parallel
background bash loops and poll; Nano Banana requests run 20-90s each. A failed call gets one
retry with a lightly rephrased prompt; a second failure is dropped and counted honestly in the
funnel. Then build thumbnails: `sips -Z 48` and `-Z 128` copies into `round-1/thumbs/`
(skip with a note if sips is unavailable).

## Stage 4: Judge panel (autonomous — 2 parallel subagents)

Spawn two independent `general-purpose` subagents in one message — one **craft** judge, one
**brand** judge. Each prompt contains: the lens assignment, absolute paths to
`references/judge-guide.md` (instruct: read it first and follow its viewing protocol and
output format), `brief.md`, `directions.md`, the `round-1/` images and `thumbs/`, and the
exemplar files named in `directions.md`. Judges must not see each other's output.

Merge in main context: combine lens scores per candidate (the axes are disjoint — sum them),
apply KILL flags, and write `icons/<slug>/judging.md` with the merged table and both judges'
batch observations. Select ~6 revision candidates by merged score while keeping at least two
directions alive; prefer a lower-scored candidate from a distinct direction over a third
sibling of the leader. If both judges independently flag the same direction as dead, that is
signal — let it die.

## Stage 5: Revision turn (autonomous)

For each selected candidate take the judges' single highest-leverage edit (when the two
lenses disagree, craft fixes outrank brand fixes — a beautiful concept that fails at 48px is
worthless). Run each edit through the engine that made the image, per the edit recipes:
one change, invariants restated, output to `round-2/`. Candidates judged "ship as is" skip
revision and advance directly. Rebuild thumbnails for `round-2/`.

## Stage 6: Final selection and presentation

For each revised candidate, view original and revision side by side (48px thumbnails first,
then full size) and keep the better one — revisions that regressed lose to their originals.
From the survivors assemble 5-7 finalists into `final/`, keeping at least two directions
represented when quality allows.

Write `icons/<slug>/contact-sheet.html`: one row per finalist showing it at 512, 128, and 48px
(relative `img` paths with width attributes, plain self-contained HTML), plus direction name
and one-line flavor text. Open it with `open`.

Then deliver the final message in chat — the user reads the conversation, not the files:
funnel numbers (generated → survived judging → revised → finalists), the finalist list with
per-icon flavor text (concept, why it works, one watch-out), and 1-2 ranked recommendations
argued from the half-second feeling and the judges' evidence. Close with the honest caveats:
these are raster candidates — production needs a vector redraw or a `--quality high` /
`--image-size 2K` re-render, App Store delivery is a 1024px square PNG with no transparency
and no pre-rounded corners. Offer next steps: another polish round on a chosen winner, dark
or tinted variants, or export sizes.

</pipeline>

<edge_cases>
- **One engine unavailable or a key missing**: ask the user to add the key to the
  app-icon-studio env file, or proceed single-engine with doubled counts and tell the user
  which comparisons are lost.
- **Gemini default model 404s**: list models via the API (command in `prompt-recipes.md`),
  switch `--model` to the newest image model, note the change.
- **Moderation block or refusal**: rephrase once; if it persists, drop that candidate slot and
  report it in the funnel.
- **A whole direction generates weak** (both judges flag it): one redial maximum — regenerate
  that direction once with amplified constraints or a sharpened twist, reusing the judges'
  batch observations. After one redial, present the best available honestly.
- **User's existing logo direction wins**: fine — the pipeline validated their mark; that is a
  result, not a failure.
- **User asks for "just one quick icon"**: this skill is overkill for that — offer both paths
  (a single direct generation now, or the full pipeline) and respect the choice.
</edge_cases>

<anti_patterns>
- Do NOT generate anything before the brief and directions are approved — the interview is
  what separates this from asking a chatbot for an icon.
- Do NOT design four renders of one concept and call them directions.
- Do NOT judge candidates yourself in place of the panel — you wrote the prompts; you are
  biased. Your role at Stage 6 is arbitrating between original and revision with judge
  evidence, not re-scoring the field.
- Do NOT stack multiple fixes into one edit, and do NOT edit across engines.
- Do NOT let text, wordmarks, or pre-rounded tiles survive into the finalists (letterform/
  wordmark directions excepted, by design).
- Do NOT inflate results: report failed generations, dropped candidates, and dead directions
  in the funnel numbers exactly as they happened.
- Do NOT print or log API key values anywhere, including metadata and error reports.
- Do NOT ask the user to export API keys globally; the scripts load app-icon-studio env files.
</anti_patterns>

<reference_index>
Lazy-loaded at stage boundaries — read only what the current stage needs:

- `references/interview-guide.md` — Stage 1: the six questions, probing notes, brief format,
  worked example.
- `references/icon-design-principles.md` — Stage 2 (and background for Stage 6): the ten
  principles, exemplar annotations, generation-model failure modes.
- `references/prompt-recipes.md` — Stages 3 and 5: shared prompt skeleton, per-engine recipes
  and CLI calls, edit rules.
- `references/judge-guide.md` — Stage 4: passed to judge subagents; viewing protocol, lens
  axes, scoring discipline, output format.
- `assets/exemplars/` — 17 world-class icons (screenshots; ignore crop margins) used for
  direction calibration and judge anchoring.
- `scripts/openai-image.mjs`, `scripts/gemini-image.mjs` — self-documenting via `--help`.
</reference_index>

<success_criteria>
Ordered by skip risk (highest first).

- [ ] Full interview completed and `brief.md` written — including the half-second feeling,
      exactly 3 adjectives, and a famous-icon collision list — before any direction design.
- [ ] Exactly 4 directions spanning literal / abstract / wildcard, each justified against the
      feeling, approved by the user before any API spend; cost stated.
- [ ] Both engines ran with content-identical prompts per direction; every prompt persisted
      under `prompts/`; failures retried once and reported.
- [ ] Two independent judge subagents (craft + brand) ran in parallel with the judge guide,
      thumbnails available, no shared context; merged scores and KILL flags in `judging.md`.
- [ ] Revision turn: one edit per selected candidate, same engine, invariants restated;
      originals kept in contention and compared at 48px.
- [ ] Final delivery: 5-7 finalists in `final/`, contact sheet at 512/128/48px opened, funnel
      numbers plus 1-2 recommendations argued from the brief in the final chat message, with
      production caveats and next steps.
</success_criteria>
