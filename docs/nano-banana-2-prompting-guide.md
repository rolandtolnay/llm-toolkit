# Nano Banana 2 Prompting Guide

Comprehensive reference for prompting Google's Nano Banana 2 (Gemini 3.1 Flash Image) for high-quality image generation. Covers JSON prompt structure, professional output techniques, icon/logo design, and platform-specific tips. Compiled from community research across Reddit, X, YouTube, TikTok, Instagram, and web sources (April 2026).

---

## Model Overview

Nano Banana 2 launched February 26, 2026, built on Gemini 3.1 Flash. It combines the speed of Nano Banana (fast) with the quality of Nano Banana Pro:

- **Near-Pro quality at 2-5x speed** — generations typically take 20-30 seconds
- **4K output** — controllable aspect ratios and resolution
- **Precise text rendering** — legible text in images (infographics, greeting cards, marketing)
- **Search grounding** — pulls from Google Search during generation for real-world subject accuracy
- **Character consistency** — maintains identity across multiple generations from reference photos
- **Style templates** — built-in UI presets (cinematic, moody, steampunk, sketch, etc.)

Available in Gemini web app, mobile, Google AI Studio, and via API. Web interface defaults to Nano Banana 2; Pro/Ultra subscribers can regenerate with Nano Banana Pro via the three-dot menu.

---

## JSON vs Natural Language

**Use JSON. Always.** The community consensus is overwhelming:

| Metric | JSON | Natural Language |
|--------|------|-----------------|
| Color/lighting/composition precision | 92% | 68% |
| Processing speed | 200-700ms | Slower |
| Memory consumption | 25-30% less | Higher |
| Reproducibility | High (swap single fields) | Low (rewrite everything) |

JSON forces the model to categorize information, isolating variables like lighting, composition, and subject details. This prevents "concept bleeding" — where environment colors leak onto the subject, or background elements get held by a character.

**Source:** God of Prompt, Miraflow, Atlabs AI

---

## JSON Schema: The 6-Part Core Structure

The community has converged on a standard structure. Start with these six blocks:

```json
{
  "style": {
    "primary": "photorealistic | cinematic | flat vector | anime | oil painting | 3d render",
    "rendering_quality": "high-resolution",
    "lighting": "soft natural light | hard direct flash | golden hour | studio"
  },
  "technical": {
    "aperture": "f/1.4 - f/16",
    "depth_of_field": "shallow | deep",
    "exposure": "balanced | high-key | low-key",
    "camera_model": "iPhone 15 Pro | Sony A7R IV (optional)",
    "film_stock": "Kodak Portra 400 | CineStill 800T (optional)"
  },
  "materials": {
    "primary": "cotton | glass | metal | wood",
    "secondary": "leather | fabric",
    "texture": "polished | matte | rough | glossy"
  },
  "environment": {
    "location": "urban café | forest clearing | studio backdrop",
    "time_of_day": "morning | golden hour | night",
    "weather": "clear | overcast | rain"
  },
  "composition": {
    "framing": "rule of thirds | centered | symmetrical",
    "angle": "eye-level | low angle | bird's eye | dutch angle",
    "focus_subject": "main subject description"
  },
  "quality": {
    "resolution": "4K | 1024x1024",
    "sharpness": "crisp | soft focus",
    "post_processing": "cinematic color grading | film grain | none"
  }
}
```

### Extended Schema (for complex scenes)

For detailed work, add these optional blocks:

```json
{
  "subject": {
    "description": "physical traits, age, features",
    "clothing": [{"item": "white cotton camisole", "fit": "loose", "layer": "base"}],
    "accessories": [{"item": "silver necklace", "material": "sterling", "location": "neck"}],
    "pose": "sitting cross-legged",
    "expression": "serene smile"
  },
  "text_rendering": {
    "enabled": true,
    "text_content": "\"Your Text Here\"",
    "placement": "center | neon_sign | printed_on_shirt",
    "font_style": "bold sans-serif | handwritten | neon tube",
    "color": "#FFFFFF"
  },
  "negative_constraints": [
    "blur", "low quality", "bad hands", "text artifacts", "watermark"
  ],
  "meta": {
    "aspect_ratio": "1:1 | 16:9 | 9:16 | 4:3 | 3:2",
    "seed": 42,
    "guidance_scale": 7.5
  }
}
```

