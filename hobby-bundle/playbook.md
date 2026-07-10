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
- **Design system:** use the requested kit from `~/Documents/Development/design-systems` as the UI source of truth.
- **Secrets/config:** browser Firebase config goes in `NEXT_PUBLIC_FIREBASE_*`; local `.env*` files stay ignored.

Keep the first slice boring: one app, one Firebase project, one Vercel project, one deployable path. Do not overindex on mobile, tablet, or desktop unless the user asks for that target.

## LLM operating instructions

This playbook is meant to run unattended inside a `/goal` loop: the user kicks it off, walks away, and returns to a finished, deployed app. Operate accordingly:

- **Never block on a question.** When something is unspecified, infer the most sensible default from the goal, state the choice, and record it in `docs/goal-log.md`. Only halt for missing credentials or genuinely irreversible actions (see Preflight and Security).
- **Persist your reasoning.** The persona, rubric, and per-pass judge verdicts must live in files, not just in context, so the user can reconstruct why the app is the way it is.

Then run the loop:

1. Treat the project as a one-shot `/goal` run: build, verify, judge, fix, deploy, and report in one loop.
2. Build the smallest useful vertical slice first.
3. Infer the target surface (mobile, tablet, desktop, or responsive) from the goal and state the choice.
4. Derive the judge persona from the goal description and persist it; this drives both the UI/UX and product-effectiveness judging lenses.
5. Create/link Firebase + Vercel early and detect whether production Firebase Auth is enabled; if it is not, keep building against emulators and save the real Auth check for the production gate.
6. Use real Firebase Auth or the Firebase Auth emulator in tests; do not add production auth bypasses.
7. Run CLI checks, browser smoke tests, and a fresh judge pass (a subagent if the harness supports it, otherwise a fresh-context review) before calling the project done.
8. Commit only the intended files, then ship production by pushing `main` once the exact committed state is ready.

### Subagent model economy

Keep the frontier model that owns the goal focused on product judgment, architecture, integration, and final synthesis. Delegate bounded work to the least costly lower-tier model that remains comfortably capable.

- Default one tier down for substantial but well-scoped implementation, analysis, or review; use two tiers down for routine research, repository exploration, fixture enumeration, mechanical edits, and targeted checks with objective acceptance criteria.
- Current examples, not permanent mappings: a Fable-owned goal can usually delegate to Opus 4.8, or to Sonnet 5 for narrow verifiable work; a Sol-owned goal can usually delegate to Terra, or to Luna for routine research and exploration.
- Keep ambiguous product decisions, cross-cutting architecture, destructive or external mutations, and work whose failure is hard to detect with the goal owner or a peer-capability model.
- Give each subagent a bounded deliverable and verification contract; have the goal owner review and integrate it. Escalate after an uncertain or failed pass instead of accumulating cheap retries.

Choose from the current model ladder at run time because aliases and relative capability change.

## Recommended agent skills

Use these skills when available:

- `vercel-react-best-practices` — React/Next performance and bundle-size guidance.
- `vercel-composition-patterns` — reusable component API design when components start getting boolean-prop-heavy.
- `agent-browser` — live UI testing, auth flows, screenshots, and target-device viewport checks.
- `web-design-guidelines` — audit UI for accessibility and interaction best practices; use it in the UI/UX judge pass.
- `deploy-to-vercel` — Vercel linking/deploy workflow.
- `improve-codebase-architecture` — keep modules deep, interfaces small, and tests focused on seams.
- `grill-with-docs` — sharpen domain terms and record durable decisions while planning.
- `humanizer` — write user-facing copy in the audience's language, not implementation jargon.
- `diagnose` — for hard bugs, failing deploys, or regressions.

Next.js best-practices are not a skill here; they ship with the framework as version-matched agent docs. See "Next.js agent guidance" under Project bootstrap.

## Preflight

Because the loop runs unattended, verify every external dependency is authenticated and reachable **before** building. Interactive logins (notably `firebase login`) cannot complete mid-run, so a missing session is a fatal, halt-and-report condition, not something to work around.

Check, and halt with a clear report if any required item is missing:

```bash
node -v && npm -v
firebase projects:list >/dev/null 2>&1 && echo "firebase: ok" || echo "firebase: NOT AUTHENTICATED"
gh auth status >/dev/null 2>&1 && echo "gh: ok" || echo "gh: NOT AUTHENTICATED"
vercel whoami >/dev/null 2>&1 && echo "vercel: ok" || echo "vercel: NOT AUTHENTICATED"
command -v agent-browser >/dev/null 2>&1 && echo "agent-browser: ok" || echo "agent-browser: MISSING"
ls ~/Documents/Development/design-systems >/dev/null 2>&1 && echo "design-systems: ok" || echo "design-systems: MISSING"
```

