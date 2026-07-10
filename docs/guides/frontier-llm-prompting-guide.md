# Frontier LLM Prompting Guide

A model-agnostic synthesis of the prompting guidance for the current frontier model generation: GPT-5.5, GPT-5.6 (sol/terra/luna), and Claude Fable 5 / Mythos 5. Use this guide to write new prompts and to audit existing prompts and skills for patterns that no longer help — or actively hurt — on these models.

Model-specific API details (reasoning parameters, tool-calling modes, caching, refusal handling) live in the source guides:

- [GPT-5.5 Prompting Guide](gpt-5.5-prompting-guide.md)
- [GPT-5.6 Prompting Guide](gpt-5.6-prompting-guide.md)
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

Removing repeated instructions, redundant examples, and verbose tool descriptions measurably improves both quality and cost. In OpenAI's internal coding-agent evals, leaner system prompts improved scores by roughly 10–15% while reducing total tokens by 41–66%. Anthropic reports the same direction: skills developed for prior models are often too prescriptive for Fable 5 and can degrade output quality.

To trim a working prompt without losing important guidance:

- Remove one group of instructions, examples, or tools at a time, then rerun the same evals.
- State each instruction once. Repetition doesn't reinforce — it distorts. Repeating "ask first" or "do not mutate" causes unnecessary approval requests for safe, expected actions.
- Expose only tools relevant to the task; keep tool descriptions concise and precise.
- Keep examples and style guidance only when they encode a product requirement or correct a measured gap.
- A short instruction stating the principle beats a list of named cases. Instead of enumerating "don't survey options you won't pursue, don't explain root causes at length, don't write heavily-structured PR descriptions...", write one brevity instruction and trust it to generalize.

## Absolutes vs decision rules

Reserve `ALWAYS`, `NEVER`, `must`, and `only` for true invariants: safety rules, required output fields, actions that should never happen. For judgment calls — when to search, ask for clarification, use a tool, keep iterating — write decision rules instead:

```text
Ask for clarification only when the missing information would materially change
the answer or create meaningful risk, and keep any question narrow.
```

Legacy prompts lean on absolutes because earlier models drifted without them. On frontier models, absolutes applied to judgment calls produce rigid, over-cautious behavior: the model searches when it already has the answer, asks when it should proceed, or refuses reasonable shortcuts.

## Stopping conditions and budgets

Autonomy needs stopping rules. Without them, capable models over-gather, over-verify, and over-iterate. Define what "enough" looks like:

```text
Resolve the user query in the fewest useful tool loops, but do not let loop
minimization outrank correctness, fallback evidence, calculations, or required
citations for factual claims.

After each result, ask: "Can I answer the user's core request now with useful
evidence and citations for the factual claims?" If yes, answer.
```

For retrieval-heavy tasks, add an explicit retrieval budget — a stopping rule for search:

```text
For ordinary Q&A, start with one broad search using short, discriminative
keywords. If the top results contain enough citable support for the core
request, answer from those results instead of searching again.

Make another retrieval call only when:
- The top results do not answer the core question.
- A required fact, parameter, owner, date, ID, or source is missing.
- The user asked for exhaustive coverage, a comparison, or a comprehensive list.
- A specific document, URL, email, meeting, record, or code artifact must be read.
- The answer would otherwise contain an important unsupported factual claim.

Do not search again to improve phrasing, add examples, cite nonessential
details, or support wording that can safely be made more generic.
```

And a general evidence rule:

```text
Use the minimum evidence sufficient to answer correctly, cite it precisely,
then stop.
```

To keep the model from overplanning when a task is ambiguous:

