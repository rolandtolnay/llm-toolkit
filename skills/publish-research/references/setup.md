# Publish Research setup

`publish-research` needs a site profile because output paths, domains, asset URLs, audience names, image policy, and deployment commands belong to the target project. None of those values are baked into the skill.

## 1. Create the site profile

Copy `site-config.example.json` to `.publish-research.json` in the target site's project root, then review every value.

```bash
cp <installed-skill>/references/site-config.example.json .publish-research.json
```

The profile is normally safe to commit because it should not contain credentials. Keep secrets in the deployment provider's normal secret store or authenticated CLI session.

### Required paths

- `researchDirectory`: Parent directory containing Product Research Skill runs. `~` is allowed here.
- `outputDirectory`: Static site root, relative to the project root.
- `manifestPath`: JSON manifest used by the bundled navigation script, relative to the project root.
- `manifestFormat`: Must be `array` for the bundled workflow and navigation script.
- `site.stylesheetPath`: Filesystem destination for the shared stylesheet.
- `site.stylesheetHref`: URL used by generated pages to load that stylesheet.
- `site.navigationScriptPath`: Filesystem destination for the shared navigation script.
- `site.navigationScriptSrc`: URL used by generated pages to load that script.
- `site.articleScriptPath`: Filesystem destination for article behavior without inline JavaScript.
- `site.articleScriptSrc`: URL used by generated pages to load that script.
- `site.manifestUrl`: Browser URL from which the navigation script reads the manifest.
- `site.homeUrl`: Sidebar title link. Use `/` for a root deployment or the site's root-relative subpath home.
- `site.articleUrlPrefix`: Root-relative URL prefix for manifest article entries, such as `/` or `/research/`. Start and end it with `/`.

Output, manifest, asset, reference, mockup, and deployment paths must stay inside the project root. `researchDirectory` is the only configured path allowed outside because it points at source material.

### Site identity

Customize:

- `site.baseUrl`: Public origin, such as `https://research.example.com`. It may remain `null` for local-only use. When set, the publisher uses it to generate a canonical link and verify the public article URL.
- `site.title` and `site.subtitle`: Sidebar identity.
- `site.language`: HTML language code.
- `site.locale`: Date formatting locale for navigation.
- `site.faviconUrl`: Existing favicon URL. Set it to `null` when the site has none; the generator should remove the favicon tag.

### Audience and footer

- `audience.readerName`: Optional intended reader. Keep `null` for neutral second-person copy.
- `audience.intervieweeName`: Name used to attribute interview answers. Keep `null` to preserve source attribution or use a neutral label.
- `audience.voice`: Concrete editorial guidance for the humanization pass.
- `footer.affiliateDisclosure`: Your actual disclosure. It defaults to `null`; do not claim there are no affiliate links if the site uses them.
- `footer.signoff`: Optional closing line. It defaults to `null`; keep it generic unless the site has a named audience.

### Images

Choose one `images.mode`. The example profile defaults to `placeholder` so the first local preview does not depend on third-party images.

- `hotlink`: Link validated retailer or manufacturer images directly. Fast, but remote URLs can expire or block hotlinks.
- `local`: Download validated images into `<outputDirectory>/<slug>/images/`. More durable, but check licensing and repository size.
- `placeholder`: Publish without external product photos.

`images.requireLightBackground` matches the bundled stylesheet's multiply-blend treatment. Set it to `false` only after adapting the CSS and checking the result in a browser.

### Reference pages

- `referencePage`: Optional project-relative path to a page already validated against this template. It may guide cross-page consistency.
- `mockupPath`: Optional project-relative design mockup. It is secondary to the bundled template unless the user explicitly decides otherwise.

Do not point either field at a private checkout path that will not exist for other users.

## 2. Install shared assets

The skill bundles starter assets:

- `assets/styles.css`
- `assets/nav.js`
- `assets/article.js`

Copy them to `site.stylesheetPath`, `site.navigationScriptPath`, and `site.articleScriptPath` when the target site does not already have equivalents. Do not overwrite an existing design system or scripts without reviewing the diff.

The navigation script reads site identity from `data-*` attributes generated on each article's `<body>` and reads entries from `site.manifestUrl`. The article script handles chip state, video activation, criterion links, and print drawer expansion without inline JavaScript.

The page template loads Google Fonts from `fonts.googleapis.com` and `fonts.gstatic.com`. A strict Content Security Policy must allow those origins, or the site must self-host the fonts and update the template before publishing. YouTube evidence also needs the relevant image and frame origins, while hotlink mode needs each chosen product-image origin.

The manifest is a JSON array of objects with this default shape:

```json
[
  {
    "title": "Example product",
    "url": "/example-product/",
    "date": "2026-06-04",
    "emoji": "📦",
    "summary": "One source-grounded sentence."
  }
]
```

The bundled workflow accepts only this array schema. If the site uses another schema, stop and create a documented custom adapter or fork before publishing; otherwise the sidebar would fail silently.

## 3. Configure deployment only when wanted

Local generation and preview do not need a deployment command. Leave this disabled by default:

```json
{
  "deployment": {
    "command": null,
    "workingDirectory": ".",
    "publishPaths": ["public"],
    "publicUrl": null
  }
}
```

For Firebase Hosting, a profile might use:

```json
{
  "deployment": {
    "command": "npx --no-install firebase deploy --only hosting --project YOUR_FIREBASE_PROJECT_ID",
    "workingDirectory": ".",
    "publishPaths": ["public"],
    "publicUrl": "https://research.example.com"
  }
}
```

Replace both placeholders. Install an exact reviewed `firebase-tools` version in the project and commit its lockfile; `npx --no-install` then refuses to fetch a different version at deploy time. The Firebase CLI must already be authenticated, and `firebase.json` must point at the configured output directory.

`deployment.workingDirectory` and every `deployment.publishPaths` entry must stay inside the project and cover the generated article, manifest, and intended shared assets. The skill shows them before asking for confirmation. Other static hosts can use their own checked-in deployment command. Keep it deterministic, non-interactive, and limited to the declared publish scope. The skill shows the exact command and asks before running it because deployment is an external write.

Never store access tokens, service-account JSON, passwords, or private keys in `.publish-research.json`.

## 4. Optional tools

- A fresh-context subagent or reviewer is needed for the documented content and structure checks.
- `agent-browser` is recommended for desktop and mobile verification.
- `curl` and `file` support remote image validation.
- Python 3 can serve the static output locally with `python3 -m http.server`.
- A provider CLI is needed only when `deployment.command` uses it.
- The `humanizer` skill improves the editorial pass when installed, but the publishing skill includes the same preserve-facts boundary.

## 5. Verify customization after installation

Before the first article, check:

- `.publish-research.json` contains no example domain or placeholder deployment project when deployment is enabled.
- Every configured project path exists or has an approved initialization plan.
- The generated template loads the configured stylesheet, navigation script, article script, manifest URL, favicon, canonical URL when configured, language, title, and subtitle.
- The audience name, interview attribution, affiliate disclosure, and sign-off are correct for this site.
- The selected image mode matches your licensing and reliability requirements.
- The deployment command targets the intended provider, project, and public URL.
- Local generation works without deployment.

Run the skill with an explicit research folder for the first test:

```text
/publish-research ~/Documents/Research/YYYY-MM-DD-example-product-research
```

Stop after local preview on that first run unless you have separately reviewed and approved deployment.