For fully non-interactive auth, expect these to be provided by the environment rather than prompted:

- Firebase: an active CLI session or `FIREBASE_TOKEN` / `GOOGLE_APPLICATION_CREDENTIALS`.
- Google Cloud: when enabling APIs or creating Firestore, `gcloud config get-value account` must be the same Google account that owns/can administer the Firebase project. A stale or different active account will produce 403/reauth friction even when `firebase` itself is logged in.
- Vercel: an active session or `VERCEL_TOKEN` (pass `--token` / `--scope` on commands).
- GitHub: an authenticated `gh` session or `GH_TOKEN`.

Record which auth mode is in use in `docs/external-setup.md`. Prefer `python3` or Node for local scripts; do not assume a `python` executable exists.

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

Pull Next.js best-practices from the framework's own version-matched agent docs instead of a separate skill:

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
- `docs/goal-log.md` — the durable record of the run: the goal, the derived persona, the rubric, each judge pass (verdict + blockers + what was fixed), and any inferred defaults you chose without the user. This is what lets the user return and understand why the app is the way it is.
- `.env.example` — public env var names with no secrets.

Create or append to additional memory files when the goal needs them; these are the minimum, not a ceiling.

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

### Firebase Auth enablement policy

For newly created hobby projects, expect the Firebase project to start on the free Spark plan. Do **not** block the whole build on Email/Password being enabled in production Auth.

Use this split gate instead:

1. **Detect early:** after the Firebase project and web app exist, attempt a real evaluator-account creation/sign-in or equivalent Auth config check.
2. **If production Auth is not initialized:** record the exact blocker in `docs/goal-log.md` and `docs/external-setup.md`, including the Firebase Console URL and the one manual step: Authentication → Sign-in method → Email/Password → Enable.
3. **Keep building:** wire the app to Firebase Auth/Firestore normally, but run local authenticated browser flows against the Firebase Emulator Suite using an explicit emulator flag. Do not add a production auth bypass.
4. **Production auth gate:** near the end, after build/lint/tests and deployment wiring are done, retry the evaluator-account script against real Firebase Auth. If it still returns `CONFIGURATION_NOT_FOUND`, stop with the precise manual instruction and resume command.
5. **Done gate:** the project is not done until the deployed production URL has been smoke-tested with a real Firebase Auth evaluator account.

Only use the fully automated Identity Platform path (`identityPlatform:initializeAuth` + `projects.updateConfig`) when the user explicitly authorizes billing-backed Identity Platform/API setup. For the default Spark-plan flow, the least-friction path is emulator-backed development plus a late, small production-auth handoff.

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

### Firestore security rules

The Firestore client SDK runs in the browser, so rules are the only thing standing between an authenticated user and everyone else's data. Never ship test-mode or open rules (`allow read, write: if true;`) to production.

Before the first production deploy, write least-privilege rules tied to `request.auth` and deploy them. A typical per-user shape:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

Deploy and verify rules non-interactively:

```bash
firebase deploy --only firestore:rules --project <project-id>
```