```text
When you have enough information to act, act. Do not re-derive facts already
established in the conversation, re-litigate a decision the user has already
made, or narrate options you will not pursue. If you are weighing a choice,
give a recommendation, not an exhaustive survey.
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

Frontier models can also occasionally take unrequested actions — drafting an email nobody asked for, creating defensive backups, fixing a problem the user was only describing. State the boundary:

```text
When the user is describing a problem, asking a question, or thinking out loud
rather than requesting a change, the deliverable is your assessment. Report your
findings and stop. Don't apply a fix until they ask for one. Before running a
command that changes system state (restarts, deletes, config edits), check that
the evidence actually supports that specific action.
```

To constrain over-engineering at high capability or effort levels:

```text
Don't add features, refactor, or introduce abstractions beyond what the task
requires. A bug fix doesn't need surrounding cleanup and a one-shot operation
usually doesn't need a helper. Don't design for hypothetical future
requirements: do the simplest thing that works well. Don't add error handling,
fallbacks, or validation for scenarios that cannot happen. Only validate at
system boundaries (user input, external APIs).
```

For checkpoints in long-running workflows, one principle beats an enumeration:

```text
Pause for the user only when the work genuinely requires them: a destructive or
irreversible action, a real scope change, or input that only they can provide.
If you hit one of these, ask and end the turn, rather than ending on a promise.
```

For fully autonomous pipelines where no user is watching, add:

```text
You are operating autonomously. The user is not watching in real time and cannot
answer questions mid-task, so asking "Want me to…?" or "Shall I…?" will block
the work. For reversible actions that follow from the original request, proceed
without asking. Before ending your turn, check your last paragraph. If it is a
plan, an analysis, a question, or a promise about work you have not done, do
that work now with tool calls. End your turn only when the task is complete or
you are blocked on input only the user can provide.
```

## Output: length, structure, tone, readability

Frontier models are highly steerable on format — and more concise by default than their predecessors. When migrating, check whether broad brevity instructions ("Be concise", "Keep it short") are still useful; they can now make responses too brief.

**Specify what a short answer must preserve, not just that it should be short.** This gives the model a priority order: keep the content needed to complete the task, then remove lower-value detail.

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

**Define tone as concrete writing choices, not adjectives.** Broad labels like "friendly" or "empathetic" are ambiguous:

```text
State the answer directly. If the user reports a problem, acknowledge the
specific issue before giving the next step. Use reassurance only when it is
relevant. Omit generic praise and unnecessary sign-offs.
```

**For editing and rewriting tasks, state what to preserve before asking for improvement:**

```text
Preserve the requested artifact, length, structure, and genre first. Quietly
improve clarity, flow, and correctness. Do not add new claims, extra sections,
or a more promotional tone unless explicitly requested.
```

## Personality and collaboration style

For customer-facing or conversational products, define two separate things, each briefly:

- **Personality** — how the assistant sounds: tone, warmth, directness, formality, humor, empathy.
- **Collaboration style** — how it works: when it asks questions, when it makes assumptions, how proactive it is, how it handles uncertainty and risk.

Example of a steady, task-focused assistant:

```text
You are a capable collaborator: approachable, steady, and direct. Assume the
user is competent and acting in good faith.

Prefer making progress over stopping for clarification when the request is
already clear enough to attempt. Ask for clarification only when the missing
information would materially change the answer, and keep any question narrow.

Stay concise without becoming curt. When correcting the user or disagreeing, be
candid but constructive. When an error is pointed out, acknowledge it plainly
and focus on fixing it.
```

Use personality to shape the experience — not to compensate for unclear goals or missing task instructions.

## Grounding, evidence, and honest reporting

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

**On long autonomous runs, ground progress claims against tool results.** In Anthropic's testing this nearly eliminated fabricated status reports:

```text
Before reporting progress, audit each claim against a tool result from this
session. Only report work you can point to evidence for; if something is not
yet verified, say so explicitly. Report outcomes faithfully: if tests fail, say
so with the output; if a step was skipped, say that; when something is done and
verified, state it plainly without hedging.
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

For long-running builds, separate fresh-context verifier subagents tend to outperform self-critique:

```text
Establish a method for checking your own work at an interval of [X] as you
build. Run this every [X interval], verifying your work with subagents against
the specification.
```

## Long-running and agentic patterns

**Preambles for perceived responsiveness.** In streaming, tool-heavy tasks, have the model send a short user-visible update before its first tool call:

```text
Before any tool calls for a multi-step task, send a short user-visible update
that acknowledges the request and states the first step. Keep it to one or two
sentences.
```

**Parallel subagents.** Frontier models dispatch subagents reliably. Provide explicit guidance on when delegation is appropriate and prefer asynchronous coordination over blocking on each subagent:

```text
Delegate independent subtasks to subagents and keep working while they run.
Intervene if a subagent goes off track or is missing relevant context.
```

**Memory across runs.** Models perform notably better when they can record and reference lessons from previous runs. A directory of Markdown files is enough:

