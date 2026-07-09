# Prompt Recipes — Driving Both Engines

How to turn a Stage 2 direction into engine-specific prompts and CLI calls. Write every prompt
fresh from the direction and the brief — never reuse a prompt from a past run. Long prompts go
in `--prompt-file` files under `icons/<slug>/prompts/`, one file per direction per engine, so
the run is reproducible and diffable.

Both scripts live in this skill's `scripts/` directory and are dependency-free Node (≥18):

- `scripts/openai-image.mjs` — GPT Image API (`gpt-image-2`). Needs `OPENAI_API_KEY`.
- `scripts/gemini-image.mjs` — Gemini image API / Nano Banana (`gemini-3-pro-image-preview`).
  Needs `GEMINI_API_KEY`. If the default model 404s, list models with
  `node <skill>/scripts/gemini-image.mjs models` and pick the newest image model.

API keys are loaded from app-icon-studio env files before each script looks up the key:

```dotenv
# ~/.claude/app-icon-studio/.env, or project override ./.claude/app-icon-studio.env
OPENAI_API_KEY=...
GEMINI_API_KEY=...
```

The project env file loads second and overrides both the global file and any inherited env
value. Keep project env files out of git; this repo ignores `.claude/*.env` and
`.claude/*/.env`. Use each script's `config` command to confirm key presence without printing
values.

Run `--help` on either script for the full flag list. Both support `--dry-run`.

## The shared prompt skeleton

Every icon prompt, for either engine, contains these blocks in this order:

1. **Deliverable**: "iOS app icon, square 1:1 canvas" — naming the artifact sets the model's
   mode and polish level.
2. **Mark**: the ONE subject, as a noun phrase with 1-2 adjectives, including the direction's
   twist. ("a plump owl formed from a single continuous envelope fold")
3. **Style**: style family + shape language + stroke/corner logic in concrete terms.
4. **Palette**: exact hex values with roles. "Mark: warm cream #F5EFE6. Background: solid deep
   teal #0E5D5A, filling the entire square canvas edge-to-edge."
5. **Composition**: "mark centered, filling about 60% of the canvas, even margins, optically
   centered" — adjust percentage to the direction.
6. **Feeling**: one sentence from the brief. ("The icon should feel watchful and calm, like
   someone quietly keeping guard.")
7. **Constraints** (every prompt, every iteration — they drift otherwise):
   - no text, no letters, no numbers, no watermark
   - no rounded-rectangle tile, no frame, no drop shadow around the icon; background bleeds to
     all four edges of the square canvas
   - very low detail: big shapes that survive 48px; no sparkles, no secondary objects
   - flat/consistent lighting per the style; colors limited to the listed palette
   - do not resemble: <famous-icon collision list from the brief>

Exception: a letterform/wordmark direction replaces the "no text" line with the exact
glyph(s) in quotes and a typography spec (weight, style, color).

## OpenAI (gpt-image-2) recipe

Prose brief, blocks separated by blank lines, in skeleton order. gpt-image-2 rewards specific
material and composition language and handles structured/geometric marks and letterforms well.

Generation (2 candidates per direction):

```bash
node <skill>/scripts/openai-image.mjs generate \
  --prompt-file icons/<slug>/prompts/<direction>-oai.md \
  --n 2 --size 1024x1024 --quality medium --format png --background opaque \
  --out icons/<slug>/round-1 --name <direction>-oai --quiet
```

- `--quality medium` for rounds, `high` for a final re-render of winners.
- gpt-image-2 has no transparent background; keep `opaque`.
- Surgical edit (revision turn) — one change, preserve list restated:

```bash
node <skill>/scripts/openai-image.mjs edit \
  --image icons/<slug>/round-1/<candidate>.png \
  --prompt "Make the owl's eyes 30% larger. Change nothing else: same palette (#F5EFE6 mark on solid #0E5D5A background), same composition and scale, same style, same lighting, background still edge-to-edge with no tile or frame, no text." \
  --quality high --format png --out icons/<slug>/round-2 --name <candidate>-r2 --quiet
```

## Nano Banana (gemini-image.mjs) recipe

Nano Banana responds well to a structured JSON brief followed by one plain sentence of art
direction. Keep the JSON to this shape (same skeleton, structured):

```json
{
  "image_type": "iOS app icon, square 1:1",
  "mark": {
    "description": "<the ONE subject with its twist>",
    "style": "<style family + shape language>",
    "feeling": "<3 adjectives from the brief>"
  },
  "palette": {
    "mark": "<hex>",
    "background": "solid <hex>, filling the entire square canvas edge-to-edge",
    "accent": "<hex or 'none'>"
  },
  "composition": {
    "framing": "mark centered, fills ~60% of canvas, even margins, optically centered",
    "detail_level": "very low — big shapes that must survive 48x48px"
  },
  "constraints": "no text, no letters, no watermark, no rounded-rectangle tile, no frame, no drop shadow, nothing outside the palette",
  "do_not_resemble": ["<famous icon 1>", "<famous icon 2>"]
}
```

Generation (2 candidates per direction — each request returns one image; `--n` fans out):

```bash
node <skill>/scripts/gemini-image.mjs generate \
  --prompt-file icons/<slug>/prompts/<direction>-nb.md \
  --n 2 --aspect-ratio 1:1 --image-size 1K \
  --out icons/<slug>/round-1 --name <direction>-nb --quiet
```

- `1K` for rounds; re-render winners at `2K` if the user wants a crisper final.
- Requests take 20-90s each; leave the default timeout alone.
- Surgical edit — attach the image, one conversational change, preserve list:

```bash
node <skill>/scripts/gemini-image.mjs edit \
  --image icons/<slug>/round-1/<candidate>.jpg \
  --prompt "Change only the background to solid #0E5D5A. Keep the mark, its size, position, style, and everything else exactly identical. No text, no tile, background edge-to-edge." \
  --aspect-ratio 1:1 --image-size 1K --out icons/<slug>/round-2 --name <candidate>-r2 --quiet
```

- With an existing logo as reference: attach it via `--image` and say what to take from it
  ("use the attached mark's shapes and palette; redesign the composition for an app icon —
  do not copy it pixel for pixel").

## Why two engines

The engines have different priors and fail differently — that is the point of running both.
Expect gpt-image-2 to be stronger on geometric precision, letterforms, and constraint
adherence; expect Nano Banana to be stronger on character, texture, and stylized warmth. Do
not pre-filter by these expectations — generate with both and let the judges decide. Keep each
prompt's *content* identical between engines (same mark, palette, constraints); only the
format differs (prose vs JSON). Anything else confounds the comparison.

## Edit rules (revision turn)

- **One change per edit.** Stacked edits compromise on all of them. Pick the single
  highest-leverage fix from the judge feedback.
- **Restate the invariants every time**: palette hexes, composition, style, edge-to-edge
  background, no text. Models drift on anything unstated.
- **Edit with the engine that made the image.** Cross-engine edits restyle everything.
- **Fix order** when a candidate has several flaws: silhouette → single concept → 48px
  readability → palette discipline → shape-language consistency → lighting → differentiation.
  Fixing lighting on a muddy silhouette is wasted spend.
- **Text or watermark artifacts are not editable** — models re-add them. Regenerate from the
  original prompt with the constraint block amplified instead.
