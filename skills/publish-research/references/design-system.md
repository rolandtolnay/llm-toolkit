# Design system

Published research pages use the shared stylesheet, navigation script, and article script configured in `.publish-research.json`. The bundled starter files are `assets/styles.css`, `assets/nav.js`, and `assets/article.js`; their default target is `public/shared/`. The article script owns chip-nav active state, lazy YouTube embeds, criterion cross-reference opening, and print drawer expansion so sites can keep a CSP that rejects inline scripts.

## Typography

Load all three families:

```html
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600;8..60,700&family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&display=swap" rel="stylesheet">
```

- Body: `Source Serif 4`
- Editorial display headings and pick names: `Fraunces`
- UI labels, metadata, buttons, nav: `DM Sans`

## Tokens

Core tokens: `--bg`, `--bg-alt`, `--bg-deep`, `--paper`, `--ink`, `--ink-2`, `--ink-3`, `--rule`, `--rule-light`, `--green`, `--green-soft`, `--amber`, `--amber-soft`, `--red`, `--red-soft`, `--link`, `--plum`, `--sage`.

Compatibility aliases exist for shared shell/directory code: `--surface`, `--text`, `--text-2`, `--text-3`, `--border`, `--border-light`, `--green-bg`, `--amber-bg`, `--red-bg`.

## Page shell

- `.page-content` — wraps directory/article content and shifts for desktop sidebar.
- `.container` — centered article column.
- `.sidebar*`, `.sidebar-toggle`, `.sidebar__overlay` — manifest-driven shared sidebar from the configured navigation script.
- `footer`, `.made-with` — page footer and sign-off.

## Chip navigation

- `.chip-nav` — sticky top article nav.
- `.chip-nav__bar` — horizontal scroll container.
- `.chip` — section link.
- `.chip.is-active` — current section state from page-local IntersectionObserver.
- `.chip__dot`, `.chip__dot--green|amber|plum|ink` — semantic color cue.

Required anchors: `#picks`, `#criteria`, `#compare`, `#all-products`, `#tradeoffs`, `#ruled-out`, `#evidence`.

## Hero and TL;DR

- `.hero` — top article region.
- `.eyebrow` — category/date label.
- `.headline` — Fraunces editorial h1.
- `.hero__lede` — research approach summary.
- `.tldr`, `.tldr__label`, `.tldr__rows`, `.tldr__row` — hero matrix of recommendation tiers.
- `.tldr__tier`, `.tldr__tier--best|budget|premium` — tier badge.
- `.tldr__main`, `.tldr__name`, `.tldr__why`, `.tldr__price` — row content.
- `.tldr__price small.in|out` — stock/status cue.
- `.tldr__cta` — hero action row.
- `.brief`, `.brief__label` — compact context/source sentence.

## Buttons

- `.btn-row` — flex wrapper.
- `.btn` — base button.
- `.btn--primary` — main action.
- `.btn--ghost` — secondary/outline action.
- `.btn__arrow` — optional arrow glyph.

## Sections

- `section` — standard vertical rhythm and divider.
- `.section-head` — section opener wrapper.
- `.section-num` — small section number.
- `.section-title` — Fraunces section h2.
- `.section-deck` — section explanatory deck.

## Criteria and myths

- `.criteria-stack` — stack of expandable criterion cards.
- `.crit` — `<details>` criterion/aspect card.
- `.crit__num`, `.crit__head`, `.crit__title`, `.crit__tldr`, `.crit__expand`, `.crit__body` — criterion card structure.
- `.pull` — optional emphasized excerpt in criterion body.
- `.crit__tradeoff` — optional inline tradeoff callout inside criterion body.
- `.myths`, `.myths__title`, `.myth`, `.myth__head`, `.myth__name`, `.myth__tag` — myth/debunking component.
- `.aside` — lightweight serif side note for source-backed caveats.
- Tables and blockquotes inside `.crit__body` are styled identically to `.drawer__body`.

Keep `data-deep-dive="crit-or-aspect-id"` on cross-reference links that should open a criterion card.

## Comparison matrix

- `.matrix`, with `.matrix--1|2|3` for the actual recommendation count — vertical comparison matrix.
- `.matrix__head` — tier/model/price header with one product column per recommendation.
- `.tier`, `.tier--best|budget|premium`, `.name`, `.price` — header labels.
- `.matrix__row` — one comparable criterion/spec row.
- `.matrix__cell` — cell value.
- `.matrix__cell.win|loss` — optional semantic emphasis when the source supports a clear winner/weakness.

## Picks

