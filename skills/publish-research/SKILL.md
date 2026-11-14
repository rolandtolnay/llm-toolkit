---
name: publish-research
description: Turn a completed Product Research Skill run into a readable static HTML article, verify it against the source, update a site manifest, and optionally deploy it. Use when explicitly asked to publish product research to a configured website.
disable-model-invocation: true
argument-hint: "[research folder or topic]"
---

# Publish research

Turn one completed Product Research Skill run into a source-grounded static article. Build and verify the page locally first. Deployment is optional and always requires the user to confirm the exact command and destination.

The target site is configured in `.publish-research.json` at the project root. Do not assume a project name, domain, audience, output path, deployment provider, or personal sign-off.

## Before publishing

1. Read `.publish-research.json` and `references/setup.md`.
2. If the config is missing, offer to create it from `references/site-config.example.json`. Ask only for values that cannot be inferred from the target repository. Do not publish or deploy until the user has reviewed the profile.
3. Resolve `researchDirectory` separately. It may be absolute or use `~`; verify that it exists before reading it. Resolve output, manifest, asset, deployment working-directory, deployment publish, reference-page, and mockup paths from the project root and reject any that escape the project.
4. Check the configured output directory, array manifest, stylesheet, navigation script, article script, optional reference page, and optional mockup.
5. If shared assets are missing, offer to copy `assets/styles.css`, `assets/nav.js`, and `assets/article.js` to the configured locations. Never overwrite existing assets without showing the conflict and getting approval.
6. Check available tools:
   - a fresh-context reviewer or subagent mechanism for the content review
   - `python3` for the bundled structure check (`scripts/check-page.py`)
   - `agent-browser` for rendered verification when available
   - `curl` and `file` when product images will be sourced
   - the configured deployment CLI only if deployment is enabled

If the site profile cannot support the bundled template, explain the mismatch and stop instead of guessing at a different site architecture.

## Source and output

Treat the argument as a research folder path or topic. Without an argument, inspect the configured `researchDirectory` and use the latest Product Research Skill run only when the match is unambiguous.

A valid source folder contains `00-synthesis.md` and normally follows this layout:

```text
YYYY-MM-DD-<category>-product-research/
├── 00-synthesis.md
├── 01-interview.md
├── 02-masterclass.md
├── 03-availability.md
├── 04-owner-voice.md
├── 05-expert-voice.md
├── 06-retailer-voice.md
├── 07-finalist-sweep.md
└── aspects/
```

Runs made with an earlier version of the Product Research Skill have no `07-finalist-sweep.md` and no "All candidates" table in the synthesis. Publish them from the files they have.

Derive the page slug from the folder name by removing the date prefix and `-product-research` suffix. Write the article to `<outputDirectory>/<slug>/index.html` unless the site profile says otherwise.

## Content rules

- `00-synthesis.md` owns the recommendations, criteria, tradeoffs, and ruled-out rationale. Its claims, numbers, hedges, and conclusions carry over unchanged. The prose is rewritten for the reader and humanized before it reaches the HTML, so the factual review sees the final text.
- Read every available research file. Angle files provide evidence, tables, source links, owner quotes, video IDs, availability, and product inventory.
- Keep every product that the research treated as a candidate discoverable in `#all-products`. The inventory is the synthesis's "All candidates" table. When the run has no such table, build it from the angle files: deduplicate obvious repeats and retain materially different configurations when they matter.
- Place product names, model numbers, prices, specs, certifications, retailer names, URLs, quotations, citations, table values, and interview answers from the sources unchanged. State stock and price caveats in plain words, not as raw status tags.
- Do not invent missing specifications, image URLs, stock, prices, or source claims. Use `Unknown`, `Not verified`, a placeholder, or omit the unsupported field.
- Escape source and config text for its HTML context. Internal links must be root-relative without a `//` prefix. External links must use `http` or `https`; reject protocol-relative URLs, localhost and private-network destinations, non-HTTP redirects, raw scripts, event handlers, and `javascript:` URLs.
- Apply the configured audience name, interview attribution, voice, affiliate disclosure, and footer sign-off. When those values are null, use neutral second-person copy and source-grounded attribution. Never insert private names from examples or prior sites.