**Key principle:** Start with `style` + `environment`, then layer in `technical`, `materials`, and `composition`. Build incrementally rather than overwhelming the model.

---

## Prompting Best Practices

### Do

- **Use photographic language** — naming real cameras, film stocks, lenses, and lighting setups translates into precise visual behavior. "Shot on Kodak Portra 400, 85mm f/1.4, golden hour window light" is far more effective than "warm and pretty."
- **Wrap text in double quotes** — `"Your Text Here"` signals the model to render it literally. Critical for infographics, logos with text, greeting cards.
- **Be granular with subject descriptions** — break into specific lines rather than one run-on sentence. Separate hair, clothing, pose, expression.
- **Specify materials explicitly** — "cotton camisole" vs "spandex top" changes how light reflects. Material specificity matters.
- **Use negative constraints** — explicitly exclude common failure modes: "no blur, no watermark, no extra fingers, no text artifacts."
- **Iterate conversationally** — if the first output is 80% right, refine what you have rather than starting over. Nano Banana 2's biggest advantage is conversational editing.
- **Use style templates** — in the Gemini web UI, click a template to set the visual tone. Combine with a short subject description for fast results.

### Don't

- **Don't contradict yourself** — "low-light" + "bright exposure" confuses the model. Audit your JSON for conflicting values.
- **Don't use vague descriptions** — "cool tech logo" produces generic results. Describe style, era, mood, colors, layout, texture.
- **Don't mix environment and subject colors** — use `ColorRestriction` or `palette` fields to isolate color assignments. Prevents background colors bleeding onto the subject.
- **Don't overload the prompt** — 8-12 fields is the sweet spot. Essential fields: goal/subject, negative_constraints, and style.
- **Don't fight a bad result** — if refinement isn't converging after 2-3 iterations, open a new chat and upload your best result as a reference image.

---

## Icon & Logo Design

### iOS App Icon Prompt Template

For App Store / Linear project icons, optimize for readability at small sizes:

```json
{
  "image_type": "app icon",
  "subject": {
    "description": "[Your subject — single clear concept]",
    "style": "[kawaii | flat vector | 3D render | minimal geometric]"
  },
  "palette": {
    "primary": "[2-3 main colors]",
    "background": "solid [color] (#hex)",
    "accents": "[highlight details]"
  },
  "composition": {
    "framing": "centered, subject fills 70% of canvas",
    "shape_language": "all round soft shapes | sharp geometric | mixed",
    "detail_level": "very low — big recognizable shapes only, must read at 48x48px"
  },
  "technical": {
    "resolution": "1024x1024",
    "format": "flat vector style with soft gradients | 3D rendered | photorealistic",
    "background_type": "solid color",
    "constraints": "no text, no letters, no fine details, no realistic textures, icon-friendly, nothing outside the frame"
  }
}
```

### Icon Design Rules

1. **Single concept** — communicate one clear idea. 1-2 focus points maximum.
2. **1024x1024** — iOS App Store requirement. Google Play needs 512x512.
3. **No fine lines or busy textures** — they turn to mush at display size (29x29 to 180x180 depending on device).
4. **Bold shapes, high contrast** — most successful app icons have block-colored backgrounds.
5. **No text** — unless the text IS the brand (like "Fb"). Text is illegible at icon size.
6. **Solid backgrounds** — transparent backgrounds cause rendering issues in many contexts (Linear, Slack, etc.).
7. **Test at target size** — shrink your 1024x1024 result to 48x48 in Preview. If you can't tell what it is, simplify.

### Logo Design Tips

- Describe style, era, mood, colors, layout, and texture explicitly
- Use a 3-level text hierarchy for logos with text: large headline, medium subtitle, small detail
- Allocate 30%+ white space for clean, professional appearance
- Wrap any text in double quotes for literal rendering
- For refinement: open a new chat and upload your best attempt as a reference image

