---
name: create-skill
description: Create new Claude Code skills through collaborative conversation. Use when building a new SKILL.md, creating a skill from scratch, or turning a workflow into a reusable skill.
---

<essential_principles>

Skills are prompts — all prompt engineering principles apply. Every token must earn its place through behavioral change, not theoretical correctness. If removing an instruction changes nothing, it wastes budget. If removing it causes failures, it earns its place.

Progressive disclosure governs skill loading: description (always in system prompt, ~25-35 words) -> SKILL.md body (on invoke) -> supporting files (on demand). Default to lazy loading. Promote to eager only when needed on every execution path.

The description is the gatekeeper — if the skill doesn't trigger, nothing else matters. Write it LAST, after the body is complete and you know exactly what the skill does.

Match specificity to fragility. Fragile operations (deployments, migrations) need exact instructions. Creative operations (analysis, reviews) need principles and freedom. Don't over-specify what the LLM handles well by default.

Show, don't tell. Examples and templates communicate format better than prose. One good example replaces paragraphs of description.

Explain the why. Help Claude understand intent, not just follow rules. Theory of mind and corrective rationale ("never X — because Y") outperform rigid MUSTs. LLMs generalize better when they understand the reasoning.

</essential_principles>

<process>

## Step 1: Capture Intent

Check the current conversation context first. Has the user been doing work that could become a skill? Look for:
- Repeated tool calls or corrections
- Established sequences or workflows
- Clear I/O patterns
- Domain knowledge the user keeps re-explaining

**If context exists:** Extract answers silently — what the skill does, what tools it uses, what sequence was followed, what output looked like. Present your understanding:

"Based on our conversation, here's what I'm seeing for this skill:
- **Purpose:** [what it does]
- **Trigger:** [when it should activate]
- **Key steps:** [sequence observed]
- **Output:** [what it produces]

What's missing or wrong?"

**If no context:** Use AskUserQuestion:
- header: "Skill purpose"
- question: "What should this skill enable Claude to do?"
- options:
  - "Automate a workflow" — multi-step process I repeat
  - "Embed domain knowledge" — teach Claude about a specific domain
  - "Create consistent output" — documents, reports, code in a specific format
  - "Let me describe it" — I'll explain in my own words

**Output of this step:** A 1-2 sentence statement of what the skill does and when it triggers.

## Step 2: Gather Requirements

Surface assumptions explicitly before questioning:

"Based on what you've described, here's what I'm assuming:
- [assumption 1]
- [assumption 2]
- [assumption 3]
Let me know if any are wrong."

Then generate 2-4 questions using AskUserQuestion based on genuine gaps. Each question should include:
- Brief analysis of why it matters
- 2-3 options with descriptions
- "Let me describe it" escape hatch

