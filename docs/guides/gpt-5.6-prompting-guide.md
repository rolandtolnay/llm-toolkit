# GPT Prompting Guide

Consolidated from OpenAI's GPT-5.5 and GPT-5.6 prompting guides (https://developers.openai.com/api/docs/guides/prompt-guidance). API-specific implementation details (parameters, migration steps, tool-calling configuration) are omitted; the prompting guidelines and best practices are kept verbatim. Use this as the reference when writing skills and instructions for GPT models.

## Core principles

GPT works best when prompts define the outcome and leave room for the model to choose an efficient solution path. Compared with earlier models, you can often use shorter, more outcome-oriented prompts: describe what good looks like, what constraints matter, what evidence is available, and what the final answer should contain.

Avoid carrying over every instruction from an older prompt stack. Legacy prompts often over-specify the process because earlier models needed more help staying on track. That can add noise, narrow the model's search space, or lead to overly mechanical answers.

GPT can better infer the user's underlying goal and intended level of work from context, so you often do not need to prescribe every step. Continue to provide domain context, hard constraints, approval boundaries, and success criteria. Tell the model when an important ambiguity should trigger a question.

The patterns here are starting points. Adapt them to your product surface, tools, evals, and user experience goals.

## Favor leaner prompts

Removing repeated instructions and examples and simplifying tool descriptions can improve task performance and token efficiency. In a sample of OpenAI's internal coding-agent eval runs, configurations with leaner system prompts improved evaluation scores by roughly 10–15% while reducing total tokens by 41–66% and cost by 33–67%. Results will vary by workload, so treat these ranges as directional and validate changes on representative tasks from your own application.

To simplify prompts without losing important guidance:

- Start with a prompt and tool set that already works. Remove one group of instructions, examples, or tools at a time, then rerun the same evals.
- State each instruction once.
- Expose only tools relevant to the task, and keep their descriptions concise and precise.
- Keep examples and style guidance when they encode a product requirement or correct a measured gap.
- Track context both at the start of a run and as the conversation grows. Long sessions can amplify repeated prompt and tool content.

## Outcome-first prompts and stopping conditions

GPT is strongest when the prompt defines the target outcome, success criteria, constraints, and available context, then lets the model choose the path.

For many tasks, describe the destination rather than every step. This gives the model room to choose the right search, tool, or reasoning strategy for the task.

Prefer this:

```
Resolve the customer's issue end to end.

Success means:
- the eligibility decision is made from the available policy and account data
- any allowed action is completed before responding
- the final answer includes completed_actions, customer_message, and blockers
- if evidence is missing, ask for the smallest missing field
```

**Avoid unnecessary absolute rules.** Older prompts often use strict instructions like `ALWAYS`, `NEVER`, `must`, and `only` to control model behavior. Use those words for true invariants, such as safety rules, required output fields, or actions that should never happen. For judgment calls, such as when to search, ask for clarification, use a tool, or keep iterating, prefer decision rules instead.

Avoid this style of instruction unless every step is truly required:

```
First inspect A, then inspect B, then compare every field, then think through
all possible exceptions, then decide which tool to call, then call the tool,
then explain the entire process to the user.
```

Add explicit stopping conditions:

```
Resolve the user query in the fewest useful tool loops, but do not let loop minimization outrank correctness, accessible fallback evidence, calculations, or required citation tags for factual claims.

After each result, ask: "Can I answer the user's core request now with useful evidence and citations for the factual claims?" If yes, answer.
```

Define missing-evidence behavior:

```
Use the minimum evidence sufficient to answer correctly, cite it precisely, then stop.
```

## Personality and behavior

GPT's default style is efficient, direct, and task-oriented. This is useful for production systems: responses stay focused, behavior is easier to steer, and the model avoids unnecessary conversational padding.

For customer-facing assistants, support workflows, coaching experiences, and other conversational products, define both personality and collaboration style.

- **Personality** controls how the assistant sounds: tone, warmth, directness, formality, humor, empathy, and level of polish.
- **Collaboration style** controls how the assistant works: when it asks questions, when it makes assumptions, how proactive it should be, how much context it gives, when it checks work, and how it handles uncertainty or risk.

Keep both short. Personality instructions should shape the user experience. Collaboration instructions should shape task behavior. Neither should replace clear goals, success criteria, tool rules, or stopping conditions.

Example personality block for a steady task-focused assistant:

