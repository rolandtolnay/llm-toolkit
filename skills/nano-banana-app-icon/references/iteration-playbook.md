# Iteration Playbook

How to turn a failing rubric criterion into a targeted refinement prompt. One change per iteration. Always.

## The refinement order (load-bearing)

Never skip ahead. If criterion 4 (silhouette) is failing, fix silhouette before touching depth or lighting. Fixing lighting on a muddy silhouette is wasted work — the iteration will score worse.

The order:

1. **Silhouette clarity** (criterion 4) — fix shape legibility first
2. **Single concept** (criterion 2) — remove competing elements
3. **48×48 readability** (criterion 1) — simplify until it reads small
4. **Palette match** (criterion 3) — fix colors after shape is locked
5. **Shape language consistency** (criterion 5) — cohere radii and strokes
6. **Depth and lighting** (criterion 6) — add dimensionality
7. **Competitive diversity** (criterion 8) — differentiate final pass
8. **Clean output / artifacts** (criterion 7) — remove text, watermarks (usually requires regenerating the original JSON with amplified negatives, not a conversational edit)

## One change per turn — why it matters

Nano Banana 2's semantic editing is precise when given ONE instruction at a time. Stacked edits ("make it more premium AND change the colors AND add depth") cause the model to compromise across all three changes, usually worsening everything.

**Send ONE change. Wait for the result. Score. Send the next change.**

Tell the user this explicitly in every refinement file — they will otherwise be tempted to batch edits.

## Failure mode → refinement prompt

Pattern-match the failing criterion to one of the templates below. Fill in specifics from the brief. Each template is phrased as a conversational edit to paste into the SAME Gemini chat as the previous iteration (unless iteration count ≥ 3, in which case see the escape hatch).

### "Concept too complex" (criterion 2 fail)

```
Simplify to just the {{PRIMARY_OBJECT}}. Remove the {{SECONDARY_ELEMENT}} entirely. Keep the palette, style, and background identical.
```

### "Doesn't read at 48px" (criterion 1 fail)

```
Make the {{PRIMARY_OBJECT}} 30% larger and center it. Remove the small details ({{LIST_SMALL_DETAILS}}). Keep the palette and style identical.
```

### "Palette drift" (criterion 3 fail)

```
Change all colors to exactly these hex values: {{HEX_1}}, {{HEX_2}}, {{HEX_3}}. Background should be solid {{BG_HEX}}. Do not use any other colors. Keep the subject and composition identical.
```

### "Silhouette is unclear" (criterion 4 fail)

```
Make the outline of the {{PRIMARY_OBJECT}} bolder and more distinct. The silhouette should be readable even as pure black on white. Keep the colors and style identical.
```

### "Inconsistent shape language" (criterion 5 fail)

```
Make all corners and edges {{SHAPE_LANGUAGE}} — for example, rounded with a 12px radius, or sharp 90-degree corners. Apply this consistently to every element. Keep everything else identical.
```

### "Flat / lacks depth" (criterion 6 fail, for 3D styles)

```
Add a soft drop shadow underneath the {{PRIMARY_OBJECT}} and a subtle highlight along the top edge. The light source is top-left. Keep the silhouette and palette identical.
```

### "Contradictory light source" (criterion 6 fail)

```
The light source is top-left. Move all highlights to the top and top-left edges. Move all shadows to the bottom and bottom-right edges. Keep the subject, palette, and composition identical.
```

### "Looks like competitor {{X}}" (criterion 8 fail)

```
This looks too much like {{COMPETITOR}}. Change the {{DIFFERENTIATING_FEATURE — usually the palette or the central mark's shape}} to distance it. Specifically: {{CONCRETE_CHANGE}}. Keep the style family and mood identical.
```

### "Has text or watermark" (criterion 7 fail)

This is usually NOT fixable by conversational edit — Nano Banana often adds text back after removing it. Instead, regenerate from the original JSON prompt with amplified negative constraints. Write a new file `NN-regen-prompt.md` containing the original JSON, but replace `negative_constraints` with:

