# One-off hobby project playbook

A reusable setup and delivery guide for quickly spinning up small, real, end-to-end apps that an LLM can build, deploy, and test from the CLI.

This playbook is distilled from the `stork-basket` project: Next.js frontend, Firebase backend, Vercel deployment, CLI-driven verification, and real-device/browser testing through `agent-browser`.

## Target stack

Use this default stack unless the project has a strong reason not to:

- **Frontend:** Next.js App Router + React + TypeScript.
- **Backend:** Firebase Auth + Firestore. Avoid extra backend infrastructure for one-off projects unless the feature truly needs it.
- **Persistence:** Firestore client SDK with offline persistence where useful.
- **Hosting:** Vercel.
- **Testing:** TypeScript, ESLint, Vitest, `next build`, and `agent-browser` smoke tests.
- **Device access:** deploy early to a Vercel preview/prod URL so the app can be opened immediately on the requested target devices: mobile, tablet, desktop, or a mix.
- **Design system:** use the requested kit from `/Users/rolandtolnay/Documents/Development/design-systems` as the UI source of truth.
- **Secrets/config:** browser Firebase config goes in `NEXT_PUBLIC_FIREBASE_*`; local `.env*` files stay ignored.

Keep the first slice boring: one app, one Firebase project, one Vercel project, one deployable path. Do not overindex on mobile, tablet, or desktop unless the user asks for that target.

## LLM operating instructions

When handing this to an LLM for a fresh project, tell it:

1. Treat the project as a one-shot `/goal` run: build, verify, judge, fix, deploy, and report in one loop.
2. Build the smallest useful vertical slice first.
3. Confirm the target surface: mobile, tablet, desktop, or responsive.
4. Set up Firebase Auth + Firestore and a GitHub-connected Vercel production path before expanding scope.
5. Use real auth in tests; do not add production auth bypasses.
6. Run CLI checks, browser smoke tests, and a fresh judge pass before calling the project done.
7. Commit only the intended files, then ship production by pushing `main` once the exact committed state is ready.

## Recommended agent skills

Use these skills when available:

- `vercel-react-best-practices` — React/Next performance and bundle-size guidance.
- `vercel-composition-patterns` — reusable component API design when components start getting boolean-prop-heavy.
- `agent-browser` — live UI testing, auth flows, screenshots, and target-device viewport checks.
- `deploy-to-vercel` — Vercel linking/deploy workflow.
- `improve-codebase-architecture` — keep modules deep, interfaces small, and tests focused on seams.
- `grill-with-docs` — sharpen domain terms and record durable decisions while planning.
- `humanizer` — write user-facing copy in the audience's language, not implementation jargon.
- `diagnose` — for hard bugs, failing deploys, or regressions.

Next.js best-practices are intentionally not in this list. They are no longer a standalone skill; the guidance now ships with the framework as version-matched agent docs. See the "Next.js agent guidance" step under Project bootstrap.

## Project bootstrap

```bash
npx create-next-app@latest my-project --ts --eslint --app
cd my-project
npm install firebase
npm install -D vitest
```

