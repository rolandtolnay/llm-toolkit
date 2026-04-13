# JSON Prompt Template — App Icon

A focused JSON template optimized specifically for app icons. Based on the generic 6-part schema from the wider Nano Banana 2 prompting guide, but trimmed to the fields that matter for icons and pre-filled with non-negotiable constants.

## Why JSON (not prose)

Nano Banana 2 produces more predictable output from structured briefs than from natural-language prompts. The structured format also makes iteration trivially — in Step 6 (refinement), the user swaps one field instead of rewriting an entire paragraph.

Never convert these prompts to prose. Always keep them as JSON.

## Mapping table — brief answer → JSON field

| Brief line | JSON field | Notes |
|---|---|---|
| Central concept (Q2) | `subject.description` | The ONE thing. Phrase as a noun with 1–2 adjectives. |
| Style family (Q7) | `subject.style` + `technical.format` | Duplicated on purpose — Nano Banana weighs both. |
| Adjectives (Q5) | `subject.mood` | Exactly 3 tokens. |
| Palette primary (Q4) | `palette.primary` | Comma-separated hex codes. |
| Palette background (Q4 + Q9) | `palette.background` | Single hex, prefixed with "solid". |
| Palette accent (Q4) | `palette.accents` | Optional highlights. |
| Shape language (Q8) | `composition.shape_language` | Verbatim from the enumerated list. |
| Competitors (Q6) | `negative_constraints` | Append as `"do not resemble: X, Y"`. |

## Non-negotiable constants

These values are always the same for app icons. Never let the user override them in the initial prompt — they encode Apple HIG-style constraints that are the difference between "AI slop" and "designed icon".

- `image_type: "app icon"`
- `composition.framing: "centered, subject fills 70% of canvas"`
- `composition.detail_level: "very low — big recognizable shapes only, must read at 48x48px"`
- `technical.resolution: "1024x1024"`
- `technical.background_type: "solid color"`
- `technical.constraints: "no text, no letters, no fine details, no realistic textures, icon-friendly, nothing outside the frame"`

## The template (fill in the placeholders)

```json
{
  "image_type": "app icon",
  "subject": {
    "description": "{{CENTRAL_CONCEPT_FROM_Q2}}",
    "style": "{{STYLE_FAMILY_FROM_Q7}}",
    "mood": "{{ADJECTIVE_1}}, {{ADJECTIVE_2}}, {{ADJECTIVE_3}}"
  },
  "palette": {
    "primary": "{{HEX_1}}, {{HEX_2}}",
    "background": "solid {{BACKGROUND_HEX}}",
    "accents": "{{HEX_ACCENT}}"
  },
  "composition": {
    "framing": "centered, subject fills 70% of canvas",
    "shape_language": "{{SHAPE_LANGUAGE_FROM_Q8}}",
    "detail_level": "very low — big recognizable shapes only, must read at 48x48px"
  },
  "technical": {
    "resolution": "1024x1024",
    "format": "{{STYLE_FAMILY_FROM_Q7}} with soft gradients",
    "background_type": "solid color",
    "constraints": "no text, no letters, no fine details, no realistic textures, icon-friendly, nothing outside the frame"
  },
  "negative_constraints": [
    "blur", "low quality", "text", "watermark",
    "do not resemble: {{COMPETITOR_1}}, {{COMPETITOR_2}}"
  ]
}
```

## Reference image handling

If the brief has an existing logo (Q4 = yes):
- Instruct the user in the output file to ATTACH the logo in Gemini before submitting the prompt (click the + button in the prompt bar).
- Append this sentence after the JSON: `Use the attached reference image for palette and shape language, but do NOT copy the composition.`

If the brief has no existing logo:
- Proceed with the prompt as-is. The first generated result can itself become the reference image for iteration 2 if needed.

## Worked example — SnapPlan (filled)

```json
{
  "image_type": "app icon",
  "subject": {
    "description": "a friendly calendar square with a small spark in the top-right corner",
    "style": "soft 3D render",
    "mood": "warm, organized, playful"
  },
  "palette": {
    "primary": "#FF6B35, #1F2937",
    "background": "solid #FF6B35",
    "accents": "#FFFFFF"
  },
  "composition": {
    "framing": "centered, subject fills 70% of canvas",
    "shape_language": "all-round soft shapes",
    "detail_level": "very low — big recognizable shapes only, must read at 48x48px"
  },
  "technical": {
    "resolution": "1024x1024",
    "format": "soft 3D render with soft gradients, glossy highlights, subtle drop shadow",
    "background_type": "solid color",
    "constraints": "no text, no letters, no fine details, no realistic textures, icon-friendly, nothing outside the frame"
  },
  "negative_constraints": [
    "blur", "low quality", "text", "watermark",
    "do not resemble: Cozi, Fantastical, Google Calendar"
  ]
}
```

## Output file format — what to write to disk

Write the prompt to `./icons/<slug>/01-initial-prompt.md` with this exact structure:

````markdown
# <App Name> — Initial Prompt (iteration 1)

**Goal:** <one-line description of what this icon should communicate>

**Reference image:** <absolute path to logo, or "none — generate from scratch">

## Prompt (paste into gemini.google.com)

```json
<filled-out JSON>
```

<If reference image exists, add:>
**Important:** attach the reference image in Gemini before pasting. Click the **+** button in the prompt bar to upload `<path>`.

## Instructions
1. Go to gemini.google.com
2. Attach the reference image if listed above
3. Paste the JSON above as your prompt
4. Generate 4 variations
5. Pick the best one and download it. Save it to `icons/<slug>/01-generated.png`
6. Come back to this chat and tell me the path — I will critique it against the rubric and write the next prompt
````