**Questions to choose from** (pick based on actual gaps — don't ask all):

**Scope boundaries:**
- header: "Scope"
- question: "What should this skill NOT do?"
- options based on likely adjacent concerns

**Output format:**
- header: "Output"
- question: "What does the skill produce?"
- options: specific formats relevant to the task

**Dependencies:**
- header: "Dependencies"
- question: "Does this skill need external tools?"
- options: "MCP servers", "Scripts/executables", "No external dependencies"

**Audience:**
- header: "Audience"
- question: "Who will use this skill?"
- options: "Just me", "My team (shared project)", "Public distribution"

Do NOT ask about:
- Technical implementation details Claude can figure out
- Codebase patterns Claude can discover
- Obvious structural decisions

**Decision gate** — after 1-2 rounds, present:
- header: "Ready to build?"
- question: "I have enough context to draft the skill. Ready to proceed?"
- options:
  - "Proceed to building" — create the skill with current context
  - "I have more to clarify" — let me add details
  - "Let me add context" — I want to provide additional information

Max 2 rounds of questions, then proceed regardless.

## Step 3: Decide Structure

Default to simple (single SKILL.md file).

**Simple** when:
- Single workflow or use case
- Under 200 lines of instructions
- One primary user intent

**Complex** (any one triggers):
- Multiple distinct user intents requiring different workflows
- Large domain knowledge base (>300 lines would bloat SKILL.md)
- Reusable scripts that benefit from separate files
- Expected significant growth in scope

State decision and reasoning: "This will be a **[simple/complex]** skill because [reason]."

If complex, describe proposed directory structure with file purposes.

## Step 4: Draft the Skill

Before writing, read these reference files:
- `references/prompt-principles.md` — prompt quality principles
- `references/skill-patterns.md` — relevant pattern for the category
- `references/templates/simple-skill.md` or `references/templates/complex-skill.md`

### Writing the body

Write the body FIRST. Do not write the description yet.

1. **Open with objective.** Clear statement of what the skill accomplishes and why.

2. **Write the process/workflow.** Use numbered steps with specific, actionable instructions.
   - Use XML structural tags for major boundaries (`<process>`, `<success_criteria>`, `<examples>`)
   - Use markdown within tags where natural (step names, subsections, lists)
   - Include lazy-load triggers for reference files: "Read `references/X.md` before proceeding"

3. **Include examples** where output format matters. Show the expected output — one good example replaces paragraphs of description. Use `<examples>` tags.

4. **Include anti-patterns** only for observed failure modes. Don't negate unlikely behaviors.

5. **Write success criteria** at the end, ordered by skip risk (highest first). Keep to 5-7 items. Use concrete, verifiable language.

6. **For complex skills:** Write supporting files with the same quality standards. References one level deep from SKILL.md.

### Writing the frontmatter

Read `references/description-guide.md` and `references/frontmatter-reference.md` before proceeding.

After the body is complete, write the frontmatter:

1. **name:** kebab-case, matches directory name, max 64 chars, no "claude" or "anthropic"

2. **description:** Write LAST. Apply `references/description-guide.md` principles:
   - Lead with a distinct verb
   - Include "Use when" clause
   - 25-35 words
   - Use user vocabulary
   - Anchor to concrete artifacts
   - No XML angle brackets

3. **Optional fields:** Set only what's needed:
   - `disable-model-invocation: true` for dangerous workflows (deploy, delete)
   - `allowed-tools` for restricted tool access
   - `context: fork` for isolated execution
   - Leave other fields at defaults unless there's a reason

### Writing the skill file(s)

Determine the correct location. Skills belong in one of:
- `~/.claude/skills/<name>/` — personal, all projects
- `.claude/skills/<name>/` — project-specific
- A plugin's `skills/<name>/` — plugin distribution

Ask the user if the location isn't obvious from context.

Write the SKILL.md file and any supporting files. Ensure all referenced files exist.

## Step 5: Validate

Run through this checklist before presenting to the user:

**Frontmatter:**
- [ ] name: kebab-case, matches directory, max 64 chars, no reserved words
- [ ] description: 25-35 words, includes "Use when", no XML tags, max 1024 chars
- [ ] Optional fields set only when needed

**Structure:**
- [ ] SKILL.md under 500 lines
- [ ] References one level deep
- [ ] All referenced files exist
- [ ] No empty directories

**Content:**
- [ ] Imperative voice throughout
- [ ] Specific and actionable instructions
- [ ] Examples where format matters
- [ ] No motivational fluff or filler
- [ ] No negations of unlikely behaviors
- [ ] Consistent terminology
- [ ] Success criteria ordered by skip risk

Present the completed skill to the user with a brief summary of what was created.

## Step 6: Testing Guidance

After presenting the skill, provide testing guidance:

**Two invocation methods:**
1. **Auto-trigger:** Ask something that matches the description (tests description quality)
2. **Direct:** Use `/skill-name` (tests body instructions)

**What to check:**
1. Does it trigger when it should? (description test)
2. Does Claude follow the instructions? (body test)
3. Is output quality good? (end-to-end test)

**Description debugging:** Ask Claude "When would you use the [skill-name] skill?" — Claude quotes the description back, revealing matching gaps.

**Common iterations:**
- **Undertriggering:** Add keywords to description, be more "pushy" about triggers
- **Overtriggering:** Add negative triggers ("Do NOT use when..."), be more specific
- **Instructions not followed:** Check positioning (critical items at start/end), reduce verbosity, add examples


</process>

<communication>

Adapt depth based on context cues. If the user mentions SKILL.md, frontmatter, or descriptions, they know the basics — skip introductions. If new to skills, briefly explain concepts as they arise (e.g., "frontmatter is the YAML between `---` markers at the top").

</communication>

<success_criteria>
- [ ] Description written LAST, after body is complete, following description-guide.md
- [ ] Validation checklist completed before presenting to user
- [ ] Testing guidance provided after presenting the skill
- [ ] Reference files read before drafting (lazy loading applied)
- [ ] Requirements gathered through collaborative conversation, not interrogation
- [ ] Structure decision stated and justified (simple by default)
</success_criteria>
