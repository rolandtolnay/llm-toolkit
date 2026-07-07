# Icon Design Principles

Distilled from a gallery of world-class app icons (`assets/exemplars/` — home-screen
screenshots, so ignore their crop margins and compression; study the design decisions). These
principles govern Stage 2 direction design and are the foundation of the judges' rubric.

## The ten principles

1. **One mark, one field.** Nearly every great icon is a single mark on a single background
   field. Not a scene, not a composition of elements, not a logo lockup. The rare exception is
   the full-bleed character face (Duolingo), which works only because the features are enormous.

2. **Two colors do the work.** The dominant professional recipe is a white (or near-white) mark
   on one saturated field: SoundCloud, Discord, Airbnb, WhatsApp, Glovo, Claude, Wolt. A third
   color is a deliberate accent (Duolingo's orange beak), not a decoration. Multi-color marks
   (Slack, Instagram) are earned exceptions with strict internal logic — treat 4+ colors as a
   red flag, not an option.

3. **The mark fills 55-70% of the canvas.** Big enough to dominate, with even breathing room on
   all sides. Optically centered — a triangle or pin sits a touch above geometric center to
   *look* centered. Undersized marks read as timid; edge-crowding reads as broken.

4. **The silhouette carries the concept.** Render any exemplar as pure black-on-white and it
   still communicates: cloud, letter R, pin, lemon wheel, speech bubble, spark. If the icon
   needs its colors or gradients to be understood, the mark is weak.

5. **One shape language, one stroke weight.** Airbnb, Instagram, and Revolut are outline marks
   with a single fat uniform stroke. Slack repeats one lozenge shape four times. Corner radii
   agree everywhere. Mixed weights and mixed radii are the fastest tell of amateur work.

6. **Flat by default; depth is one controlled move.** Flat vector wins most categories. When
   depth appears (Obsidian's faceted crystal, Reddit's soft 3D, Linear's brushed metal), there
   is exactly one implied light source and the material logic is consistent. Depth is a style
   decision made once, never an "add more polish" slider.

7. **No text — unless the word IS the mark.** Wolt (wordmark) and Revolut (letterform R) work
   because typography is their entire concept, set fat and high-contrast. Decorative text,
   taglines, or a small app name under a mark: never.

8. **The best marks have one twist.** Glovo's pin doubles as an exclamation mark. Airbnb's "A"
   is a loop that reads as location, belly, and heart at once. Waze's speech bubble grows
   wheels. Claude's starburst is hand-cut, not geometric. One unexpected move makes a mark
   memorable — "surprisingly familiar." Zero twists is forgettable; two twists is noise.

9. **Emotion is carried by geometry and saturation before concept.** Round = friendly
   (Duolingo, Waze), sharp/faceted = technical-premium (Obsidian, Linear), saturated warm =
   energetic (SoundCloud, Reddit), desaturated dark = serious tool (Linear). Check every
   direction's geometry against the brief's half-second feeling — a friendly brand with a
   sharp-faceted mark is a contradiction no palette can fix.

10. **It must survive 48px and delight at 1024px.** At 48px only silhouette, contrast, and one
    or two shapes survive. At 1024px (App Store) the same icon must reward a close look —
    subtle grain, a soft gradient, crisp curves. Design for 48, finish for 1024.

## Exemplar annotations

| File | Mark | Why it works |
|---|---|---|
| soundcloud.webp | White cloud + level bars on orange | Two ideas fused into one silhouette; reads at any size |
| discord.webp | White game-controller face on blurple | Character implied by a glyph; zero fine detail |
| airbnb.webp | White looped "A" outline on coral | One stroke weight; three meanings in one twist |
| glovo.webp | Teal pin/exclamation on amber | The twist principle at its purest; two colors |
| duolingo.webp | Full-bleed owl face | The exception: full-bleed works when features are huge |
| reddit.webp | Soft-3D mascot head in white circle on orange | Character + one light source + hard silhouette |
| waze.webp | Speech bubble with wheels on sky blue | Playful twist; thick outline unifies |
| whatsapp.webp | Phone in speech bubble on green gradient | Concept fusion; gradient subtle enough to stay two-color |
| wolt.webp | Fat script wordmark on blue | Text as the mark, done with total commitment |
| revolut.webp | Heavy outline letterform R | Letterform route: one letter, huge weight, nothing else |
| linear.webp | Brushed-metal sliced circle on near-black | Premium via material restraint; monochrome |
| obsidian.webp | Faceted purple crystal on black | Controlled dimensionality; every facet obeys one light |
| instagram.webp | White camera outline on warm gradient | Gradient as the brand; outline stays one weight |
| slack.webp | Four two-color lozenges on white | Multi-color earned by strict repetition of one shape |
| claude.webp | Hand-cut cream starburst on terracotta | Organic irregularity as warmth; still one mark one field |
| codex.webp | Terminal glyph inside soft cloud blob, gradient | Technical concept made friendly by container shape |
| lime.webp | Lime wheel as wheel on white | Name, product, and object in one pun |

## Generation-model failure modes (encode as prompt constraints, check as judge)

- **Collapse to the nearest famous icon.** A generic concept prompt ("paper plane on blue")
  reproduces Telegram almost exactly — verified with both engines. Every prompt needs the
  brief's famous-icon collision list as explicit "do not resemble" constraints, and every
  direction needs a twist that famous icons don't have.
- **The pre-rounded tile.** Models love drawing a rounded-rectangle tile with margins inside
  the square canvas, sometimes with a fake drop shadow on a white backdrop. Demand: background
  fills the entire square canvas edge-to-edge; no rounded-corner tile; no frame; the OS applies
  the corner mask.
- **Detail creep.** Models add sparkles, secondary objects, texture, and tiny highlights that
  die at 48px. Constrain detail level explicitly and strip survivors in the revision turn.
- **Text creep.** Unprompted letters, app-name captions, watermark-like glyphs. Exclude text
  explicitly in every prompt; treat any accidental text as an automatic kill.
- **Gradient soup.** Left unconstrained, backgrounds drift into multi-stop rainbow gradients.
  Specify the exact background: one solid hex, or a two-stop gradient with named endpoints.
