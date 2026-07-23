# Frontier LLM Prompting Guide

A lean, model-agnostic synthesis of the prompting guidance for the current frontier model generation. It contains only the principles the vendors' guidance shares.

Model-specific behavioral tendencies, the patches for them, and API details live in the source guides — consult them when accuracy for a specific model matters:

- [GPT Prompting Guide](gpt-prompting-guide.md)
- [Claude Fable 5 Prompting Guide](fable-5-prompting-guide.md)

## What changed in this generation

Three shifts drive nearly every recommendation in this guide:

1. **Stronger instruction following.** A brief instruction now steers behavior that previously required enumerating every case. Listing each unwanted pattern by name is no longer necessary — and the extra text adds noise.
2. **Better intent understanding.** These models infer the user's underlying goal and intended level of work from context. You no longer need to prescribe every step; you do still need domain context, hard constraints, approval boundaries, and success criteria.
3. **More autonomy and persistence.** Frontier models sustain long multi-step runs, dispatch subagents, and self-verify. The prompt's job shifts from directing each step to defining the destination, the boundaries, and when to stop.

The consequence: **legacy prompts written for earlier models are often too prescriptive and degrade output quality on frontier models.** Process-heavy instruction stacks that once kept a weaker model on track now narrow the search space, produce mechanical answers, and waste tokens. Capability improvements are a standing invitation to re-evaluate which instructions, tools, and guardrails are still needed.

## Outcome-first prompts

Define the target outcome, success criteria, constraints, and available evidence — then let the model choose the path. Describe the destination, not every step.

Prefer this:

```text
Resolve the customer's issue end to end.

Success means:
- the eligibility decision is made from the available policy and account data
- any allowed action is completed before responding
- the final answer includes completed_actions, customer_message, and blockers
- if evidence is missing, ask for the smallest missing field
```

Avoid this style unless every step is truly required:

```text
First inspect A, then inspect B, then compare every field, then think through
all possible exceptions, then decide which tool to call, then call the tool,
then explain the entire process to the user.
```

Step-by-step scripts encode one solution path. Outcome definitions give the model room to pick the right search, tool, or reasoning strategy for the actual situation — which is where frontier models outperform.

### Give the reason, not only the request

Models perform better when they understand the intent behind a request: context lets them connect the task to relevant information rather than inferring intent on their own.

```text
I'm working on [the larger task] for [who it's for]. They need [what the output
enables]. With that in mind: [request].
```

## Lean prompts: state each instruction once

Removing repeated instructions, redundant examples, and verbose tool descriptions measurably improves both quality and cost. In vendor-internal coding-agent evals, leaner system prompts improved scores by roughly 10–15% while reducing total tokens by 41–66%. Skills developed for prior models are often too prescriptive for the current generation and can degrade output quality.

To trim a working prompt without losing important guidance:

- Remove one group of instructions, examples, or tools at a time, then rerun the same evals.
- State each instruction once. Repetition doesn't reinforce — it distorts. Repeating "ask first" or "do not mutate" causes unnecessary approval requests for safe, expected actions.
- Expose only tools relevant to the task; keep tool descriptions concise and precise.
- Keep examples and style guidance only when they encode a product requirement or correct a measured gap.
- A short instruction stating the principle beats a list of named cases. Trust it to generalize.

## Absolutes vs decision rules

Reserve `ALWAYS`, `NEVER`, `must`, and `only` for true invariants: safety rules, required output fields, actions that should never happen. For judgment calls — when to search, ask for clarification, use a tool, keep iterating — write decision rules instead:

```text
Ask for clarification only when the missing information would materially change
the answer or create meaningful risk, and keep any question narrow.
```

Legacy prompts lean on absolutes because earlier models drifted without them. Applied to judgment calls, absolutes produce rigid, over-cautious behavior.

## Stopping conditions

Autonomy needs stopping rules. Define what "enough" looks like:

```text
Resolve the user query in the fewest useful tool loops, but do not let loop
minimization outrank correctness, fallback evidence, calculations, or required
citations for factual claims.

After each result, ask: "Can I answer the user's core request now with useful
evidence and citations for the factual claims?" If yes, answer.
```

And a general evidence rule:

```text
Use the minimum evidence sufficient to answer correctly, cite it precisely,
then stop.
```

## Autonomy and approval boundaries

Frontier models are proactive and persistent. Define what level of action each request authorizes, so the model continues safe in-scope work without unnecessary pauses while stopping before external, destructive, costly, or scope-expanding actions. A compact policy is usually sufficient:

```text
For requests to answer, explain, review, diagnose, or plan, inspect the relevant
materials and report the result. Do not implement changes unless the request also
asks for them.

For requests to change, build, or fix, make the requested in-scope local changes
and run relevant non-destructive validation without asking first.

Require confirmation for external writes, destructive actions, purchases, or a
material expansion of scope.
```

Name safe local actions explicitly (reading files, inspecting logs, editing in-scope code, running tests). Keep the policy in one place and state each rule once.

## Output: length, structure, formatting