Shipping correct rules is part of the Done definition, not an optional hardening step.

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
~/Documents/Development/design-systems
```

Start by reading the design-system index files, then the requested kit:

```bash
ls ~/Documents/Development/design-systems
cat ~/Documents/Development/design-systems/CANONICAL.md
cat ~/Documents/Development/design-systems/README.md
```

Treat the `CANONICAL.md` / `README.md` index as the source of truth for which kits exist; do not rely on a hardcoded list here. Use whichever kit the user names. If they did not name one, pick the closest match to the goal, state the choice, and record it in `docs/goal-log.md` — do not stop and wait for the user.

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

`gh` auth is checked in Preflight, so this should succeed unattended. If `gh` is genuinely unavailable at this point, this is a halt-and-report condition: commit locally, record the blocker in `docs/goal-log.md`, and report that production deployment needs a GitHub remote. Do not silently skip deployment. Once a remote exists, the standard wiring is:

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

If linking Vercel from the CLI and a git remote exists, prefer the stable project-link path:

```bash
vercel link --yes --scope <team-slug> --project <project-name>
```

Do not rely on `vercel link --repo` for unattended setup. It can discover the GitHub remote but still leave no project selected. After linking, verify the GitHub connection with `vercel project inspect <project-name> --scope <team-slug>` or by checking the next production deployment metadata.

Set Firebase env vars in Vercel for every target (production, preview, and development if needed). The CLI `vercel env add ... preview` path can still ask for a preview branch even with `--yes`, so prefer Vercel's REST API for unattended setup when token-backed API access is available. Upsert one variable per request with a single-object body, not an array:

```bash
# For each NEXT_PUBLIC_FIREBASE_* var, with VALUE read from local config without printing it:
tmp=$(mktemp)
KEY=NEXT_PUBLIC_FIREBASE_API_KEY VALUE="$VALUE" node - <<'NODE' > "$tmp"
process.stdout.write(JSON.stringify({
  type: 'encrypted',
  key: process.env.KEY,
  value: process.env.VALUE,
  target: ['production', 'preview', 'development']
}));
NODE
vercel api '/v10/projects/<project-name>/env?upsert=true' -X POST --input "$tmp" --scope <team-slug> --silent
rm -f "$tmp"
```

Pull the values from the Firebase web app config (`firebase apps:sdkconfig WEB ...`). Avoid the dashboard for routine env entry; it requires manual interaction the unattended loop cannot perform. After setting envs, verify with `vercel env ls --scope <team-slug>` and require each key to show `Production, Preview, Development`. If only an interactive Vercel session is available and the CLI prompts for a preview branch, record the blocker and either skip preview envs until production is wired or ask the user for the exact branch scope.

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
- Judge on two lenses every pass: **UI/UX** (drive the real running app via `agent-browser` with real auth; audit with `web-design-guidelines`) and **product effectiveness** (does each feature serve the stated outcome; is anything essential to the outcome missing; is anything gold-plating).
- Run the judge as a fresh pass — a subagent if the harness supports it, otherwise a fresh-context review of the real running app, not the diff.
- Stop only when the judge returns `GOAL MET` on both lenses. The two-or-three-pass cap is an anti-thrash limit on re-litigating the *same* unresolved blocker, not a ceiling on total iteration: keep improving across UI/UX and product passes until the rubric holds. If blockers keep changing, the goal is underspecified — sharpen the rubric instead of spinning.
- Record each pass's verdict, blockers, and fixes in `docs/goal-log.md`.

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
- Ship least-privilege Firestore rules tied to `request.auth` before production; never deploy open/test-mode rules. Keep rules committed and verify deploys/dry-runs.
- Do not bypass auth in production for testing convenience.
- Treat pushes to `main` as production deployments; push `main` only when the exact committed state is intended to ship.
- Do not change Vercel security/project settings autonomously. If the goal genuinely requires it, halt and report rather than guessing.

### Unattended failure policy

The loop runs without a human watching, so a blanket "stop on any error" wastes the run. Classify failures instead:

- **Recoverable** (build/type/lint/test errors, a flaky deploy, a transient network call): fix or retry, and log the cause in `docs/goal-log.md`. Use `diagnose` for hard ones.
- **Fatal** (missing or expired credentials, a destructive/irreversible action, repeated failure of the same cloud command, anything that would recreate resources blindly): stop, leave the project in a clean committed state, and report the exact command and error. Do not paper over it.

## Done checklist for a fresh project

A one-off project is ready for real use when:

- [ ] Project was run as a one-shot `/goal` loop with a rubric and a fresh judge pass.
- [ ] Target platform is documented: mobile, tablet, desktop, or responsive.
- [ ] Selected design system from `~/Documents/Development/design-systems` is documented.
- [ ] `CONTEXT.md` and `docs/decisions.md` exist.
- [ ] `docs/goal-log.md` records the derived persona, rubric, per-pass judge verdicts, and any inferred defaults.
- [ ] Firebase project, web app, Auth provider, and Firestore database exist.
- [ ] `.env.example` documents required `NEXT_PUBLIC_FIREBASE_*` vars.
- [ ] Local `.env.local` works and is ignored.
- [ ] Least-privilege, auth-scoped Firestore rules and indexes are committed and deployed.
- [ ] Private GitHub repo exists and `main` tracks `origin/main`.
- [ ] Vercel project is connected to the GitHub repo.
- [ ] Pushes to `main` automatically deploy production.
- [ ] App has at least one real end-to-end user flow.
- [ ] Verification gate passes (`typecheck`, `lint`, `test`, `build`).
- [ ] Vercel production deployment from `main` is live.
- [ ] Fresh judge pass returned `GOAL MET` on both the UI/UX and product-effectiveness lenses.
- [ ] `agent-browser` smoke test passes at the target viewport/device class.
- [ ] Authenticated flow is tested with a real evaluator account, if auth exists.
- [ ] Live URL is opened or ready to open on the target devices.

To kick off a new project, use the copy-paste `/goal` template in `judged-goal-loop.md` rather than a separate prompt that restates this playbook.
