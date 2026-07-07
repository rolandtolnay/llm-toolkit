# Interview Guide — The Icon Brief

Six questions, asked conversationally. This is the highest-leverage stage of the pipeline: every
downstream prompt, judgment, and edit traces back to these answers. Long enough that the user
invests, short enough that it never feels like a survey.

Ask the free-text questions one at a time so the user can think. Use `AskUserQuestion` only for
Q5 (style appetite). A vague answer is worse than a narrow one — probe until you have something
concrete, using the notes under each question.

Unlike a single-concept icon brief, do NOT ask the user to pick one visual concept. Concept
exploration is the pipeline's job (Stage 2 produces 4 directions). The interview captures the
strategy; the directions translate it into imagery.

## Q1 — Product and audience

> "What does the app do, and who is it for? A sentence or two."

- Good: "Tracks parcels from any carrier automatically by reading your email — for online
  shoppers who order weekly."
- Vague: "a productivity app" → probe: "for whom, doing what, in what moment of their day?"
- If a PROJECT.md / CONTEXT.md exists in the working directory, read it first and confirm
  instead of asking cold.

## Q2 — The half-second feeling

> "Someone sees this icon on a stranger's home screen for half a second. What should they
> *feel* — before they've had time to think?"

Then: "Give me exactly 3 adjectives for the brand." (Exactly 3. More dilutes, fewer starves.)

- Good: "calm relief — like someone else is handling it" + "trustworthy, warm, effortless"
- This is the most important answer in the brief. Icons communicate pre-verbally: shape, color,
  and weight land before any concept is decoded. Every direction in Stage 2 must be justified
  against this feeling.
- If the user answers with features instead of feelings, ladder up: "and when the app does
  that, what does the person feel?"

## Q3 — Brand reality

> "What already exists? App name, a logo or mark, brand colors, a font — or is this a blank
> slate?"

- If a logo/mark exists: get the file path. It becomes a reference image; one direction should
  adapt the existing mark rather than invent.
- If colors exist as names ("blue"), push for hex codes or a file to sample from.
- If nothing exists: fine — palettes are proposed per-direction in Stage 2. Note any colors the
  user is drawn to or bans.

## Q4 — Home-screen neighbors

> "Which apps will this sit next to on the target user's home screen? And which competitors
> exist — what should we clearly NOT be mistaken for?"

- Push for 2-4 named apps with a one-line note each ("Flighty — love the craft, too technical
  for us").
- **Also collect famous-icon collisions yourself**: for each obvious concept in this category,
  name the famous icon that owns it (a paper plane is Telegram's; a white phone on green is
  WhatsApp's; a camera outline is Instagram's). Image models collapse generic concepts into the
  nearest famous icon they memorized — these names go into every prompt's "do not resemble"
  list and into the judges' distinctiveness check.

## Q5 — Style appetite (AskUserQuestion, multiSelect)

> "Which of these ways of being resonate for this brand? Pick any that fit."

| Option | What it means | Exemplars (assets/exemplars/) |
|---|---|---|
| Playful & characterful | Mascot, face, or personality-forward mark | duolingo, reddit, waze |
| Minimal bold glyph | One flat symbol on a solid field | soundcloud, discord, airbnb, glovo |
| Dimensional & premium | Controlled 3D, material, light | obsidian, linear, reddit |
| Explore freely | No constraint — the pipeline proposes | — |

Selections bias the Stage 2 directions; they do not forbid a wildcard. "Explore freely" means
all four directions are yours to design.

## Q6 — Hard rules

> "Anything the icon MUST contain, and anything it must NEVER contain?"

- Musts: a letterform, an existing mascot, a specific object, a color.
- Must-nots: text, specific colors, clichés the user is sick of, imagery with bad connotations
  in their market.
- Defaults that apply unless the user overrides them: no text in the icon (unless the word or
  letter IS the mark), no photorealism, no UI screenshots.

## Probing checklist

Before writing the brief, verify:

- [ ] Product description concrete enough to picture the user mid-task
- [ ] A named feeling plus exactly 3 adjectives
- [ ] Brand assets either captured (paths, hex codes) or explicitly blank-slate
- [ ] 2+ neighbors/competitors with diverge notes, plus your own famous-icon collision list
- [ ] Style appetite recorded (or "explore freely")
- [ ] Musts and must-nots explicit, defaults confirmed

## Brief file format — `icons/<slug>/brief.md`

```markdown
# <App Name> — Icon Brief

**App:** <one-sentence description>
**Audience:** <specific user>
**Half-second feeling:** <the feeling>
**Adjectives:** <adj1>, <adj2>, <adj3>

**Existing brand:** <logo path / hex codes / "blank slate">
**Neighbors:** <app1> (<note>), <app2> (<note>)
**Famous-icon collisions to avoid:** <icon1 (concept)>, <icon2 (concept)>

**Style appetite:** <selections from Q5>
**Must:** <or "nothing mandated">
**Must not:** <user items> + defaults: no text, no photorealism, no UI screenshots
```

## Worked example — PostOwl

```markdown
# PostOwl — Icon Brief

**App:** Reads your email and tracks every parcel automatically, across carriers.
**Audience:** Frequent online shoppers, 25-45, non-technical.
**Half-second feeling:** calm relief — someone is watching your packages so you don't have to.
**Adjectives:** watchful, warm, effortless

**Existing brand:** blank slate; user likes deep teal, bans corporate blue
**Neighbors:** Flighty (love the craft, too technical), AfterShip (generic box+truck cliché)
**Famous-icon collisions to avoid:** Telegram (paper plane), Twitter/owl apps (bird glyphs),
Amazon (smile-arrow parcel)

**Style appetite:** Playful & characterful, Minimal bold glyph
**Must:** nothing mandated
**Must not:** boxes-with-motion-lines cliché + defaults: no text, no photorealism, no UI screenshots
```
