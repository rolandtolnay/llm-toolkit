# <project-name> — agent working notes

How any agent builds in this repo. The task-specific goal lives in the prompt; this file is the standing method so loops do not have to repeat it.

## Domain & locked decisions

- Canonical vocabulary is `CONTEXT.md`. Use those terms exactly during implementation. Use user-friendly variants for user-facing text when the glossary terms are too internal.
- Locked decisions are in `docs/adr/` — read the ones your task touches and do not re-litigate them.
- Non-obvious choices and their reasons are in `docs/decisions.md` — read it before undoing anything deliberate; record new lightweight decisions there.
- Standing locks for this project:
  - <decision 1, with ADR/doc link if available>
  - <decision 2, with ADR/doc link if available>
  - <styling source, e.g. `app/tokens.css` or selected design-system tokens, is the source of truth; avoid ad hoc colors/radii>

## Stack & cloud

- Default hobby stack: Next.js App Router + React + TypeScript; Firebase Auth + Firestore; installable PWA where useful; deploy to Vercel.
- Project-specific stack notes:
  - Frontend: <framework/version>
  - Backend/data: <Firebase project/services or other backend>
  - Hosting: <Vercel project/team/repo connection>
  - Design system: <kit under `~/Documents/Development/design-systems` or local token source>
- Cloud setup is documented in `docs/external-setup.md`. Reuse existing resources; do not reprovision or recreate resources after a failure.
- If a cloud command fails unexpectedly, stop and report the exact command/error rather than guessing, recreating resources, or changing project security settings.

## Deployment

- `main` auto-deploys to production via Vercel's Git integration once configured. Pushing to `main` builds and ships, so do not push half-done work.
- Path: run the checks the change touches, commit only the task's files, then push `main`. Vercel builds on push — do not use manual `vercel --prod` unless GitHub integration is unavailable or broken.
- Production URL: <https://example.vercel.app>
- Hold the push only if the user asks for a plan/preview, the work is blocked, or it is unsafe to ship.
- For a throwaway smoke target, use a Vercel preview deployment or a non-`main` branch preview.
- After production is ready, verify changed behavior on the production URL with `agent-browser` for UI or HTTP checks for routes/assets. Report the commit, production URL, and checks actually run.

## How to verify

- Verify with a fresh, separate context, not self-critique. Prefer a judge subagent/fresh-context pass for UI/UX and product-effectiveness checks.
- Run the repo checks the change touches. For most Next.js hobby projects:
  - `npm run typecheck`
  - `npm run lint`
  - `npm run test`
  - `npm run build`
- Add Vitest units for changed domain logic. Report only checks you actually ran; if one fails or was skipped, say so with the output or reason.
- Verify UI/UX changes against the real app from a user's perspective with `agent-browser`:
  - Use the target viewport from the goal: <mobile/tablet/desktop/responsive viewport>.
  - Sign in through the normal auth form when auth exists.
  - Evaluator credentials live in <ignored credentials path, e.g. `.local/evaluator-credentials.md`>.
  - Never build or use a production auth bypass.
- Hand important UI screens or flows to a fresh judge/subagent. Do not score your own work as the final judge.
- Dogfooding is a separate, occasional whole-app bug hunt; it is not a per-change gate unless the task asks for it.
- Delegate bulky, repetitive sub-work such as synthetic cases or per-screen judging to bounded parallel subagents and reason over their summaries.

## Architecture & data access

- Keep pure domain logic in small modules that can be tested without browser or cloud.
- Put data access behind feature/domain interfaces; Firestore or other persistence is an adapter behind those seams.
- React components should consume feature/domain interfaces, not scatter raw database paths or cloud details.
- Prefer deep modules with small interfaces. Avoid shallow pass-through files that only add navigation overhead.
- The interface is the test surface.

## Build style

- Build the simplest thing that meets the goal; do not add features, refactors, abstractions, or infrastructure beyond what the task needs.
- Optimize for the target platform from the goal:
  - Mobile: portrait-first, thumb-reachable controls, large tap targets, no horizontal overflow.
  - Tablet: use extra width without making a cramped desktop layout.
  - Desktop: make keyboard/pointer interactions natural and use density deliberately.
  - Responsive: define the primary target and verify adjacent breakpoints.
- Use the selected design system/tokens as the styling source of truth. Avoid literal colors, radii, spacing, and shadows in components when tokens exist.
- User-facing copy should fit the audience and avoid implementation jargon, generic praise, filler, title-case overuse, and AI-sounding polish.

## Security and operations

- Keep `.env.local`, `.local/*`, evaluator credentials, service-account JSON, and other secrets ignored.
- Browser Firebase config may be public app config, but local env files still stay ignored.
- Use least-privilege Firestore rules tied to `request.auth` before production. Never deploy open/test-mode rules.
- Use Admin SDK only in local/admin scripts, not browser code.
- Do not change Vercel security/project settings autonomously. If the goal requires that, halt and report.
- Treat missing credentials, destructive actions, repeated cloud-command failures, and resource recreation as fatal blockers. Leave the tree clean if possible and report exact commands/errors.