Frontier models are highly steerable on output format and structure. Use that control when it improves comprehension or product fit.

**Specify what a short answer must preserve, not just that it should be short.** Both vendors converge on this: instead of "be concise," state what to lead with, what to keep, and what to drop first. This gives the model a priority order: keep the content needed to complete the task, then remove lower-value detail.

```text
Lead with the conclusion. Include the evidence needed to support it, any
material caveat, and the next action. Omit secondary detail and repetition.

Keep all required facts, decisions, caveats, and next steps. Trim introductions,
repetition, generic reassurance, and optional background first.
```

**Readability beats brevity.** The way to keep output short is selectivity about content, not compression of the writing:

```text
Lead with the outcome. Your first sentence after finishing should answer "what
happened" or "what did you find": the thing the user would ask for if they said
"just give me the TLDR." Supporting detail and reasoning come after.

The way to keep output short is to be selective about what you include (drop
details that don't change what the reader would do next), not to compress the
writing into fragments, abbreviations, arrow chains like A → B → fails, or jargon.
```

**Formatting should serve comprehension.** Default to plain paragraphs; reach for headers, bullets, and tables when the answer needs comparison or ranking, or when the information would be harder to scan as prose:

```text
Let formatting serve comprehension. Use plain paragraphs as the default format
for normal conversation, explanations, reports, and technical writeups. Use
headers, bold text, bullets, and numbered lists sparingly — when the user
requests them, when the answer needs clear comparison or ranking, or when the
information would be harder to scan as prose. Respect formatting preferences
from the user.
```

## Grounding and evidence

**Make citation behavior part of the prompt** for grounded answers: define what needs support, what counts as enough evidence, and what to do when evidence is missing. Absence of evidence shouldn't automatically become a factual "no."

**For creative drafting** (slides, launch copy, summaries, talk tracks), distinguish source-backed facts from creative wording:

```text
Use retrieved or provided facts for concrete product, customer, metric, roadmap,
date, capability, and competitive claims, and cite those claims. Do not invent
specific names, metrics, roadmap status, customer outcomes, or product
capabilities to make the draft sound stronger. If there is little citable
support, write a useful generic draft with placeholders or clearly labeled
assumptions rather than unsupported specifics.
```

## Prompt the model to check its work

Give the model tools to validate its output, and ask for concrete validation:

```text
After making changes, run the most relevant validation available:
- targeted unit tests for changed behavior
- type checks or lint checks when applicable
- build checks for affected packages
- a minimal smoke test when full validation is too expensive

If validation cannot be run, explain why and describe the next best check.
```

For visual artifacts:

```text
Render the artifact before finalizing. Inspect the rendered output for layout,
clipping, spacing, missing content, and visual consistency. Revise until the
rendered output matches the requirements.
```

## Reasoning effort

Effort/reasoning settings are the primary intelligence–latency–cost control, and frontier models reason more efficiently than their predecessors: **re-test one level lower than your legacy setting before escalating.** Lower efforts on this generation often exceed the highest efforts on prior models. Reserve the top settings for measured quality gains on the hardest workloads.

## Auditing legacy prompts and skills

Work through an existing prompt or skill with these checks. Change one group at a time and re-test against representative tasks.

**Remove or rewrite:**

1. **Step-by-step process scripts** ("first do A, then B, then C…") → replace with the outcome, success criteria, and constraints. Keep ordering only where sequence is a genuine requirement.
2. **Absolutes on judgment calls** (`ALWAYS search before answering`, `NEVER proceed without asking`) → replace with decision rules stating when the action is warranted. Keep absolutes only for true invariants.
3. **Repeated instructions** — the same rule stated in multiple places or paraphrased for emphasis → state once, in the section where it belongs.
4. **Enumerated behavior lists** ("don't do X, don't do Y, don't do Z, …" for variants of one failure mode) → replace with one instruction stating the principle.
5. **Broad brevity commands** ("be concise", "keep it short") → replace with what a short answer must preserve and what to lead with.
6. **Adjective-only tone guidance** ("be friendly and professional") → replace with concrete writing choices.
7. **Compensatory hand-holding** — worked examples, reformulations, and warnings added because an older model kept failing → delete, re-test, and re-add only what a measured gap justifies.
8. **Excess tools and verbose tool descriptions** → expose only task-relevant tools; make descriptions state inputs, outputs, and error behavior precisely and briefly.

**Add if missing:**

9. **Success criteria** — what must be true before the final answer.
10. **Stopping conditions** — when the model should stop searching, iterating, or verifying and answer.
11. **An approval-boundary policy** — what the model may do without asking, and what requires confirmation, stated once.
12. **Evidence rules** — what needs citation, what counts as enough, what to do when evidence is missing.
13. **Validation instructions** — the concrete checks to run when the output is verifiable.
14. **Intent context** — why the task is being asked, who the output is for, what it enables.

**Then re-evaluate settings:** test one reasoning-effort level below your current setting; check whether the model's improved defaults have made any remaining style instructions redundant.
