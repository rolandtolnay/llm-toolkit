# Judged goal loop for one-shot hobby projects

Use this when a project goal includes product quality that cannot be fully unit-tested: "make it feel obvious", "make this pleasant on tablet", "make the copy less technical", "this should be ready to use on my phone tonight".

The point is simple: the builder should not be the only judge of its own work. Turn the outcome into a small rubric, have a fresh judge drive the real running app, fix what the judge finds, and stop only when the judge returns `GOAL MET`.

## When to use it

Use this loop for one-shot `/goal` projects in Codex or Claude Code when the LLM is expected to build, test, deploy, and present a working result.

It is especially useful for:

- new hobby apps
- UI/UX quality
- target-device fit: mobile, tablet, desktop, or responsive
- user-facing copy
- onboarding/auth flows
- "ready to use" polish before shipping production

Do not turn this into ceremony. Two or three judge passes is usually enough. If blockers keep changing, the goal is underspecified; sharpen the rubric instead of spinning.

## Core loop

1. **Rubric:** turn the user's outcome into falsifiable checks across two lenses — UI/UX and product effectiveness.
2. **Build:** implement the smallest version that can satisfy the rubric.
3. **Checks:** run the repo checks that apply.
4. **Judge:** run a fresh judge pass — a subagent if the harness supports it, otherwise a fresh-context review — driving the real running app as the target persona.
5. **Fix:** resolve blockers and surfaced polish.
6. **Re-judge:** repeat until the judge returns `GOAL MET`.
7. **Ship:** deploy the exact committed state and verify the live URL.

Done means:

```text
BLOCKERS: none
VERDICT: GOAL MET
```

plus the surfaced polish from that pass has either been fixed or explicitly rejected with a reason.

## Inputs the builder needs

The user is not available mid-run, so **derive** these from the goal description rather than asking, and persist them to `docs/goal-log.md`:

- **Target:** app, screen, flow, or command.
- **Outcome:** what should change or exist.
- **Target platform:** mobile, tablet, desktop, or responsive.
- **Persona:** who is using it, with constraints such as device, time pressure, expertise, mood, and environment. When the user did not name one, infer the most likely persona from the goal and state the assumption in `docs/goal-log.md`.
- **Design system:** which kit under `/Users/rolandtolnay/Documents/Development/design-systems` to use.
- **Confusions to kill:** what should not be unclear anymore.
- **Guardrails:** what not to build, refactor, or touch.
- **How to drive it:** URL, viewport, credentials file, or command.

## Rubric shape

Keep the rubric short. Every line should be able to pass or fail.

```text
# <Project or flow> judging rubric

Judge as <persona> on <target platform>.

UI/UX checks:
1. <Falsifiable check tied to the target device>
2. <Falsifiable check tied to clarity/copy>
3. <Falsifiable check tied to the primary flow>
4. <Falsifiable check tied to trust, save state, auth, or deployment if relevant>

Product-effectiveness checks:
5. <Does the primary flow actually achieve the user's stated outcome?>
6. <Is every feature pulling its weight toward the outcome, or is something gold-plating?>
7. <Is anything essential to the outcome missing?>

Scope guardrails:
- Grade only <requested scope>.
- Additions are allowed only when essential to the stated outcome; reject feature creep beyond it.
- Empty blockers is a valid result.

Return format:
- BLOCKERS: must-fix issues, or "none".
- POLISH: smaller friction with concrete fixes, or "none".
- VERDICT: GOAL MET only if blockers are empty; otherwise BLOCKERS REMAIN.
```

Good checks are concrete:

- "A first-time user can complete the primary action without opening docs."
- "There is no horizontal overflow at the chosen viewport."
- "The page uses the selected design-system tokens instead of ad hoc colors."
- "User-facing copy avoids implementation terms from `CONTEXT.md` unless those terms are also natural for the audience."
- "The signed-in flow uses normal Firebase Auth, not a bypass."

Bad checks are vague:

- "The UI is good."
- "The app feels modern."
- "The copy is friendly."

## Judge prompt

Run as a fresh judge pass — a subagent if the harness supports it, otherwise a fresh-context review. The judge should not edit code.