Read `references/section-mapping.md` before composing the page.

## Template and structural authority

Read `references/page-template.html` and `references/design-system.md`.

The bundled page template is the structural authority. `scripts/check-page.py` reads the expected element for every class from it. The configured `referencePage`, when it exists, guides editorial consistency only: title style and footer wording. The optional `mockupPath` settles component details the template does not show.

No external or previously published page is an implicit authority. The generated page must use the configured stylesheet, navigation script, and article script and must not contain embedded CSS, inline scripts, or inline `style` attributes.

Required anchors:

- `#picks`
- `#criteria`
- `#compare`
- `#all-products`
- `#tradeoffs`
- `#ruled-out`
- `#evidence`
- applicable `#pick-best`, `#pick-budget`, and `#pick-premium`

Required component classes:

- `.chip-nav`
- `.tldr`
- `.criteria-stack` and `.crit`
- `.matrix`
- `.pick`
- `.allp`
- `.trade`
- `.ruled-item`
- `.drawers` and `.drawer`

The interview Q&A belongs in the final evidence drawer, not a separate section.

## Write and humanize the reader copy

Write the page's prose as markdown in a temporary folder outside the site, one heading per page slot, so each block can be placed later.

The copy covers the lede and context line, section decks, criterion summaries and bodies, myths, pick verdicts, pros and cons, runner-up reasons, price and stock notes, all-products notes, tradeoff gains and losses, the bottom line, ruled-out explanations, and the drawer titles and connecting prose. Names, prices, spec lines, matrix cells, tables, quotes, interview answers, button labels, and links stay out of it; they are placed from the sources unchanged.

Start from the synthesis text and address the configured reader in the configured voice. With no reader configured, use neutral second person. Lead each block with the verdict or the point, say what a spec means in daily use next to the number, and keep every hedge as hedged and every certainty as certain.

Then humanize the copy before it reaches the HTML. Use the `humanizer` skill when it is installed, or another isolated editor that preserves facts. Tell it that the headings are slot labels to keep as written and that each block should stay close to its draft length. Without such a tool, edit the copy directly inside the same boundary. Afterwards compare the result with the draft: headings, links, and numbers should be the same, and any difference gets a targeted fix.

## Build the page

1. Fill every template placeholder except image markers with the humanized copy and the source-placed facts. Remove unused representative components and duplicate repeatable components as needed. Keep the fixed labels the template carries.
2. Build one TL;DR row and one matching pick article per recommendation tier.
3. Build the criteria cards from the synthesis and masterclass, preserving source links and deep evidence.
4. Build a comparison matrix only from facts present in the research. Use `.matrix--1`, `.matrix--2`, or `.matrix--3` for the actual recommendation count and generate exactly one header and row cell per recommendation.
5. Build the full product inventory, tier tradeoffs, ruled-out items, and evidence drawers.
6. Add the configured site title, subtitle, language, locale, manifest URL, home URL, canonical URL when available, asset URLs, audience labels, and footer text. Remove optional favicon, disclosure, and sign-off elements when their config values are null; never render the word `null`.
7. Leave the documented image placeholders for the image pass.

## Verify content with fresh context

Use a fresh reviewer to compare the draft with the research files. The reviewer must check:

1. Every synthesis section is represented.
2. Product names, model numbers, prices, capacities, specs, retailers, links, and stock notes match.
3. Every tier has a TL;DR row and matching pick article.
4. Every surfaced candidate appears once in `#all-products`, unless separate variants are intentional.
5. Criteria and evidence preserve the strongest links, quotes, tables, and videos.
6. Tradeoffs and ruled-out explanations are source-grounded.
7. The interview remains the last evidence drawer and preserves the original answers.
8. Unsupported claims were not added.
9. Meaning did not shift in the rewrite: no hedge dropped, no caveat softened, no certainty added.

