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
   - a fresh-context reviewer or subagent mechanism for content and structure review
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
└── aspects/
```

Derive the page slug from the folder name by removing the date prefix and `-product-research` suffix. Write the article to `<outputDirectory>/<slug>/index.html` unless the site profile says otherwise.

## Content rules

- `00-synthesis.md` owns the recommendation prose, criteria, tradeoffs, and ruled-out rationale. Use it verbatim in the first HTML draft, then humanize only the editorial copy after factual review.
- Read every available research file. Angle files provide evidence, tables, source links, owner quotes, video IDs, availability, and product inventory.
- Keep every product that the research treated as a candidate discoverable in `#all-products`. Deduplicate obvious repeats and retain materially different configurations when they matter.
- Preserve product names, model numbers, prices, specs, certifications, retailer names, URLs, verification statuses, quotations, citations, table values, and interview answers exactly.
- Do not invent missing specifications, image URLs, stock, prices, or source claims. Use `Unknown`, `Not verified`, a placeholder, or omit the unsupported field.
- Escape source and config text for its HTML context. Internal links must be root-relative without a `//` prefix. External links must use `http` or `https`; reject protocol-relative URLs, localhost and private-network destinations, non-HTTP redirects, raw scripts, event handlers, and `javascript:` URLs.
- Apply the configured audience name, interview attribution, voice, affiliate disclosure, and footer sign-off. When those values are null, use neutral second-person copy and source-grounded attribution. Never insert private names from examples or prior sites.

Read `references/section-mapping.md` before composing the page.

## Template and structural authority

Read `references/page-template.html` and `references/design-system.md`.

Use this precedence:

1. The configured `referencePage`, when it exists and has been validated for the same template version.
2. The bundled page template and design-system reference.
3. The optional configured `mockupPath`, only for component details it still represents.

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

## Build the first draft

1. Fill every template placeholder except image markers. Remove unused representative components and duplicate repeatable components as needed.
2. Build one TL;DR row and one matching pick article per recommendation tier.
3. Build the criteria cards from the synthesis and masterclass, preserving source links and deep evidence.
4. Build a comparison matrix only from facts present in the research. Use `.matrix--1`, `.matrix--2`, or `.matrix--3` for the actual recommendation count and generate exactly one header and row cell per recommendation.
5. Build the full product inventory, tier tradeoffs, ruled-out items, and evidence drawers.
6. Add the configured site title, subtitle, language, locale, manifest URL, home URL, canonical URL when available, asset URLs, audience labels, and footer text. Remove optional favicon, disclosure, and sign-off elements when their config values are null; never render the word `null`.
7. Leave the documented image placeholders for the image pass.

## Verify content with fresh context

Use a fresh reviewer to compare the draft with the research files. The reviewer must check:

1. Every synthesis section is represented.
2. Product names, model numbers, prices, capacities, specs, retailers, links, and verification statuses match.
3. Every tier has a TL;DR row and matching pick article.
4. Every surfaced candidate appears once in `#all-products`, unless separate variants are intentional.
5. Criteria and evidence preserve the strongest links, quotes, tables, and videos.
6. Tradeoffs and ruled-out explanations are source-grounded.
7. The interview remains the last evidence drawer and preserves the original answers.
8. Unsupported claims were not added.

Fix all confirmed gaps before continuing.

## Review structure and rendering

Use independent reviewers for these lenses when the host supports them:

- **Template structure:** element types, nesting, required classes, stable anchors, image slots, and no unresolved non-image placeholders.
- **Cross-page consistency:** compare only against the configured reference page, if any. Check title style, footer shape, evidence drawers, and valid HTML nesting.
- **Browser rendering:** serve the configured site root locally and inspect desktop and 375px mobile layouts. Check chip navigation, TL;DR wrapping, comparison columns, drawers, images, carousel behavior, and print expansion.

If browser automation is unavailable, run static checks and report the exact manual browser pass still needed.

## Humanize copy and add images

Run these as separate passes. They may run in parallel only when the workers edit disjoint parts of the page.

### Editorial pass

Rewrite the headline, lede, section decks, criteria explanations, myth copy, pick verdicts, pros and cons, tradeoff labels, bottom line, evidence titles, and footer in the configured voice.

Do not change factual fields, source material, interview answers, URLs, table cells, product names, prices, specs, certifications, verification blocks, or image markup. If the `humanizer` skill is installed, use it for this pass; otherwise follow the same preserve-facts boundary directly.

### Image pass

Read `references/image-sourcing.md` and follow the configured `images.mode`:

- `hotlink`: validate and reference remote product images.
- `local`: download validated images into the article directory and use relative URLs.
- `placeholder`: remove optional hero imagery and use placeholders for product cards.

The image pass may change image markup only. It must not edit article copy.

Review the combined page for factual drift and broken images, then repeat the desktop and mobile rendering check.

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
- Content and structural reviews have no unresolved gaps.
- Local desktop and mobile verification passed, or remaining manual checks are reported.
- The manifest is updated without changing its established schema.
- Deployment happened only when configured and explicitly confirmed.
