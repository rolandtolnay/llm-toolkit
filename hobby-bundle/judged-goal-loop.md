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

1. **Rubric:** turn the user's outcome into falsifiable checks.
2. **Build:** implement the smallest version that can satisfy the rubric.
3. **Checks:** run the repo checks that apply.
4. **Judge:** ask a fresh judge subagent to drive the real running app as the target persona.
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

Ask or infer these before writing the rubric:

- **Target:** app, screen, flow, or command.
- **Outcome:** what should change or exist.
- **Target platform:** mobile, tablet, desktop, or responsive.
- **Persona:** who is using it, with constraints such as device, time pressure, expertise, mood, and environment.
- **Design system:** which kit under `/Users/rolandtolnay/Documents/Development/design-systems` to use.
- **Confusions to kill:** what should not be unclear anymore.
- **Guardrails:** what not to build, refactor, or touch.
- **How to drive it:** URL, viewport, credentials file, or command.

## Rubric shape

Keep the rubric short. Every line should be able to pass or fail.

```text
# <Project or flow> judging rubric

Judge as <persona> on <target platform>.

First-principles checks:
1. <Falsifiable check tied to the user's outcome>
2. <Falsifiable check tied to the target device>
3. <Falsifiable check tied to clarity/copy>
4. <Falsifiable check tied to the primary flow>
5. <Falsifiable check tied to trust, save state, auth, or deployment if relevant>

Scope guardrails:
- Grade only <requested scope>.
- Do not propose new features unless required to satisfy the stated outcome.
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

## Judge subagent prompt

Use a fresh context when practical. The judge should not edit code.

```text
You are the judge for one one-shot hobby project. Do not edit code.

Read this rubric:
<rubric>

Grade the real running app as <persona> on <target platform>. Use the normal app path, not a mock and not a production auth bypass.

Drive it via:
- URL: <local or deployed URL>
- Viewport/device: <width height or device class>
- Auth: <normal auth instructions; credentials file path if needed>

Tasks:
1. Walk the primary flow end to end.
2. Try the important controls.
3. Check layout at the target viewport.
4. Check whether the copy fits the audience.
5. Capture concrete evidence: text, screenshot path, command output, or DOM facts.

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
- If rejecting a judge item, write down why.
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
Persona: <who uses it, on what device, in what context>.
Confusions to kill: <what must be obvious or no longer frustrating>.
Guardrails: <what not to build or touch>.

Method: use the judged goal loop from hobby-bundle/judged-goal-loop.md.
1. Write a short rubric with falsifiable checks.
2. Build the smallest working vertical slice.
3. Run typecheck, lint, tests, and build where applicable.
4. Have a fresh judge drive the real running app with agent-browser using normal auth.
5. Fix blockers and surfaced polish, then re-judge until the judge returns GOAL MET.
6. Create or use a private GitHub repo, connect Vercel to it, push main to deploy production, inspect the deployment, and smoke-test the production URL.

Done when: checks pass, production is live from main, agent-browser smoke passes on the target device class, and the fresh judge returns GOAL MET.
```