```
# Personality
You are a capable collaborator: approachable, steady, and direct. Assume the user is competent and acting in good faith, and respond with patience, respect, and practical helpfulness.

Prefer making progress over stopping for clarification when the request is already clear enough to attempt. Use context and reasonable assumptions to move forward. Ask for clarification only when the missing information would materially change the answer or create meaningful risk, and keep any question narrow.

Stay concise without becoming curt. Give enough context for the user to understand and trust the answer, then stop. Use examples, comparisons, or simple analogies when they make the point easier to grasp. When correcting the user or disagreeing, be candid but constructive. When an error is pointed out, acknowledge it plainly and focus on fixing it.

Match the user's tone within professional bounds. Avoid emojis and profanity by default, unless the user explicitly asks for that style or has clearly established it as appropriate for the conversation.
```

Example personality block for an expressive collaborative assistant:

```
# Personality
Adopt a vivid conversational presence: intelligent, curious, playful when appropriate, and attentive to the user's thinking. Ask good questions when the problem is blurry, then become decisive once there is enough context.

Be warm, collaborative, and polished. Conversation should feel easy and alive, but not chatty for its own sake. Offer a real point of view rather than merely mirroring the user, while staying responsive to their goals and constraints.

Be thoughtful and grounded when the task calls for synthesis or advice. State a clear recommendation when you have enough context, explain important tradeoffs, and name uncertainty without becoming evasive.
```

For more expressive products, add warmth, curiosity, humor, or point of view explicitly, but keep the block short. Use personality to shape the experience, not to compensate for unclear goals or missing task instructions.

## Define autonomy and approval boundaries

GPT can be proactive and persistent when carrying out multi-step tasks. Define what level of action each request authorizes so the model can continue safe, in-scope work without unnecessary pauses while stopping before external, destructive, costly, or scope-expanding actions.

A compact policy is usually sufficient:

```
For requests to answer, explain, review, diagnose, or plan, inspect the relevant
materials and report the result. Do not implement changes unless the request also
asks for them.

For requests to change, build, or fix, make the requested in-scope local changes
and run relevant non-destructive validation without asking first.

Require confirmation for external writes, destructive actions, purchases, or a
material expansion of scope.
```

Name safe local actions explicitly, such as reading files, inspecting logs, editing in-scope code, and running tests. Keep the policy in one place and state each rule once. Repeating instructions such as "ask first," "do not mutate," or "wait for approval" can cause unnecessary approval requests for safe, expected actions.

## Improve time to first visible token with a preamble

In streaming applications, users notice how long it takes before the first visible response appears. GPT may spend time reasoning, planning, or preparing tool calls before emitting visible text.

For longer or tool-heavy tasks, prompt the model to start with a short preamble: a brief visible update that acknowledges the request and states the first step. This can improve perceived responsiveness without changing the underlying task.

Use this pattern when the task may take more than one step, require tool calls, or involve a long-running agent workflow.

```
Before any tool calls for a multi-step task, send a short user-visible update that acknowledges the request and states the first step. Keep it to one or two sentences.
```

For coding agents that expose separate message phases, you can be more explicit:

```
You must always start with an intermediary update before any content in the analysis channel if the task will require calling tools. The user update should acknowledge the request and explain your first step.
```

## Formatting, response length, and style

GPT is highly steerable on output format and structure. Use that control when it improves comprehension or product fit. Describe the expected output shape, and reserve heavier structure for cases where it improves comprehension or your product UI needs a stable artifact.

GPT tends to be concise by default. Check whether broad brevity instructions such as "Be concise" or "Keep it short" are still useful. They may be unnecessary for some tasks and can sometimes make responses too brief. Keep them when they reliably produce the output your application needs.

Plain conversational formatting:

```
Let formatting serve comprehension. Use plain paragraphs as the default format for normal conversation, explanations, reports, documentation, and technical writeups. Keep the presentation clean and readable without making the structure feel heavier than the content.

Use headers, bold text, bullets, and numbered lists sparingly. Reach for them when the user requests them, when the answer needs clear comparison or ranking, or when the information would be harder to scan as prose. Otherwise, favor short paragraphs and natural transitions.

Respect formatting preferences from the user. If they ask for a terse answer, minimal formatting, no bullets, no headers, or a specific structure, follow that preference unless there is a strong reason not to.
```

Add explicit audience and length guidance:

```
Write for a senior business audience. Keep the answer under 400 words. Use short paragraphs and only include bullets when they improve scannability. Prioritize the conclusion first, then the reasoning, then caveats.
```

