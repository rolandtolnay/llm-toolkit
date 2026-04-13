# Visual Evaluation Rubric

Apply this rubric every time the user returns with a generated PNG. Score each criterion pass/fail with a one-line reason. The single most-important failing criterion drives the next refinement.

## How to use

1. Use the `Read` tool to load the PNG. Claude Code supports PNG/JPG natively — the image appears in your context for visual inspection.
2. Score all 8 criteria. Do not skip any. For flat vector icons, criterion 6 may be marked N/A.
3. Write the scored rubric to `./icons/<slug>/NN-critique.md` using the format at the bottom of this file.
4. Pick ONE failing criterion — the one that most hurts professional appearance — to drive the next refinement per `iteration-playbook.md`.

## The 8 criteria

### 1. Readable at 48×48 (the squint test)

**The most important criterion. Non-negotiable.**

Mentally shrink the icon to 48 pixels. Ask: "Can I tell what this is?"

- **Pass:** Central concept is recognizable at small size. Silhouette still communicates.
- **Fail:** Icon becomes a blob. Loses its defining feature. Details dominate over shape.

An icon that fails this is unshippable regardless of how beautiful it looks at 1024.

### 2. Single concept

One clear focal point with no visual competition.

- **Pass:** Eye lands in one place. Secondary elements support the primary.
- **Fail:** Two or more elements fight for attention (e.g., a calendar AND a lightning bolt AND a checkmark).

### 3. Palette match

Colors align with the brief's hex palette. ±1 unexpected accent is acceptable; more is not.

- **Pass:** All major color areas are from `palette.primary` + `palette.background` + at most one accent.
- **Fail:** Nano Banana invented new colors that don't appear in the brief.

### 4. Silhouette clarity

Imagine the icon rendered as pure black-on-white. Is the outline of the main subject still readable as the concept?

- **Pass:** Silhouette alone communicates the concept.
- **Fail:** Silhouette is a meaningless blob — the icon relies entirely on color or texture to communicate what it is.

### 5. Shape language consistency

Corner radii, stroke weights, and shape types are cohesive across all elements.

- **Pass:** If the brief said "all-round soft", every corner is round. If "sharp geometric", every corner is sharp.
- **Fail:** Mixed radii without intentional reason. Inconsistent stroke weights. Some elements beveled, others flat.

### 6. Depth and lighting plausibility

For 3D, skeuomorphic, or gradient mesh styles: is the light source consistent across all elements?

- **Pass:** One implied light source. Highlights and shadows agree on direction.
- **Fail:** Highlights on top-left AND top-right. Shadows falling in contradictory directions. Reflections that don't match the implied source.
- **N/A:** Flat vector icons — skip this criterion.

### 7. Clean output (no text, no watermark, no artifacts)

- **Pass:** No text overlays, no Gemini watermark, no weird artifacts.
- **Fail:** Any text (even lorem-ipsum-style decoration), visible watermarks, glitched edges, chromatic aberration, extra fingers on anything resembling a hand.

This criterion has a high false-negative rate with Nano Banana — it sometimes adds decorative "text" that looks like typography. Look carefully.

### 8. Competitive diversity

Does it look meaningfully different from the competitors listed in the brief?

- **Pass:** Unique enough to not be mistaken for any named competitor at a glance.
- **Fail:** Too similar in palette, layout, or central mark to one of the competitors.

## What "done" looks like

- **7 or 8 of 8 criteria pass** → icon is shippable. Proceed to variant generation (dark mode, tinted, notification badge — see `iteration-playbook.md`).
- **5–6 of 8 pass** → one more refinement iteration, focused on the single biggest failing criterion.
- **≤4 of 8 pass** → bigger problem. Consider the escape hatch in `iteration-playbook.md` (new Gemini chat + reference image).

**The 48×48 test (criterion 1) is a hard gate.** If it fails, the icon is not done regardless of other scores.

## Critique file format

Write the critique to `./icons/<slug>/NN-critique.md` (where NN matches the iteration number) with this exact structure:

```markdown
# Critique — Iteration NN

**Image:** `NN-generated.png`
**Date:** YYYY-MM-DD

## Rubric scores

| # | Criterion | Pass/Fail | Reason |
|---|---|---|---|
| 1 | Readable at 48×48 | ✅ / ❌ | <one line> |
| 2 | Single concept | ✅ / ❌ | <one line> |
| 3 | Palette match | ✅ / ❌ | <one line> |
| 4 | Silhouette clarity | ✅ / ❌ | <one line> |
| 5 | Shape language consistency | ✅ / ❌ | <one line> |
| 6 | Depth/lighting plausibility | ✅ / ❌ / N/A | <one line> |
| 7 | Clean output | ✅ / ❌ | <one line> |
| 8 | Competitive diversity | ✅ / ❌ | <one line> |

**Score:** X/8 (or X/7 if criterion 6 is N/A)

## What works
- <observation 1>
- <observation 2>

## What doesn't
- <observation 1>
- <observation 2>

## Next change focus
**<The single most important failing criterion>** — <why this one first, per iteration playbook refinement order>
```
