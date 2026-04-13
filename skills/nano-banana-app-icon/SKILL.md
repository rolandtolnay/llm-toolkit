---
name: nano-banana-app-icon
description: >
  Design iOS/Android app icons with Nano Banana 2. Use when making, replacing,
  or refining an app icon — runs a discovery brief, writes the JSON prompt,
  critiques the generated PNG against a rubric, and outputs refinement prompts.
---

<objective>
Design a professional iOS/Android app icon with Nano Banana 2 through an interactive brief, a ready-to-paste JSON prompt, and a vision-based iteration loop.

**This skill does NOT generate images itself.** It produces prompts the user runs in gemini.google.com, then reads and critiques the downloaded PNG to produce the next prompt. The loop is: brief → JSON prompt (file) → user runs in Gemini → PNG → critique → refinement prompt (file) → repeat.

All artifacts live under `./icons/<app-slug>/` in the user's current working directory.
</objective>

<essential_principles>

1. **The brief is the work.** Skipping discovery guarantees generic output. The 9 questions in `references/brief-questions.md` are the difference between "AI icon" and "designed icon" — never shortcut them.

2. **One change per iteration. Always.** Never stack edits. Refine in this order: silhouette → single concept → 48×48 readability → palette → shape consistency → depth → differentiation → artifacts. Fixing out of order wastes iterations because later fixes depend on earlier ones being locked.

3. **The 48×48 squint test is the only acceptance gate that matters.** If the central concept isn't recognizable at 48 pixels, the icon fails regardless of how beautiful it looks at 1024. Apply this test every iteration.

4. **Bail to a new Gemini chat after 3 failed iterations.** Gemini conversations accumulate conflicting state. After 3 edits without convergence, open a fresh chat, attach the best-so-far PNG as a reference image, and restart the loop. This is the single biggest unlock for stuck workflows.

5. **Every prompt and critique goes to a file.** The user copy-pastes prompts into gemini.google.com and diffs critiques across iterations — they need markdown files, not chat transcripts. Never produce a prompt only in chat.

</essential_principles>

<process>

## Step 1: Set up the project folder

1. Identify the current working directory (`cwd`). Output files go under `./icons/<app-slug>/` relative to this directory.
2. If the user hasn't already told you the app name, ask: "What's the app called?" Derive a kebab-case slug (e.g., "SnapPlan" → `snapplan`, "Family Hub" → `family-hub`).
3. Check if `./icons/<slug>/` already exists:
   - **Exists with `brief.md`**: this is a resumption. Read `brief.md` and the highest-numbered `NN-critique.md` to understand state. Ask the user: "I see we already started this icon. Do you want to continue refining (go to Step 5) or start over (delete and go to Step 2)?" Skip to the chosen step.
   - **Does not exist**: create it (`mkdir -p ./icons/<slug>`) and proceed to Step 2.
4. Never write files outside `./icons/<slug>/`.

## Step 2: Run the discovery brief

**Read `references/brief-questions.md` before proceeding.**

1. Ask the 9 questions in order. Use `AskUserQuestion` for the three enumerated-choice questions (7, 8, 9). Ask the open-ended questions (1–6) as free-text follow-ups — one at a time so the user can think.
2. Probe vague answers using the examples in the reference. Do not accept "blue" without a hex code. Do not accept two concepts for Q2 — push for one.
3. Run through the probing checklist at the bottom of `brief-questions.md` before moving on. If any item fails, ask a follow-up.
4. Write the captured answers to `./icons/<slug>/brief.md` using the exact format from the reference file.
5. Announce: "Brief saved to `icons/<slug>/brief.md`. Generating the initial prompt now."

## Step 3: Generate the initial prompt

**Read `references/prompt-template.md` before proceeding.**

1. Map each brief line to its JSON field using the mapping table in the reference.
2. Fill in the non-negotiable constants verbatim — do not let them drift even if the user asked for something contradictory in the brief (flag the conflict instead).
3. Determine the reference-image strategy:
   - If the brief has an existing logo path → instruct the user to attach it in Gemini before pasting
   - Otherwise → no attachment, generate from scratch
4. Write the filled-out prompt to `./icons/<slug>/01-initial-prompt.md` using the exact output format from `prompt-template.md`.
5. Tell the user the file path, remind them to copy the JSON block into gemini.google.com, and ask them to come back with the downloaded PNG path.
6. **Stop.** Do not continue to Step 5 until the user returns with a PNG path. Do not generate additional prompts speculatively.

## Step 4: User runs the prompt externally

This step happens outside Claude. The user pastes the JSON into gemini.google.com, generates 4 variations, picks the best, and downloads the PNG.

When the user returns with a file path (e.g., "I saved it to `~/Downloads/icon.png`" or "it's at `icons/snapplan/01-generated.png`"), proceed to Step 5.

If the user comes back and says "that didn't work" or "Gemini refused", look at what they pasted and diagnose — most common failure is that the reference image wasn't attached when the brief required one.

## Step 5: Visually critique the generated icon

**Read `references/evaluation-criteria.md` before proceeding.**