```text
Store one lesson per file with a one-line summary at the top. Record corrections
and confirmed approaches alike, including why they mattered. Don't save what the
repo or chat history already records; update an existing note rather than
creating a duplicate; delete notes that turn out to be wrong.
```

**Final summaries after long unattended runs** need re-grounding, not continuation:

```text
Terse shorthand is fine between tool calls. Your final summary is different:
it's for a reader who didn't see any of that. Write it as a re-grounding — the
outcome first, then the one or two things you need from them, each explained as
if new. Drop the working shorthand: complete sentences, terms spelled out, no
labels you made up earlier.
```

**Verbatim mid-run delivery.** For long asynchronous agents, add a send-to-user tool so deliverables and progress updates reach the user exactly as written without ending the turn — and pair it with an instruction, since models rarely call such tools unprompted. See the [Fable 5 guide](fable-5-prompting-guide.md#create-a-send-to-user-tool) for the tool definition.

**Context-budget anxiety.** In very long sessions, avoid surfacing remaining-token countdowns to the model; if the harness must show them, add: "You have ample context remaining. Do not stop, summarize, or suggest a new session on account of context limits."

## Reasoning effort

Effort/reasoning settings are the primary intelligence–latency–cost control, and frontier models reason more efficiently than their predecessors: **re-test one level lower than your legacy setting before escalating.** Lower efforts on this generation often exceed the highest efforts on prior models. Reserve the top settings (`xhigh`/`max`, pro mode) for measured quality gains on the hardest workloads — and note that higher effort amplifies over-engineering and over-deliberation on routine tasks, which the boundary instructions above counteract.

## Suggested prompt structure

A starting skeleton for complex prompts. Keep each section short; add detail only where it changes behavior.

```text
Role: [1-2 sentences defining the model's function, context, and job]

# Personality
[tone, demeanor, and collaboration style]

# Goal
[user-visible outcome]

# Success criteria
[what must be true before the final answer]

# Constraints
[policy, safety, business, evidence, and side-effect limits]

# Output
[sections, length, and tone]

# Stop rules
[when to retry, fallback, abstain, ask, or stop]
```

## Auditing legacy prompts and skills

Work through an existing prompt or skill with these checks. Change one group at a time and re-test against representative tasks.

**Remove or rewrite:**

1. **Step-by-step process scripts** ("first do A, then B, then C…") → replace with the outcome, success criteria, and constraints. Keep ordering only where sequence is a genuine requirement.
2. **Absolutes on judgment calls** (`ALWAYS search before answering`, `NEVER proceed without asking`) → replace with decision rules stating when the action is warranted. Keep absolutes only for true invariants.
3. **Repeated instructions** — the same rule stated in multiple places or paraphrased for emphasis → state once, in the section where it belongs.
4. **Enumerated behavior lists** ("don't do X, don't do Y, don't do Z, …" for variants of one failure mode) → replace with one instruction stating the principle.
5. **Broad brevity commands** ("be concise", "keep it short") → replace with what a short answer must preserve, or delete if the model's default is already right.
6. **Adjective-only tone guidance** ("be friendly and professional") → replace with concrete writing choices.
7. **Compensatory hand-holding** — worked examples, reformulations, and warnings added because an older model kept failing → delete, re-test, and re-add only what a measured gap justifies.
8. **Excess tools and verbose tool descriptions** → expose only task-relevant tools; make descriptions state inputs, outputs, and error behavior precisely and briefly.
9. **"Show your reasoning" instructions** — prompts telling the model to echo or transcribe its internal reasoning as response text → remove (on Claude models these can trigger reasoning-extraction refusals; use the API's thinking output instead).

**Add if missing:**

10. **Success criteria** — what must be true before the final answer.
11. **Stopping conditions** — when the model should stop searching, iterating, or verifying and answer.
12. **An approval-boundary policy** — what the model may do without asking, and what requires confirmation, stated once.
13. **Evidence rules** — what needs citation, what counts as enough, what to do when evidence is missing.
14. **Validation instructions** — the concrete checks to run when the output is verifiable.
15. **Intent context** — why the task is being asked, who the output is for, what it enables.

**Then re-evaluate settings:** test one reasoning-effort level below your current setting; check whether the model's improved defaults have made any remaining style instructions redundant.