```text
You are the judge for a one-shot hobby project. Do not edit code.

Read this rubric:
<rubric>

Grade the real running app as <persona> on <target platform>, on two lenses: UI/UX and product effectiveness. Use the normal app path, not a mock and not a production auth bypass.

Drive it via:
- URL: <local or deployed URL>
- Viewport/device: <width height or device class>
- Auth: <normal auth instructions; credentials file path if needed>

Tasks:
1. Walk the primary flow end to end and confirm it achieves the stated outcome.
2. Try the important controls.
3. Check layout at the target viewport.
4. Check whether the copy fits the audience.
5. Audit the UI against web-design-guidelines (accessibility, interaction).
6. Judge product fit: does every feature serve the outcome, is anything gold-plating, is anything essential missing?
7. Capture concrete evidence: text, screenshot path, command output, or DOM facts.

Return exactly:

BLOCKERS:
- <location> — <what blocks the persona> — <concrete fix>
(or "none")

POLISH:
- <location> — <friction> — <concrete fix>
(or "none")

VERDICT: GOAL MET | BLOCKERS REMAIN

Rules:
- `GOAL MET` is allowed only when blockers are empty.
- Do not invent issues to hit a quota.
- Scope is only the requested project/flow.
- Prefer removing, reordering, and simplifying over adding features.
```

## Builder rules

The builder owns the final decision. The judge provides evidence, not commands.

- Fix every blocker unless it conflicts with the user's explicit goal, `CONTEXT.md`, an ADR, or a security boundary.
- Fix surfaced polish when it is cheap and aligned with the goal.
- If rejecting a judge item, write down why in `docs/goal-log.md`.
- Record each judge pass — verdict, blockers, and what you changed — in `docs/goal-log.md` so the user can reconstruct the run.
- Re-run checks after fixes.
- Re-judge fresh after meaningful changes.
- Stop only after `GOAL MET`.

## User-facing copy rule

Use canonical terms from `CONTEXT.md` for implementation and internal reasoning. Do not blindly expose those terms to users.

For visible copy, use the `humanizer` skill and write for the actual audience. Remove AI-sounding patterns: generic praise, filler, vague benefit language, title-case overuse, emoji decoration, and mechanical bold-label lists.

## Deployment rule

A judged local app is not done until the shipped app is verified.

For the hobby bundle, production should usually ship through GitHub-connected Vercel:

1. Commit the exact intended files.
2. Push `main`.
3. Wait for Vercel's production deployment.
4. Smoke-test the production URL with `agent-browser`.
5. Report the URL and the checks actually run.

Use a manual `vercel deploy --prod` only when GitHub integration is unavailable or broken, and deploy from a clean committed tree.

## Copy-paste `/goal` template

```text
/goal Build <APP / FLOW> as a one-shot hobby project.

Outcome: <what should exist or improve>.
Target platform: <mobile | tablet | desktop | responsive>.
Design system: <kit under /Users/rolandtolnay/Documents/Development/design-systems>.
Guardrails: <what not to build or touch>.

This runs unattended: I will walk away and return to a finished, deployed app. Never block on a question — infer sensible defaults from this goal, state them, and record them in docs/goal-log.md. Derive the user persona and the things that must be obvious from this description yourself.

Method: follow hobby-bundle/playbook.md and the judged goal loop in hobby-bundle/judged-goal-loop.md.
1. Run the Preflight checks; halt and report if any credential is missing.
2. Derive the persona and write a short rubric with falsifiable checks on two lenses: UI/UX and product effectiveness. Persist persona + rubric to docs/goal-log.md.
3. Build the smallest working vertical slice.
4. Run typecheck, lint, tests, and build where applicable.
5. Run a fresh judge pass driving the real running app with agent-browser using normal auth; audit UI with web-design-guidelines and judge product fit against the outcome.
6. Fix blockers and surfaced polish, log each pass, and re-judge until the judge returns GOAL MET on both lenses.
7. Use a private GitHub repo, connect Vercel to it, set Firebase env vars non-interactively, deploy least-privilege Firestore rules, push main to deploy production, inspect the deployment, and smoke-test the production URL.

Done when: checks pass, least-privilege rules are deployed, production is live from main, agent-browser smoke passes on the target device class, docs/goal-log.md is complete, and the fresh judge returns GOAL MET.
```
