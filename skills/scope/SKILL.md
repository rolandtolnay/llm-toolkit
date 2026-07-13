---
name: scope
description: Turn a vague prompt into a well-bounded task — ask only the questions the model can't answer itself, confirm the frame, then implement. Use at the start of a fresh conversation when the request lacks bounds or success criteria.
disable-model-invocation: true
---

Take the user's prompt and close only the gaps that would make a frontier model guess badly. Ambiguity invites 10x the work: without bounds and a definition of done, the model fills in the blanks and over-builds. Your job is a tight frame, not a PRD — describe the destination, never the steps.

If no prompt was given, ask once: "What do you want done, and where?"

## 1. Check the frame

Judge the prompt against four fields. Mark each **present / inferable / missing**:

1. **Outcome** — what the user can do or see when it works, stated as a result. This is what done looks like.
2. **Bounds** — the sandbox: which area or module the work attaches to, what's off-limits, and where the relevant information lives (repo area, doc, ticket, URL) when it isn't discoverable.
3. **Verification** — how to check the work: the observable signal or command that proves the outcome, and the existing behavior that must keep working.
4. **Hard constraints** — only if real: a fixed API shape, required integration, specific data.

**Infer over interrogate.** Do a quick orientation pass (a minute, not an investigation) to resolve what the repo can answer: conventions, stack, existing patterns, likely anchor. Never ask about those. A field is a question only when the answer would materially change the implementation *and* can't be read from the code or reasonably defaulted.

## 2. Ask the gaps

Ask the remaining gaps in one batched round via the built-in question tool — usually 1–3 questions, each with a sensible default so the user can accept fast. Lead with outcome if it's vague. If nothing is missing, skip straight to step 3.

## 3. Confirm the frame

Restate your understanding compactly:

```markdown
## Task frame
**Goal:** <outcome, as a delta from current behavior>
**Bounds:** <where the work lives; what stays untouched>
**Verification:** <how you'll prove it works; what must not break>
**Out of scope:** <what you will deliberately not do>
```

Then ask for approval via the built-in question tool: proceed, or adjust. Incorporate any correction and re-confirm only if the goal itself changed.

## 4. Implement

On approval, implement the frame end to end. Stay inside the bounds; match the conventions the orientation pass found; don't add features or abstractions beyond what the frame requires. Run the verification you named — tests, build, or driving the actual behavior — before reporting. Report faithfully: what you verified, what you couldn't, anything deliberately left out of scope.

## Success criteria

- No question asked that the repo, a default, or a quick look could have answered
- Frame confirmed by the user before any implementation
- Implementation stays within the confirmed bounds
- The named verification actually ran, and the final report distinguishes verified from unverified