---

## Platform-Specific Tips

### Gemini Web Interface (gemini.google.com)

- **Default model is Nano Banana 2** — no setup needed
- **Style templates** — click presets (monochrome, runway, cinematic, moody, self-portrait, steampunk) to set visual tone without prompting
- **Reference images** — click + in the prompt bar to upload up to 14 reference images
- **Regenerate with Pro** — three-dot menu → regenerate using Nano Banana Pro (Pro/Ultra subscribers)
- **Conversational refinement** — describe what to change in plain English after JSON generation
- **Safety filters active** — won't generate certain subjects, but irrelevant for professional/design use cases

### API (Google AI Studio / Vertex AI)

- **Batch generation** — programmatically generate dozens of variations
- **No UI system prompts** — raw model access
- **Seed control** — reproducible generations with `seed` parameter
- **Steps control** — 10-100 (default 40), higher = more detail but slower
- **Guidance scale** — 1.0-20.0 (default 7.5), higher = stricter prompt adherence

### Recommendation

Use the **web interface** for creative exploration and single-image refinement. Use the **API** for batch generation, automation, or pipeline integration.

---

## Advanced Techniques

### Character Consistency Across Generations

Upload reference images and explicitly state "keep the identity consistent of all characters." Nano Banana 2 maintains clothing, accessories, and facial features across multiple prompts in the same conversation.

### Location/Style Swapping

With JSON, swap a single block to change the entire environment or mood while keeping everything else identical:
- Change `environment.location` from "urban café" to "neon-lit rain-slicked street"
- Change `style.lighting` from "soft diffused" to "hard direct flash"
- The structured format prevents unintended changes to other elements

### Non-Photorealistic Adaptation

Change `style.primary` to "oil painting", "3D render", "anime", or "pixel art" while keeping the same subject/composition blocks. Adjust subject descriptions to match the medium (e.g., "bold outlines" for anime, "smooth polygonal surfaces" for 3D).

### Text Translation

Nano Banana 2 can translate text within existing images. Upload an image with text and ask it to translate to another language while preserving the layout.

### Search Grounding

Nano Banana 2 pulls from Google Search during generation. For real-world subjects (buildings, celebrities, products), naming them specifically produces more accurate depictions than describing their appearance.

---

## Community Resources

- **GitHub: awesome-nanobanana-pro** — curated prompt examples and use cases
- **GitHub: awesome-nano-banana-pro-prompts** — 10,000+ prompts with preview images, 16 languages
- **GitHub: gemini-image-prompting-handbook** — open source JSON schema for structured prompts
- **GitHub Gist: alexewerlof** — comprehensive draft-07 JSON Schema with all field types and enums
- **nanobananapro.cloud** — prompt library with categorized templates including app icons
- **nanobananaprompt.org** — community prompt library
- **Google Cloud Blog** — official prompting guide from Google

---

## Quick Reference: Field Priority

When you need to keep a prompt lean, these are the fields that matter most (in order):

1. **subject.description** — what you're generating (required)
2. **style.primary** — the visual medium (required)
3. **negative_constraints** — what to exclude (highly recommended)
4. **composition.framing** — how it's framed
5. **palette / color** — color control
6. **technical.aperture + lighting** — the two biggest quality levers
7. **meta.aspect_ratio** — output dimensions
8. Everything else — layer in as needed

---

*Research date: April 4, 2026. Sources: @NanoBanana (X), @pictsbyai, @youngcatwoman, r/GeminiAI, Tasia Custode (YouTube), Atomic Gains (YouTube), Dan Kieft (YouTube), @learnwithseb (TikTok), @sabrina_ramonov (TikTok), @nathanhodgson_ (TikTok), God of Prompt, Atlabs AI, Leonardo.ai, Miraflow, fofr.ai, nanobananapro.cloud, ImagineArt, Apple HIG, Google Cloud Blog.*