The reviewer reports gaps. Decide which are real, and fix those before continuing.

## Review structure and rendering

**Structure.** Run the bundled check from this skill's directory and fix everything it lists:

```sh
python3 scripts/check-page.py <outputDirectory>/<slug>/index.html --styles <site.stylesheetPath> --pre-images
```

It compares the page with the template: element types, unknown classes, anchors and cross-references, pick IDs, nesting, inline styles and scripts, image attributes, and unfilled placeholders. Drop `--pre-images` once the image pass is done.

**Rendering.** Serve the configured site root locally and inspect desktop and 375px mobile layouts. Check chip navigation, TL;DR wrapping, comparison columns, drawers, images, carousel behavior, and print expansion. If browser automation is unavailable, report the exact manual browser pass still needed.

## Add images

Read `references/image-sourcing.md` and follow the configured `images.mode`:

- `hotlink`: validate and reference remote product images.
- `local`: download validated images into the article directory and use relative URLs.
- `placeholder`: remove optional hero imagery and use placeholders for product cards.

The image pass changes image markup only. Have it report any buy link that is dead or lands on a different product than the page names, and fix those from the run's other sellers.

Rerun the structure check without `--pre-images`, then repeat the desktop and mobile rendering check.

## Manifest and local verification

The bundled workflow supports `manifestFormat: "array"`. Stop with a config error when the profile requests another format or the existing manifest is not a JSON array; do not silently preserve a schema the bundled navigation cannot read. Create an empty array only when the manifest is missing and the user approves initialization. Add or update one entry:

```json
{
  "title": "<product category>",
  "url": "<articleUrlPrefix><slug>/",
  "date": "<YYYY-MM-DD from synthesis>",
  "emoji": "<relevant emoji>",
  "summary": "<one source-grounded sentence>"
}
```

Preserve the existing schema and ordering convention when a manifest already exists.

Before any deployment:

- confirm no unresolved `{{PLACEHOLDER}}` remains
- validate HTML nesting as far as available tooling permits
- confirm the stylesheet, navigation script, article script, manifest, links, and image paths resolve locally
- render the page at desktop and mobile sizes when browser tooling is available
- report any skipped or manual checks

Do not commit unless the user asks.

## Optional deployment

Deployment is disabled when `deployment.command` is null or empty. In that case, finish with the local output path and the next manual publishing step.

When a command is configured:

1. Resolve `deployment.workingDirectory` and every `deployment.publishPaths` entry inside the project. Confirm the generated article, manifest, and intended shared assets are inside those publish paths. Show the exact command, working directory, publish paths, and configured public URL.
2. Explain that this is an external write. Inspect the configured entrypoint when it resolves through a package script. Reject commands that fetch an unpinned `@latest` package, chain unrelated shell actions, perform destructive cleanup, or mutate outside the declared publishing scope; deployment tooling must be checked in, lockfile-pinned, or exact-versioned.
3. Ask for confirmation.
4. Run the command once after approval.
5. Open or fetch the final page and verify the rendered URL. Prefer `deployment.publicUrl` when set; otherwise derive the article URL from `site.baseUrl` and `site.articleUrlPrefix`. If neither is available, report the provider output without inventing a URL.

Do not retry a failed deployment with changed flags, another project, or another provider without fresh confirmation.

## Success criteria

- The page is generated from one valid Product Research Skill run.
- All visible factual claims trace back to the source files.
- Every surfaced candidate appears in the product inventory.
- Required classes and anchors are present, with no embedded CSS, inline CSS, or inline scripts.
- Audience names, footer text, site paths, URLs, and deployment behavior come from config or source, never from the bundled examples.
- Product images follow the configured mode and are verified or replaced with honest placeholders.
- The structure check passes, and the content review has no unresolved gaps.
- Local desktop and mobile verification passed, or remaining manual checks are reported.
- The manifest is updated without changing its established schema.
- Deployment happened only when configured and explicitly confirmed.
