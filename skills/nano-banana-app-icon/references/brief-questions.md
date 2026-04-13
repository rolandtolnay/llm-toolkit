# Discovery Brief — Questions Framework

The brief is the single biggest predictor of professional-looking output. Do not skip. Do not shortcut. Do not generate a prompt until all 9 questions are answered in usable form.

A vague answer is worse than a narrow one — probe until you get something specific and concrete.

## The 9 questions

Ask these in order. Use `AskUserQuestion` for the three enumerated-choice questions (7, 8, 9). Ask the open-ended questions (1–6) as free-text follow-ups, one at a time so the user can think.

### Product (questions 1–3)

**1. What does the app do, in one sentence?**
- Good: "Helps parents coordinate family schedules and shared to-dos"
- Vague: "Productivity app" → probe: "for what kind of user, doing what?"
- Unlocks: `subject.description` context in the JSON prompt.

**2. What is the single most recognizable visual concept a user would associate with it?**
- Must be ONE thing. If the answer contains "and", push back: "pick one."
- Examples: a calendar square, a shield, a lightning bolt, a letter, a character, a wave, a flame.
- Unlocks: the central subject of the icon — the #1 driver of recognizability at 48×48.

**3. Who is the primary user?**
- Good: "Busy parents 30–45" / "Enterprise IT admins" / "Kids 8–12" / "Indie developers"
- Unlocks: playful vs. serious, vibrant vs. muted, round vs. sharp — dictates the whole mood vector.

### Brand (questions 4–6)

**4. Is there an existing logo, wordmark, or color palette?**
- If YES: ask for the image path OR hex codes. Flag this as a brand-anchor reference image for the prompt template (this is the single biggest professional-quality unlock).
- If NO: ask the user to pick a 2–3 color palette now with hex codes. Do not accept vague color names ("blue") — push for hex values.
- Unlocks: `palette.primary`, `palette.background`, and the reference-image strategy.

**5. What 3 adjectives describe the brand?**
- Good: "trustworthy, playful, premium" / "sharp, technical, minimal" / "warm, organized, approachable"
- Must be exactly 3. More = diluted. Fewer = insufficient.
- Unlocks: `subject.mood` — the emotional tone tokens in the prompt.

**6. What are 2–3 competitor app icons you'd sit next to on the home screen? What do you want to borrow, and what do you want to diverge from?**
- Have the user actually look at the App Store pages.
- Good: "Cozi uses muted teal — I want warmer. Fantastical uses red — I don't want to look like a calendar. Things uses a checkmark — I like the simplicity."
- Unlocks: the `negative_constraints` "do not resemble" list and competitive positioning.

### Visual direction (questions 7–9)

**7. Style family? Pick ONE.** (Use `AskUserQuestion` with these options.)
- **Flat vector** — cleanest, most modern, works at all sizes, safest choice.
- **Soft 3D render** — glossy, popular 2026 style, high visual appeal, slightly harder to read small.
- **Skeuomorphic** — textured, realistic materials. Use sparingly — can date quickly.
- **Glyph on solid** — letter or symbol on a colored background. Most recognizable at small sizes.
- **Gradient mesh** — abstract, colorful, artistic. Best for creative tools.
- **Kawaii / character-based** — friendly, playful. Only if audience matches.

**8. Shape language? Pick ONE.** (Use `AskUserQuestion`.)
- **All-round soft shapes** — friendly, approachable.
- **Sharp geometric** — technical, precise.
- **Mixed** — warn the user this is tricky to pull off consistently.

**9. Background?** (Use `AskUserQuestion`.)
- **Solid color** — safest. Required for Linear, Slack, and App Store.
- **Subtle gradient** — acceptable only if style family is 3D or gradient mesh.
- **Textured** — rarely a good idea at icon size. Push back unless the user has a reason.

## Probing checklist

Before moving to Step 3 (prompt generation), verify every item:
- [ ] App description is specific enough to picture the product
- [ ] Central concept is ONE thing, not two or three
- [ ] Target user is named with an age/role, not "everyone"
- [ ] Palette has hex codes, not color names
- [ ] Exactly 3 adjectives — not 2, not 5
- [ ] At least 2 competitors with a specific "diverge from" note each
- [ ] Style family is a single choice from the enumerated list
- [ ] Shape language is a single choice
- [ ] Background has a specific hex code if solid, or an explicit gradient direction

If any item fails, go back and ask a follow-up question before proceeding.

## Brief file format — what to write to disk

Write the captured answers to `./icons/<slug>/brief.md` using this exact structure. This is the canonical input to Step 3.

```markdown
# <App Name> — App Icon Brief

**App:** <one-sentence description from Q1>
**Central concept:** <ONE thing from Q2>
**User:** <specific user from Q3>

**Existing brand:** <logo path, or "none">
**Palette:** <primary hex>, <secondary hex>, <accent hex>
**Adjectives:** <adj1>, <adj2>, <adj3>
**Competitors:** <name1> (<diverge note>), <name2> (<diverge note>)

**Style family:** <choice from Q7>
**Shape language:** <choice from Q8>
**Background:** <choice from Q9 — with hex if solid>

**Must-not:** no fine lines, no text, no busy textures, no colors outside the palette
```

## Worked example — SnapPlan

```markdown
# SnapPlan — App Icon Brief

**App:** SnapPlan helps parents coordinate family schedules and shared to-dos.
**Central concept:** a calendar square with a friendly spark in the top-right corner.
**User:** busy parents, 30–45.

**Existing brand:** logo at ~/Downloads/snapplan-logo.png
**Palette:** #FF6B35 (primary), #1F2937 (dark), #FFFFFF (light)
**Adjectives:** warm, organized, playful
**Competitors:** Cozi (muted teal — want warmer), Fantastical (red — want to diverge), Things (checkmark — like the simplicity)

**Style family:** soft 3D render
**Shape language:** all-round soft shapes
**Background:** solid #FF6B35

**Must-not:** no fine lines, no text, no busy textures, no colors outside the palette
```

This is the input Step 3 consumes to fill the JSON template.
