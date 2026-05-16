---
name: pr-qa-browser
description: Derive and execute risk-focused browser QA for dashboard-web PRs. Use when reviewing current-branch pull requests, validating regressions, or needing Agent Browser screenshots and manual follow-ups.
argument-hint: "[pr-number-or-branch]"
---

<objective>
Act like an experienced QA specialist for dashboard-web pull requests: derive the smallest high-confidence set of user stories from the PR description and code diff, automate what Agent Browser can verify, save visual evidence, and clearly hand off what still needs human judgment.
</objective>

<process>

## Step 0: Load browser and project testing context

Before browser work, load the installed Agent Browser guide:

```bash
agent-browser skills get core
```

Follow the dashboard-web `AGENTS.md` browser-testing rules for backend choice, auth state, account selection, screenshots, and cleanup. If downloads are in scope, read `.agents/agent-browser-blob-downloads.md` before testing them.

## Step 1: Inspect the PR surface

Identify the branch, PR metadata, base branch, changed files, and user-facing diff.

Use the PR if available; otherwise compare the current branch to `origin/main`:

```bash
git status --short --branch
git branch --show-current
gh pr view --json number,title,url,baseRefName,headRefName,body 2>/dev/null || true
git diff --name-status origin/main...HEAD
git diff --stat origin/main...HEAD
```

Read changed Vue, TypeScript, route, service, story, and test files. Focus on observable behavior:
- pages/routes changed
- forms, modals, drawers, tables, filters, tabs, selectors, exports, and pagination
- loading, empty, error, disabled, permission, and retry states
- gRPC calls, network behavior, auth/account/capability checks
- data mutations and cleanup paths

## Step 2: Create the evidence directory

Derive a branch slug and create the run directory:

```bash
BRANCH=$(git branch --show-current)
SLUG=$(printf '%s' "$BRANCH" | sed -E 's|^(feature/|feat/|fix/|bugfix/|worktree-)||; s|[^A-Za-z0-9._-]+|-|g')
OUT="etc/mine/test-$SLUG"
mkdir -p "$OUT"
```

Save all screenshots, optional HAR files, and any notes under `etc/mine/test-<branch-slug>/`. Use descriptive screenshot names like `01-payments-filter-empty.png`.

## Step 3: Derive Pareto user stories

Generate 5-8 QA stories that cover the highest regression risk, not every possible path. Prefer the 20% of flows most likely to catch 80% of serious issues.

Prioritize stories in this order:
1. Core workflow changed by the PR.
2. Existing high-traffic flow touched by shared components or services.
3. Data mutation, payment, finance, billing, auth, or capability behavior.
4. State transitions: loading, empty, error, retry, disabled, pagination.
5. Boundary cases introduced by new props, filters, route params, account context, or missing data.
6. Visual regressions in shared UI used by multiple pages.

Write each story as:

```text
S1 — <short title> [risk: high|medium|low] [automation: yes|partial|manual]
As a <user>, I want <action/outcome>, so that <business value>.
Why this matters: <regression risk from PR diff>.
Verification: <browser steps or manual check>.
Evidence target: <screenshot filenames or manual note>.
```

Mark automation realistically:
- `yes`: Agent Browser can navigate, click, fill, assert visible text/state, intercept network, and screenshot.
- `partial`: Agent Browser can reach/capture the state but human visual judgment, timing, external system behavior, or seeded data is still needed.
- `manual`: Requires human-only judgment, credentials, production-only fixture, animation nuance, email/third-party side effect, or unsafe mutation.

## Step 4: Plan automatic coverage

For each `yes` or `partial` story, define a concise browser flow:
- starting URL or route
- account/data fixture needed
- actions to perform
- expected observable UI or network outcome
- screenshot points
- cleanup, if data is changed

Safe mutations are allowed when the data is clearly test/sandbox/local and either cleanup is available or the mutation creates harmless test artifacts. Ask before destructive actions, irreversible finance/payment actions, production-impacting changes, or mutations without a cleanup path.