Add standard scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint .",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  }
}
```

### Next.js agent guidance

Next.js best-practices used to be a separate `next-best-practices` skill. That knowledge now ships with the framework, version-matched, so it never drifts:

- On Next.js 16.3+, `next dev` auto-generates `AGENTS.md` / `CLAUDE.md` agent rules in the project. Let it, and keep those generated files committed or ignored per your convention.
- On older versions, pull the version-matched bundled docs in manually:

```bash
npx @next/codemod@canary agents-md
```

This writes the docs to `.next-docs/` and points your `AGENTS.md` at them. See https://nextjs.org/docs/app/guides/ai-agents for full setup.

For Next.js workflow skills (cache-component adoption/optimization, dev loop), install them from the framework repo rather than copying them around:

```bash
npx skills add vercel/next.js
```

Create the minimal docs/contracts early:

- `CONTEXT.md` — glossary and domain terms only. No implementation details.
- `docs/decisions.md` — lightweight notes for non-obvious choices that are useful but not ADR-worthy.
- `docs/adr/` — create lazily for decisions that are hard to reverse, surprising without context, and the result of a real trade-off.
- `docs/external-setup.md` — Firebase/Vercel/GitHub project IDs, CLI state, deploy URLs, evaluator account location.
- `.env.example` — public env var names with no secrets.

## Firebase setup

Use Firebase for Auth and Firestore first. Add Cloud Functions only after a real need appears.

Typical setup:

```bash
firebase login
firebase projects:create <project-id>
firebase apps:create WEB <app-name> --project <project-id>
firebase apps:sdkconfig WEB <firebase-web-app-id> --project <project-id>
firebase init firestore
```

Enable in the Firebase console or CLI as needed:

- Firestore database, preferably in a nearby region.
- Firebase Auth provider, usually Email/Password for small private apps.
- A dedicated evaluator/test user for browser automation.

Commit Firebase project metadata and rules:

- `.firebaserc`
- `firebase.json`
- `firestore.rules`
- `firestore.indexes.json`

Do not commit:

- `.env.local`
- `.local/*`
- service-account JSON files
- evaluator credentials

Recommended `.env.example` shape:

```dotenv
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=
```

Browser Firebase config values are public app config, but keep local `.env*` ignored anyway to avoid accidental mixing with secrets.

### Firebase client pattern

Create one small Firebase client module that:

- Reads and validates `NEXT_PUBLIC_FIREBASE_*`.
- Initializes the app once.
- Exposes Auth and Firestore through a narrow interface.
- Enables local/offline persistence if the app benefits from it.

Keep Firestore as an adapter behind app/domain interfaces. UI should not scatter raw Firestore paths everywhere.

## Data, architecture, and supporting docs

Use the `improve-codebase-architecture` vocabulary when shaping the code:

- A **Module** has an interface and an implementation.
- A **Seam** is where an interface lives.
- An **Adapter** is a concrete implementation behind a seam.
- The interface is the test surface.
- Use the deletion test: if deleting a module makes complexity disappear, it was probably pass-through; if complexity would spread across callers, the module is earning its keep.

For fast projects, still keep these seams:

- Pure domain logic in `lib/domain/*`, tested with Vitest.
- Data module interfaces in `lib/<feature>/*`.
- Firestore adapter behind those interfaces.
- React components consume feature/domain interfaces, not raw database details.

Keep modules deep enough to buy locality: a small interface should hide meaningful behavior. Avoid extracting shallow pass-through files just to look organized.

Use `grill-with-docs` discipline while planning:

- Read `CONTEXT.md` before naming concepts.
- If a user term is vague or overloaded, resolve it and update `CONTEXT.md` immediately.
- Keep `CONTEXT.md` as a glossary only, not a spec.
- Add ADRs sparingly: only for decisions that are hard to reverse, surprising without context, and trade-off driven.
- If a judge or reviewer suggests wording that conflicts with canonical domain language, either reject it or update the glossary deliberately.

This keeps the LLM effective: logic is testable without a browser or cloud, and UI changes do not require rewriting persistence.

## Design system and user-facing copy

Always build UI from the design systems under:

```text
/Users/rolandtolnay/Documents/Development/design-systems
```

Start by reading the design-system index files, then the requested kit:

```bash
ls /Users/rolandtolnay/Documents/Development/design-systems
cat /Users/rolandtolnay/Documents/Development/design-systems/CANONICAL.md
cat /Users/rolandtolnay/Documents/Development/design-systems/README.md
```

Available kits may include `warm-press-kit`, `calm-paper-kit`, `dark-workspace-kit`, `sunny-playfield-kit`, and `violet-arcade-kit`. Use whichever kit the user names. If they do not name one, ask or pick the closest match and state the choice.

Copy rule:

- Use `CONTEXT.md` terms for implementation and internal reasoning.
- Use the `humanizer` skill for user-facing copy.
- User-facing text should fit the target audience, device, and emotional context. It should not expose internal terms just because they are canonical in the glossary.
- Avoid AI-sounding copy: generic praise, filler, vague benefit language, title-case overuse, emoji decoration, and mechanical bold-label lists.

## GitHub and Vercel deployment

Use the `deploy-to-vercel` skill when available. The preferred production setup is **GitHub-connected Vercel**: the project has a private GitHub repository, Vercel is connected to that repository, and every push to `main` automatically builds and deploys production.

Initial state checks:

```bash
git status --short
git remote get-url origin 2>/dev/null
gh auth status 2>/dev/null
cat .vercel/project.json 2>/dev/null || cat .vercel/repo.json 2>/dev/null
vercel whoami 2>/dev/null
vercel teams list --format json 2>/dev/null
```

If no git repository exists yet:

```bash
git init
git branch -M main
git add .
git commit -m "Initial app"
```

If no GitHub remote exists yet, create a private repository and push `main`:

```bash
gh repo create <repo-name> --private --source=. --remote=origin --push
```

If `gh` is unavailable or unauthenticated, ask the user to create a private GitHub repo, then add it:

```bash
git remote add origin git@github.com:<owner>/<repo-name>.git
git push -u origin main
```

Preferred long-term state:

1. Private GitHub repo exists and local `main` tracks `origin/main`.
2. Vercel project is connected to that GitHub repo.
3. Pushes to non-production branches create preview deployments.
4. Pushes to `main` automatically create production deployments.
5. Agents deploy production by committing the intended files and pushing `main`, not by running manual production deploys.

If linking Vercel from the CLI and a git remote exists, prefer repo linking:

```bash
vercel link --repo --scope <team-slug>
```

Set Firebase env vars in Vercel for every target you will use:

- Production
- Preview
- Development, if needed

If the CLI prompts awkwardly for preview branch selection, use the Vercel dashboard to add preview env vars manually from the Firebase web app config.

For throwaway smoke testing before production is ready, create a preview deployment directly:

```bash
vercel deploy . -y --no-wait --scope <team-slug>
vercel inspect <deployment-url> --scope <team-slug>
```

For production, prefer the automatic GitHub flow. Run the Verification gate checks first, then:

```bash
git add <changed-files>
git commit -m "<summary>"
git push origin main
sleep 5
vercel ls <project-name> --format json --scope <team-slug>
```

Use `vercel inspect <deployment-url> --scope <team-slug>` to poll the production deployment until it is ready, then smoke-test the production URL. Use manual `vercel deploy --prod` only as an explicit fallback when GitHub integration is unavailable or broken, and deploy from a clean committed tree rather than a dirty working directory.

## Verification gate

Before reporting done, run the checks the change touches. For most fresh projects, use all of these:

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

Notes:

- Add Vitest tests for changed domain logic.
- `next build` catches production-only Next/React issues that unit tests miss.
- If `next/font` fetches Google Fonts, `npm run build` may need network access.
- Report only checks actually run. Include exact failures if any.

## `/goal` judged loop

These hobby projects are built as one-shot `/goal` runs in Codex or Claude Code. The full workflow — rubric shape, judge subagent prompt, builder rules, and the deploy rule — lives in `judged-goal-loop.md` next to this playbook. Use that file as the single source for the loop; do not re-derive it here.

The only things to remember at the playbook level:

- Turn the user's outcome into a short rubric with falsifiable checks, then build the simplest version that satisfies it.
- Have a fresh judge subagent drive the real running app (not the diff) via `agent-browser` with real auth.
- Stop only when the judge returns `GOAL MET`. Cap at two or three passes; if blockers keep changing, the goal is underspecified — sharpen the rubric instead of spinning.

## Browser and device testing with agent-browser

Use `agent-browser` for real UI smoke tests instead of guessing from code.

Start with the installed-version guide:

```bash
agent-browser skills get core
```

Choose the viewport from the user's target, not from this playbook:

- Mobile portrait: around `402 874`.
- Tablet: use a representative tablet viewport such as `820 1180` or the user's device size.
- Desktop: use a representative desktop viewport such as `1440 900`.
- Responsive apps: test at least the primary target plus one adjacent size.

Typical local smoke flow:

```bash
npm run dev
agent-browser open http://localhost:3000
agent-browser set viewport <width> <height>
agent-browser snapshot -i
```

Useful checks:

```bash
agent-browser eval "({ innerWidth: window.innerWidth, scrollWidth: document.documentElement.scrollWidth, hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth })"
agent-browser screenshot /tmp/my-project-smoke.png
```

For authenticated apps:

- Create a real Firebase Auth evaluator account.
- Store credentials in `.local/evaluator-credentials.md` and ignore it.
- Sign in through the normal auth form.
- Do not print credentials in logs.
- Do not build a production auth bypass.

Example credential-safe shell pattern:

```bash
EMAIL=$(awk -F': ' '/^Email:/ {print $2}' .local/evaluator-credentials.md)
PASS=$(awk -F': ' '/^Password:/ {print $2}' .local/evaluator-credentials.md)
agent-browser fill @email "$EMAIL"
agent-browser fill @password "$PASS"
agent-browser click @signIn
```

If a smoke test creates data, clean it up through the app or a documented admin/test helper before finishing.

For live-device testing, deploy to Vercel early and open the Vercel URL on the physical device. Then also run an `agent-browser` smoke pass against the same URL.

## Target-platform defaults

Optimize for the platform the user requests:

- **Mobile:** portrait-first, large tap targets, thumb-reachable primary actions, no horizontal overflow at the chosen phone viewport.
- **Tablet:** make use of extra width without turning the app into a cramped desktop layout; check both portrait and landscape when relevant.
- **Desktop:** keyboard and pointer interactions should feel natural; use space for density and comparison, not just stretched mobile cards.
- **Responsive:** define the primary target, then verify one smaller and one larger breakpoint.

For all targets:

- Prefer installable PWA basics when the app benefits from device access: `manifest.webmanifest`, app icons, theme color, and appropriate metadata.
- Keep the primary flow short and obvious.
- Avoid platform-specific assumptions unless the user asked for that platform.

## Styling defaults

Use the selected design system as the styling source of truth. Port only the tokens and components the first slice needs:

- Colors
- Radii
- Spacing
- Shadows
- Typography scale
- Component states and interaction patterns

Avoid scattering literal colors and radii through components. It slows later redesigns and makes LLM edits less consistent. If the project needs local tokens, create one token file and map it back to the selected design system.

## Security and operational rules

- Treat Firebase service account keys as local-only. Store under `.local/` and ignore them.
- Use Admin SDK only in local/admin CLIs, not browser code.
- Keep Firestore rules committed and verify deploys/dry-runs.
- Do not bypass auth in production for testing convenience.
- Treat pushes to `main` as production deployments; push `main` only when the exact committed state is intended to ship.
- Ask before changing Vercel security/project settings.
- If a cloud command fails unexpectedly, stop and report the exact command/error instead of recreating resources blindly.

## Done checklist for a fresh project

A one-off project is ready for real use when:

- [ ] Project was run as a one-shot `/goal` loop with a rubric and fresh judge pass.
- [ ] Target platform is documented: mobile, tablet, desktop, or responsive.
- [ ] Selected design system from `/Users/rolandtolnay/Documents/Development/design-systems` is documented.
- [ ] `CONTEXT.md` and `docs/decisions.md` exist.
- [ ] Firebase project, web app, Auth provider, and Firestore database exist.
- [ ] `.env.example` documents required `NEXT_PUBLIC_FIREBASE_*` vars.
- [ ] Local `.env.local` works and is ignored.
- [ ] Firestore rules and indexes are committed.
- [ ] Private GitHub repo exists and `main` tracks `origin/main`.
- [ ] Vercel project is connected to the GitHub repo.
- [ ] Pushes to `main` automatically deploy production.
- [ ] App has at least one real end-to-end user flow.
- [ ] Verification gate passes (`typecheck`, `lint`, `test`, `build`).
- [ ] Vercel production deployment from `main` is live.
- [ ] Fresh judge subagent returned `GOAL MET`.
- [ ] `agent-browser` smoke test passes at the target viewport/device class.
- [ ] Authenticated flow is tested with a real evaluator account, if auth exists.
- [ ] Live URL is opened or ready to open on the target devices.

To kick off a new project, use the copy-paste `/goal` template in `judged-goal-loop.md` rather than a separate prompt that restates this playbook.