```json
"negative_constraints": [
  "text", "letters", "numbers", "characters", "typography", "writing", "words",
  "watermark", "logo overlay", "signature", "caption", "label",
  "blur", "low quality"
]
```

Instruct the user to open a NEW Gemini chat for this regeneration.

## Refinement file format — what to write to disk

Write the refinement prompt to `./icons/<slug>/NN-refinement-prompt.md` (where NN is the new iteration number, e.g., `02-refinement-prompt.md`) with this structure:

````markdown
# <App Name> — Refinement Prompt (iteration NN)

**What's changing:** <the single criterion being fixed>
**Why this one first:** <one-line rationale from refinement order>

## Prompt (paste into the SAME gemini chat as iteration NN-1)

```
<the refinement text, no JSON — conversational edit>
```

## Instructions
1. Go back to the Gemini chat where you generated iteration NN-1 — do NOT open a new chat
2. Paste the text above as a new message
3. Generate variations (Gemini usually gives you 2–4 automatically)
4. Pick the best one, download it, save as `icons/<slug>/NN-generated.png`
5. Come back here with the path — I will score it and write the next prompt

**Remember:** one change per turn. Do not add your own modifications to the refinement text — the point is to isolate this single change so we can see exactly what it does to the rubric score.
````

## The escape hatch

Trigger this when ANY of the following are true:
- 3 iterations in the same Gemini chat without the rubric score improving
- Rubric score dropping iteration-over-iteration
- Stuck below 6/8 after 3+ iterations

**Why:** Gemini chats accumulate conflicting state. After enough edits, the model starts averaging across contradictory instructions and every new edit pulls the image in a new wrong direction.

**The hatch:**
1. Identify the iteration with the highest rubric score so far. Call this the "best so far" image.
2. Open a NEW Gemini chat — do not continue the old one.
3. Attach the "best so far" PNG as a reference image in the new chat (click + in the prompt bar).
4. Write a restart prompt to `./icons/<slug>/NN-restart-prompt.md` using this template:

````markdown
# <App Name> — Restart Prompt (iteration NN, from iteration MM)

**Reason:** 3 iterations without converging. Opening a fresh chat with iteration MM as reference.

## Prompt (paste into a NEW gemini chat, with `icons/<slug>/MM-generated.png` attached)

```
Use the attached image as the starting point. Make exactly this change: {{SINGLE_MOST_IMPORTANT_FIX_FROM_RUBRIC}}. Keep everything else about the image identical — same palette, same composition, same style, same background.
```

## Instructions
1. Open gemini.google.com in a new tab (do not continue the previous chat)
2. Click + in the prompt bar and attach `icons/<slug>/MM-generated.png`
3. Paste the prompt above
4. Generate variations, download the best, save as `NN-generated.png`
5. Come back — I will score from the fresh baseline
````

5. Resume the normal loop from Step 5 of the main workflow.

## When to stop iterating

Stop when ANY of these are true:
- Rubric score is 7/8 or 8/8 AND the 48×48 test passes (criterion 1).
- The user says "good enough" — respect it, don't push.
- You have reached 5 iterations total. After 5, more iterations rarely improve things. Offer to regenerate from scratch with an updated brief (go back to Step 2).

## After completion — generate variants

Once the hero icon is locked, offer to generate these variants. Each is a single-field swap on the final JSON, taking one Gemini generation.

**Dark mode** — swap the background:
```json
"palette": { "background": "solid #0A0A0A", ... }
```

**iOS tinted mode (monochrome)** — swap style and palette:
```json
"subject": { "style": "monochrome glyph" },
"palette": { "primary": "#FFFFFF", "background": "solid transparent" }
```

**Notification badge (high contrast)** — amplify the primary silhouette:
```json
"composition": { "detail_level": "minimum — just the primary silhouette, high contrast" }
```

Save each variant prompt as `final-variant-<name>.md` in the icon folder. Remind the user these can go into the same Gemini chat as the final iteration.