1. Use the `Read` tool to load the PNG the user pointed at. Claude Code supports PNG/JPG natively — the image will appear in your visual context.
2. If the user saved the file outside `./icons/<slug>/`, offer to copy it into the folder as `NN-generated.png` (where NN is the iteration number) so the project folder stays self-contained.
3. Score the image against all 8 rubric criteria. Mark criterion 6 as N/A only if the style family is flat vector.
4. Write the scored rubric to `./icons/<slug>/NN-critique.md` using the exact format from the reference file.
5. Compute the total score. Branch:
   - **Score 7/8 or 8/8 AND criterion 1 (48×48) passes** → icon is done. Skip Step 6. Go to finalization: congratulate the user, offer to generate dark mode / tinted / notification badge variants per the last section of `references/iteration-playbook.md`.
   - **Score 5/8 or 6/8** → proceed to Step 6.
   - **Score ≤4/8** → proceed to Step 6, but note in the critique that escape-hatch territory is near.
   - **Criterion 1 fails** → proceed to Step 6 regardless of total score. 48×48 is a hard gate.

## Step 6: Generate the refinement prompt

**Read `references/iteration-playbook.md` before proceeding.**

1. Take the single most-important failing criterion from Step 5. Use the refinement order in the playbook — silhouette first, then single concept, then 48×48, etc.
2. Pattern-match that criterion to one of the refinement templates in the playbook.
3. Fill in the template using specifics from the brief and the generated image.
4. Check the iteration count:
   - **Iterations 1–3** → write a conversational refinement prompt to `./icons/<slug>/NN-refinement-prompt.md`. Instructions tell the user to paste into the SAME Gemini chat.
   - **Iteration 4+ with no convergence** → trigger the escape hatch. Identify the best previous iteration (highest rubric score). Write `./icons/<slug>/NN-restart-prompt.md` using the escape-hatch template from the playbook. Instructions tell the user to open a NEW Gemini chat and attach the best-so-far PNG.
5. Tell the user the file path and ask them to run it, download the new PNG, and return with the path.
6. **Stop.** Return to Step 4 when the user comes back.

## Step 7: Finalize and generate variants

Triggered when Step 5 passes (7/8+ and criterion 1 passes).

1. Congratulate the user briefly — one line, not a victory lap.
2. Copy the final prompt (the one that produced the winning iteration) to `./icons/<slug>/final-prompt.md` for easy reference.
3. Offer the three variants from the playbook: dark mode, iOS tinted monochrome, notification badge high-contrast. Ask which they want.
4. For each requested variant, write a variant prompt to `./icons/<slug>/final-variant-<name>.md` with instructions to paste into the same Gemini chat as the final iteration.
5. The skill's job is done. Do not keep iterating unless the user asks.

</process>

<reference_index>
Supporting files in `references/` — loaded lazily, only when the corresponding step needs them:

- `brief-questions.md` — The 9 discovery questions with probing notes, the brief file format, and a worked example. **Read in Step 2.**
- `prompt-template.md` — JSON template with placeholder mapping, non-negotiable constants, reference image strategy, and the output file format. **Read in Step 3.**
- `evaluation-criteria.md` — 8-criterion visual rubric with pass/fail definitions and the critique file format. **Read in Step 5.**
- `iteration-playbook.md` — Refinement order, failure-mode → refinement-prompt templates, the escape hatch, and final-variant prompts. **Read in Step 6 (and Step 7 for variants).**

Keep references lazy-loaded — do not read all four up front. Each step reads only what it needs.

The project also has a broader reference at `docs/nano-banana-2-prompting-guide.md` (generic Nano Banana 2 prompting guide, not app-icon specific). That document is not required by this skill and is not loaded automatically.
</reference_index>

<output_conventions>

All files live under `./icons/<app-slug>/` in the current working directory. Naming:

- `brief.md` — written once in Step 2
- `NN-initial-prompt.md` — initial prompt (only NN=01)
- `NN-refinement-prompt.md` — refinement prompts from iteration 02 onward
- `NN-restart-prompt.md` — escape-hatch prompts (iteration 4+)
- `NN-critique.md` — scored rubric for iteration NN
- `NN-generated.png` — optional, the PNG the user downloaded from Gemini
- `final-prompt.md` — written on completion, the prompt that produced the final icon
- `final-variant-<name>.md` — variant prompts (dark mode, tinted, badge)

Example of a completed project:

```
icons/snapplan/
├── brief.md
├── 01-initial-prompt.md
├── 01-generated.png
├── 01-critique.md
├── 02-refinement-prompt.md
├── 02-generated.png
├── 02-critique.md
├── 03-refinement-prompt.md
├── 03-generated.png
├── 03-critique.md
├── final-prompt.md
├── final-variant-dark-mode.md
└── final-variant-tinted.md
```

</output_conventions>

<success_criteria>
- [ ] The full 9-question brief was captured before any prompt was written (skipping this guarantees generic output)
- [ ] Each refinement prompt targets exactly one change — never stacked edits
- [ ] All generated prompts and critiques are written to markdown files under `./icons/<slug>/`, not only in chat
- [ ] Each critique scores all 8 rubric criteria and identifies a single next-change focus
- [ ] The escape hatch (new Gemini chat + reference image) was triggered once iteration count hit 4 without convergence
</success_criteria>
