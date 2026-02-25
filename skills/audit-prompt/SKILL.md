---
name: audit-prompt
description: Check prompt files for quality issues — wasted tokens, poor positioning, vague instructions. Use when reviewing changes to commands, skills, agents, SKILL.md, or any .md containing LLM instructions.
disable-model-invocation: true
---

<objective>
Audit changed prompt-related files against @references/prompt-quality-guide.md. Validates commands, workflows, agents, skills, templates, references — any file containing LLM instructions.
</objective>

<context>
**Uncommitted changes (staged + unstaged):**
!`git diff HEAD --name-only`

**Untracked files:**
!`git ls-files --others --exclude-standard`

**Target files (from arguments):** $ARGUMENTS
</context>

<process>

1. **Identify files to audit:**
   - If `$ARGUMENTS` contains file paths, use those exclusively
   - If `$ARGUMENTS` is empty, combine uncommitted + untracked files from context. If both are empty, run `git show --name-only --format="" HEAD` to get files from the last commit
   - Filter to prompt-related files — any `.md` or `.yaml` that contains LLM instructions (slash commands, workflows, agent definitions, skills, templates, references, CLAUDE.md files). When unclear, check for XML tags, YAML frontmatter, or behavioral instructions
   - If no prompt-related files found, report "No prompt-related changes detected" and stop

2. **For each file, read full content.** For uncommitted files, also run `git diff HEAD -- <file>` to isolate what changed. Focus audit on changed sections but flag pre-existing issues only if severe.

3. **Evaluate against the quality guide.** Apply The Reliability Test to each instruction. Check against the Common Waste and Common Value tables. **XML boundary verification:** When an XML structural issue appears at the first or last line of Read output, verify the tag exists in the file with Grep before reporting — the Read tool's `</output>` framing is easily confused with file content in XML-heavy files. Map findings to these categories:
   - `Budget waste` → Common Waste table (fluff, filler, verbose restatements, unlikely negations)
   - `Positioning` → Positional Attention Bias (critical constraints buried in middle, success criteria ordering)
   - `Context efficiency` → Context Is a Shared, Depletable Resource + Progressive Disclosure (eager vs lazy loading)
   - `Specificity` → Specificity Over Abstraction + Patterns and Anti-Patterns (vague instructions, missing contrastive examples)
   - `Structure` → project conventions (semantic XML tags, plan format, output format specs)

   **Section-level removal requires per-instruction verification.** When flagging a multi-instruction block (a principles section, a numbered list, a guidelines block) as redundant, verify each instruction individually. A section can be 80% redundant while one instruction carries unique semantics — decision gates, priority orderings, conditional skip logic — not captured elsewhere. Recommend surgical extraction (promote the unique content, remove the rest), not wholesale removal.

   **Success criteria require skip-risk verification before recommending removal.** The 5-7 guideline is a dilution heuristic, not a hard cap — 9 genuinely skip-prone items beats 6 where one was load-bearing. Multi-step behaviors (ask user → act on answer), optional/conditional steps, and post-completion actions (commits, state updates) are inherently skip-prone. Prefer merging over removing.

4. **Report per file:**

   ```
   ### path/to/file.md

   **N issues found**

   1. **[Category]** (line ~N): [specific issue]
      → [concrete fix: "change X to Y" or "remove this line"]

   2. ...
   ```

   Categories: `Budget waste` | `Positioning` | `Context efficiency` | `Specificity` | `Structure`

   Clean files: `**path/to/file.md** — Clean`

5. **Summary:**
   - Files audited: N
   - Findings by category (counts)
   - Top 3 highest-impact fixes

6. **Next steps:** After presenting the summary, use the `AskUserQuestion` tool to ask the user how to proceed. Offer these options:
   - **Fix top 3**: Apply only the top 3 highest-impact fixes. Minimal changes, lowest regression risk.
   - **Fix all issues**: Address every finding from the audit. More comprehensive but still generally safe.
   - **Report only**: No fixes needed — the user just wanted the audit.

   The tool's built-in free text input lets the user specify custom scope (e.g. pick specific issues, disagree with findings).

   Then apply the selected fixes directly to the files.

</process>

<success_criteria>
- [ ] Every finding cites a specific quality guide principle — no subjective opinions
- [ ] Suggestions are concrete ("change X to Y"), not vague ("could be improved")
- [ ] Valid patterns (peripheral reinforcement, corrective rationale, contrastive examples) not flagged as waste
- [ ] Success criteria removals justified by skip-risk assessment, not solely by count
- [ ] Section removals verified per-instruction — no unique semantics lost in wholesale removal
</success_criteria>