- `.pick`, `.pick--best|budget|premium` — recommendation article card.
- `.pick__header`, `.pick__tier-block`, `.pick__tier-num`, `.pick__tier`, `.pick__price` — pick header.
- `.pick__name`, `.pick__specs`, `.pick__verdict`, `.pick__meta` — model details and verification status.
- `.pick__warning` — red warning/caveat box.
- `.pc` — pros/cons grid.
- `.pc__col`, `.pc__col--pro`, `.pc__col--con` — pros/cons columns.
- `.refer` — compact criterion cross-reference link; use with `data-deep-dive`.
- `.pick__runner`, `.pick__runner-label` — runner-up inset.
- `.pick__divider` — optional separator between pick cards.

Stable IDs: `#pick-best`, `#pick-budget`, `#pick-premium`.

## All products

- `.allp__intro` — lead-in copy.
- `.allp__legend`, `.sw`, `.sw--p|c|a` — optional card status legend.
- `.allp` — horizontal scroll-snap product list.
- `.allp__track` — card track.
- `.allp__card`, `.allp__card--pick|consider|avoid` — product card and role accent.
- `.allp__rank`, `.allp__meta`, `.allp__note`, `.allp__link` — card content.
- `.allp__hint` — scroll cue.

Do not hardcode carousel controls in article HTML. The bundled navigation script adds controls at runtime when the carousel overflows.

## Tradeoffs

- `.tradeoffs` — stack wrapper.
- `.trade` — one tier-transition card.
- `.trade__head`, `.tier-tag`, `.arrow`, `.delta` — transition header.
- `.trade__cols`, `.trade__col`, `.trade__col--gain`, `.trade__col--lose`, `.label` — gain/loss columns.
- `.bottom-line`, `.bottom-line__label` — final recommendation callout.

## Ruled out

- `.ruled` — stack wrapper.
- `.ruled-item` — one discarded candidate.
- `.ruled-item__tag`, `.ruled-item__tag--red|amber` — rejection severity.

## Evidence drawers

- `.drawers` — drawer stack. Includes all evidence drawers plus the interview Q&A as the last drawer.
- `.drawer` — evidence `<details>`.
- `.drawer__icon` — letter icon (A, B, C…). Not numbers.
- Summary layout: `<span class="drawer__icon">` + `<div>` wrapper containing `<div class="drawer__title">` and `<div class="drawer__sub">` + optional trailing `<span class="drawer__sub">` for a right-aligned count hint.
- `.drawer__body` — expanded content.
- `.source-link` — small source attribution line.
- Tables and blockquotes inside `.drawer__body` are styled for evidence.

## Product imagery

The configured image mode may hotlink remote images, store validated local copies, or use placeholders. Hotlinked images carry `loading="lazy"` and `referrerpolicy="no-referrer"`; local images still use lazy loading. Containers use `--paper` backgrounds and contained images use `mix-blend-mode: multiply`, so the starter design expects white or light backgrounds unless its CSS is adapted. See `references/image-sourcing.md` for the full recipe and tradeoffs.

- `.hero__media` — borderless hero image; the product dissolves into the paper (`object-fit: contain` + `mix-blend-mode: multiply`, no box/border). Holds the best pick's photo. Sits between the `.eyebrow` caption and the `<h1 class="headline">`. Assumes a white/light source image like the other shots.
- `.tldr__thumb` — TL;DR row thumbnail, top-aligned, borderless, first child of `.tldr__row`. The grid is `[thumb] [main] [price]`; the tier chip lives **inside** `.tldr__main` above `.tldr__name`.
- `.pick__media` — pick banner (`aspect-ratio: 16/9` on the img for Safari). Goes after `.pick__specs`, before `.pick__verdict`.
- `.pick__runner-media` — runner-up thumbnail; floats left as the first child of `.pick__runner`.
- `.allp__media` — carousel card banner, first child of `.allp__card`. Reuse a pick/runner image when the product matches.
- `.allp__media--placeholder` — hatched "No image" block for cards with no sourced image: `<div class="allp__media allp__media--placeholder"><span>No image</span></div>`.
- `.matrix__img` — small product shot atop each `.matrix__head` column (first child of the column `<div>`, before the tier span). Reuse the pick images.

Note for Safari: aspect-ratio boxes put the ratio + `object-fit` **on the `<img>`**, never on a wrapper with a `height: 100%` child.

## Video embeds

- `.video-embed` — wrapper.
- `.video-embed__annotation` — why this video matters.
- `.video-embed__thumb[data-video-id]` — lazy thumbnail target.
- `.video-embed__play` — play overlay.
- `.video-embed iframe` — injected iframe after click.

## Research directory

- `.directory`, `.directory__subtitle`, `.directory__grid` — optional directory shell.
- `.research-card`, `.research-card__emoji`, `.research-card__info`, `.research-card__title`, `.research-card__summary`, `.research-card__date` — manifest-rendered card.

The bundled navigation expects the default manifest schema documented in `references/setup.md`. Adapt the navigation asset before using another schema.