If required fixture data is missing after checking 2-3 plausible accounts, stop that story and mark it `[blocked]` with the exact missing condition.

## Step 5: Run Agent Browser verification

Use Agent Browser for all feasible stories.

Baseline setup:

```bash
agent-browser set viewport 1440 1000
# Load auth state when using the construction backend and a saved state exists.
[ -f .agent-browser-state.json ] && agent-browser state load .agent-browser-state.json
agent-browser open http://localhost:5173
agent-browser wait --load networkidle
agent-browser snapshot -i
```

Use semantic locators or fresh `snapshot -i` refs before each interaction. Re-snapshot after navigation or dynamic UI changes. Prefer `find role`, `find text`, `find label`, and visible text checks over DOM scraping.

Useful capabilities:
- Navigate: `agent-browser open <url>`
- Inspect: `agent-browser snapshot -i`, `agent-browser get text @eN`, `agent-browser get url`
- Interact: `agent-browser click @eN`, `fill`, `select`, `scroll`, `mouse move/down/up`
- Network errors: `agent-browser network route "**/ListX*" --abort`, then `agent-browser network unroute`
- Screenshots: `agent-browser screenshot "$OUT/<name>.png"` or `--full`
- Evidence: `agent-browser network requests`, HAR recording, video recording when useful

Always capture screenshots at critical states:
- first successful page/state for a changed workflow
- each changed modal/drawer/table/filter/result state
- each error/retry or empty/loading state that the PR changes
- final post-action state after a mutation or recovery

Do not mark a story passed unless the expected behavior was directly observed. Use `[inference]` for conclusions based only on code review.

## Step 6: Identify human follow-up

List what remains for the user to test manually. Be explicit about why Agent Browser could not fully verify it.

Common manual follow-ups:
- subjective visual polish from screenshots
- transient loading animations when no reliable throttling/delay is available
- hover/focus polish beyond basic accessibility visibility
- external emails, webhooks, payment processors, bank flows, or third-party redirects
- blob downloads unless the blob-download recipe was used
- data states not present in available seeded accounts
- destructive or irreversible mutations intentionally skipped

## Step 7: Deliver a concise QA report

Reply with this structure. Keep it concise; include paths, not screenshot dumps.

```markdown
## PR QA Summary
PR: #<number> — <title>
Branch: <branch>
Evidence: `etc/mine/test-<branch-slug>/`

## High-risk user stories
1. **S1 — <title>** [risk: high] [automation: yes]
   - Why: <one sentence>
   - Flow: <one sentence>

## Automated results
- [pass] S1 — <observed result>
  - Evidence: `etc/mine/test-<branch-slug>/01-example.png`
- [fail] S2 — <observed failure>
  - Evidence: `<path>`
  - Suggested investigation: <file/behavior>
- [blocked] S3 — <missing fixture/auth/server condition>

## Manual follow-up for user
- S4 — <what to test manually and why>
- Visual review — inspect screenshots in `etc/mine/test-<branch-slug>/` for spacing, alignment, and animation feel.

## Confidence
<low|medium|high>: <short reason based on automated coverage and remaining gaps>
```

If a browser session was opened, close it at the end unless keeping it open helps the user inspect a failure. Restore any local environment file you changed.

</process>

<success_criteria>
- [ ] PR description and code diff both informed the QA stories.
- [ ] Stories are Pareto-prioritized by regression risk, not exhaustive checklists.
- [ ] Agent Browser was used for every feasible `yes` or `partial` story.
- [ ] Critical screenshots were saved under `etc/mine/test-<branch-slug>/`.
- [ ] Each pass/fail/blocked result is grounded in observed browser output or clearly marked `[inference]`.
- [ ] Manual follow-ups explain exactly what the user still needs to test and why.
- [ ] Browser/auth/environment cleanup was completed or explicitly reported.
</success_criteria>
