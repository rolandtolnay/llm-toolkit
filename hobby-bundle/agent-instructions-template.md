# <project-name> — agent working notes

How any agent builds in this repo. The task-specific goal lives in the prompt; this file is the standing method so loops do not have to repeat it. Read the canonical sources below for detail instead of trusting a summary.

## Canonical sources

- Domain vocabulary → `CONTEXT.md` (glossary only). Use these terms in implementation; use user-friendly variants in user-facing copy when the glossary terms are too internal.
- Locked decisions and their reasons → `docs/decisions.md`. Do not re-litigate them; record new lightweight decisions there, and use `docs/adr/` only for hard-to-reverse, trade-off-driven choices.
- Cloud/project facts — backend/hosting IDs, regions, env wiring, evaluator accounts, emulator/local commands → `docs/external-setup.md`. Reuse existing resources; never reprovision or recreate them after a failure.
- Full build/verify/deploy method → `<method docs path, e.g. etc/playbook.md>`.
- Judged `/goal` loop — rubric, judge prompt, builder rules → `<method docs path, e.g. etc/judged-goal-loop.md>`.
- <Any project-specific doc, e.g. asset/art direction → `docs/<topic>.md`>.

## Standing locks (do not break without an explicit goal)

- <decision 1, e.g. data scoping/security boundary — with the rule that enforces it>
- <decision 2, e.g. primary target platform + viewport and its non-negotiable UX constraints>
- <decision 3, e.g. a core flow rule that must not gain friction>
- <styling source, e.g. `app/tokens.css` or selected design-system tokens, is the source of truth; no ad hoc colors, radii, spacing, shadows, or typography>

## Stack

<Frontend + backend + hosting in one line, e.g. Next.js App Router + React + TypeScript; Firebase Auth + Firestore (project `<id>`); deployed to Vercel.> Project IDs, regions, and env wiring are in `docs/external-setup.md`. If a cloud command fails unexpectedly, stop and report the exact command/error rather than guessing or recreating resources.

## Build style

- Build the simplest thing that meets the goal; no features, refactors, abstractions, or infrastructure beyond what the task needs.
- Keep pure domain logic in small testable modules; put data access behind feature/domain interfaces with persistence as an adapter; components consume those interfaces, not raw database paths. The interface is the test surface. (Detail: `<method docs path>` → architecture.)
- User-facing copy: short, glanceable, concrete, fitted to the audience. Avoid jargon, generic praise, filler, title-case overuse, and AI-sounding polish.

## Verify

- Run the repo checks the change touches — `npm run typecheck`, `npm run lint`, `npm run test`, `npm run build` — and add unit tests for changed domain logic. Report only checks you actually ran; if one fails or was skipped, say so.
- Verify UI/UX from the user's perspective with `agent-browser` at the target viewport (<mobile/tablet/desktop/responsive>), signed in through the normal auth form (never a production auth bypass). Evaluator credentials live in `<ignored path, e.g. .local/evaluator-*.md>`; never print them.
- Verify with a fresh context, not self-critique: hand important screens/flows to a fresh judge/subagent. Loop method and judge prompt are in `<method docs path, e.g. etc/judged-goal-loop.md>`. Delegate bulky, repetitive sub-work to bounded parallel subagents and reason over their summaries.
- Dogfooding is a separate, occasional whole-app bug hunt, not a per-change gate unless the task asks for it.

## Deploy

- `main` auto-deploys production via Vercel's Git integration once configured, so never push half-done work. Run the checks, commit only the task's files, then push `main`; do not run manual `vercel --prod` unless the GitHub integration is broken. For a throwaway smoke target, use a Vercel preview or non-`main` branch.
- Production URL: `<https://example.vercel.app>`. After shipping, verify changed behavior there (`agent-browser` for UI, HTTP checks for routes/assets) and report the commit, URL, and checks run.
- Hold the push only if the user asks for a plan/preview, the work is blocked, or it is unsafe to ship.

## Security & blockers

- Keep `.env.local`, `.local/*`, evaluator credentials, and service-account JSON ignored. Use least-privilege rules tied to `request.auth` (or the equivalent auth boundary); never deploy open/test-mode rules. Use admin/privileged SDKs only in local/admin scripts, not browser code.
- Do not change Vercel security/project settings autonomously; if the goal requires it, halt and report.
- Treat missing credentials, destructive actions, repeated cloud-command failures, and resource recreation as fatal blockers: leave the tree clean if possible and report the exact command/error.