### Specify what a short answer must include

When a task calls for a shorter answer, identify the information the model must preserve and the detail it can omit. For example:

```
Lead with the conclusion. Include the evidence needed to support it, any material
caveat, and the next action. Omit secondary detail and repetition.

Keep all required facts, decisions, caveats, and next steps. Trim introductions,
repetition, generic reassurance, and optional background first.
```

This gives the model a clear priority order: preserve the content needed to complete the task, then remove lower-value detail.

### Define the tone

Broad labels such as "friendly" or "empathetic" can be ambiguous. Describe the writing choices that define your product's tone, such as how directly to state the answer, when to acknowledge a problem, and whether reassurance or a sign-off is appropriate.

```
State the answer directly. If the user reports a problem, acknowledge the
specific issue before giving the next step. Use reassurance only when it is
relevant. Omit generic praise and unnecessary sign-offs.
```

### Preserve before improving

For editing, rewriting, summaries, or customer-facing messages, tell the model what to preserve before asking it to improve style. This pattern is useful when you want polish without expansion.

```
Preserve the requested artifact, length, structure, and genre first. Quietly improve clarity, flow, and correctness. Do not add new claims, extra sections, or a more promotional tone unless explicitly requested.
```

## Grounding, citations, and retrieval budgets

For grounded answers, citation behavior should be part of the prompt. Define what needs support, what counts as enough evidence, and how the model should behave when evidence is missing. Absence of evidence shouldn't automatically become a factual "no."

### Add an explicit retrieval budget

Retrieval budgets are stopping rules for search. They tell the model when enough evidence is enough.

```
For ordinary Q&A, start with one broad search using short, discriminative keywords. If the top results contain enough citable support for the core request, answer from those results instead of searching again.

Make another retrieval call only when:
- The top results do not answer the core question.
- A required fact, parameter, owner, date, ID, or source is missing.
- The user asked for exhaustive coverage, a comparison, or a comprehensive list.
- A specific document, URL, email, meeting, record, or code artifact must be read.
- The answer would otherwise contain an important unsupported factual claim.

Do not search again to improve phrasing, add examples, cite nonessential details, or support wording that can safely be made more generic.
```

## Creative drafting guardrails

For drafting tasks, tell the model which claims must come from sources and which parts may be creatively written. This is especially important for slides, launch copy, customer summaries, talk tracks, leadership blurbs, and narrative framing.

```
For creative or generative requests such as slides, leadership blurbs, outbound copy, summaries for sharing, talk tracks, or narrative framing, distinguish source-backed facts from creative wording.

- Use retrieved or provided facts for concrete product, customer, metric, roadmap, date, capability, and competitive claims, and cite those claims.
- Do not invent specific names, first-party data claims, metrics, roadmap status, customer outcomes, or product capabilities to make the draft sound stronger.
- If there is little or no citable support, write a useful generic draft with placeholders or clearly labeled assumptions rather than unsupported specifics.
```

## Prompt the model to check its work

Give GPT access to tools that let it check outputs when validation is possible.

For coding agents, ask for concrete validation commands:

```
After making changes, run the most relevant validation available:
- targeted unit tests for changed behavior
- type checks or lint checks when applicable
- build checks for affected packages
- a minimal smoke test when full validation is too expensive

If validation cannot be run, explain why and describe the next best check.
```

For visual artifacts, ask for inspection after rendering:

```
Render the artifact before finalizing. Inspect the rendered output for layout, clipping, spacing, missing content, and visual consistency. Revise until the rendered output matches the requirements.
```

For engineering and planning tasks, make implementation plans traceable:

```
For implementation plans, include:
- requirements and where each is addressed
- named resources, files, APIs, or systems involved
- state transitions or data flow where relevant
- validation commands or checks
- failure behavior
- privacy and security considerations
- open questions that materially affect implementation
```

## Frontend engineering and visual taste

For frontend work, refer to OpenAI's [example instructions](https://developers.openai.com/api/docs/guides/frontend-prompt) for practical ways to steer UI quality. They cover product and user context, design-system alignment, first-screen usability, familiar controls, expected states, responsive behavior, and common generated-UI defaults to avoid, such as generic heroes, nested cards, decorative gradients, visible instructional text, and broken layouts.

## Suggested prompt structure

Use this structure as a starting point for complex prompts. Keep each section short. Add detail only where it changes behavior.

```
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
