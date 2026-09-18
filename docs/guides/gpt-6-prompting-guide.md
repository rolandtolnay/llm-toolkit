---
latestModelInfo:
  model: gpt-6-astra
  migrationGuide: /api/docs/guides/latest-model/gpt-6-astra.md#migration-quickstart
  promptingGuide: /api/docs/guides/latest-model/gpt-6-astra.md#prompting-best-practices
---

# Using GPT-6 Astra

> For the complete documentation index, see [llms.txt](/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

## Introduction

GPT-6 Astra is our most intelligent model yet, with state-of-the-art performance in computer use, browsing, software engineering, science, and professional work. It excels at carrying out multistep workflows across code, browsers, and professional software. In [several evaluations](https://openai.com/index/gpt-6-astra/), Astra achieves stronger results while using substantially fewer output tokens—delivering a lower estimated API cost per task than earlier models despite its higher per-token pricing.

GPT-6 Astra is also our most aligned model yet. It excels at exercising care, respecting task boundaries, and communicating transparently. When instructions leave room for interpretation, it uses the context it has to fill in routine gaps and asks focused questions when the answer could change the outcome. It incorporates new requirements, changes course when asked, and answers side questions without losing track of the broader task.

To build with Astra, set `model` to `gpt-6-astra` in a [Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses) request.

<a id="gpt-6-astra-what-is-new" className="scroll-mt-[110px]"></a>

## What's new

- **Async tool calling:** GPT-6 Astra can continue reasoning, call other tools, or answer independent parts of a request while your application runs a tool. Set `async: true` on a function or custom tool and return its result when ready using the original `call_id`. Your application still executes the tool and manages pending work. See [Async tool calling](https://developers.openai.com/api/docs/guides/async-tool-calling) for basic usage and a developer-defined wait-tool pattern.
- **Mid-turn steering:** Send additional user instructions while GPT-6 Astra is working, such as a correction or a change in requirements. Over a WebSocket connection, the Responses API preserves completed work and includes the update in a continuation. See [Mid-turn steering](https://developers.openai.com/api/docs/guides/steering) for the event flow and tool-result handling.
- **Change reasoning mid-conversation while preserving cache:** Add a `configuration_update` input item to increase reasoning effort for difficult work or reduce it for routine follow-ups without rewriting the original prompt prefix. The updated reasoning effort applies until another `configuration_update` input item overrides it. See [Change reasoning mid-conversation](https://developers.openai.com/api/docs/guides/reasoning#change-reasoning-mid-conversation) for examples and compatibility.
- **Misalignment monitoring:** As part of our [strengthened safeguards](https://openai.com/index/path-to-astra/) for GPT-6 Astra, our systems asynchronously monitor for misalignment and trigger alerts when necessary. See [Misalignment monitoring](https://developers.openai.com/api/docs/guides/safety-checks/misalignment-monitoring) for more information.
- **Limitations:** GPT-6 Astra does not support the `none` reasoning effort. [Fast mode](https://developers.openai.com/api/docs/guides/fast-mode) is unavailable for GPT-6 Astra with EU data residency.

GPT-6 Astra also supports the existing API capabilities available with GPT-5.6, including [computer use](https://developers.openai.com/api/docs/guides/tools-computer-use), [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [streaming](https://developers.openai.com/api/docs/guides/streaming-responses), [Programmatic Tool Calling](https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling), [multi-agent orchestration](https://developers.openai.com/api/docs/guides/responses-multi-agent), [prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching), [persisted reasoning](https://developers.openai.com/api/docs/guides/reasoning#preserve-reasoning-across-calls), [compaction](https://developers.openai.com/api/docs/guides/compaction), and [pro mode](https://developers.openai.com/api/docs/guides/reasoning#reasoning-mode).

## Prompting best practices

GPT-6 Astra is more intelligent and capable than prior models like GPT-5.6 Sol, and also exhibits behavior patterns that can be optimized through prompting the model for your use case.

### GPT-6 Astra behavior

- [Initiative and follow-through](#initiative-and-follow-through) – The model is designed to be a more effective collaborator and is thus more likely to ask the user a question when additional input could materially change the result. This can cause it to stop when the user may expect it to make reasonable assumptions and persist.
- [Instruction following](#instruction-following) – GPT-6 Astra is stronger at general instruction following than our previous models, giving you greater control over its behavior. It can be more sensitive to instructions contained in skills and other files, such as `AGENTS.md`. We **strongly recommend** auditing skills and other files accessible to your model for instructions that could influence its behavior. See [Rethinking skills and prompts](#rethinking-skills-and-prompts-for-gpt-6-astra) for what to look for.
- [Personality and writing style](#personality-and-writing-style) – The model tends toward detailed, formatted responses and may use recurring phrases across sessions. Specify the writing style and structure your application needs.
- [Subagent delegation](#subagent-delegation) – The model may delegate less often than desired for your workflow. Specify when and how much it should use subagents for parallel work.
- [Testing and verification](#testing-and-verification) – For coding tasks, the model tends to be thorough in testing before considering a task complete. For smaller tasks, this can result in broader tests than the task requires.

### Initiative and follow-through

GPT-6 Astra is generally better than GPT-5.6 Sol and earlier models at staying coherent during long tasks. It is also more likely to ask for clarification where earlier models would make assumptions.

To encourage more autonomous work, start with this prompt:

```text
You should infer the user's intent and task scope from the instructions and prior conversation context. Your job is to bias towards action and carry the user's intended task to completion.

When the user expresses intent to perform new work or fix an existing issue, persist until the user's intended goal is complete. Progress autonomously towards the user's goal (e.g. creating isolated worktrees / checkouts if needed, resolving merge conflicts, read-only actions, creating draft PRs etc.) unless they are clearly destructive or irreversible.
```

When the user’s intent is unclear, the model is more likely to ask the user for clarification to proceed. Prompt the model to follow through if the user’s prompt implies authorization:

```text
When the user's prompt indicates a request for action, such as "can you...", "I want to...", "help me..." and similar expressions, treat these as instructions to do the work and take action. Do not stop at acknowledging capability (e.g. "Yes…"), proposing a plan, or offering to continue. Do not settle for a partial or "helpful enough" solution that does not fully satisfy the user's task to save time, effort or tokens. If a task requires sustained work, complete all the necessary work until the intended outcome is fulfilled.
```

Prompt the model to ask for approval only after preparing a concrete, reviewable result. This avoids blocking the task before the model has done the work it can, and often leads to quicker task completion.

```text
Before asking the user clarifying questions, you should complete the work that is already authorized from context and necessary to make the proposed action concrete and reviewable. The user should be approving a concrete, reviewable result. For example, before deploying a change, writing to an external application, merging a PR or publishing a site, do all the required work first so that user approval is the final step. You don't need user permission for reversible tasks, read-only actions, reviews or fixes, or anything for which authorization is provided earlier in the session or strongly implied from the task instruction.

Do not introduce unsolicited warnings, disclaimers, approval flows, or safety/compliance checklists due to hypothetical risk.
```

The model also likes to ask non-blocking questions as it’s working by default, so adjust these prompts to match the level of autonomy your application needs.

### Instruction following

GPT-6 Astra is better able to follow longer instructions, but can also be more sensitive to information in context. For example, unclear or conflicting guidance in a skill file may cause the model to pause and block work early. Make the priority of user instructions and skills explicit.

```text
The user's instructions take precedence over guidelines provided in a skill. If explicit user instructions conflict with a skill's instructions, prioritize the user's instructions.
```

Asking the model to identify the skill and instruction that caused it to pause or change direction can also be effective in providing transparency into model behavior.

```text
If a skill causes you to ask for permission or confirmation, pause, leave requested work unfinished, or diverge from the user's intent, name and link to the exact SKILL.md file you read, quote the relevant instruction, and briefly explain how it applies. Distinguish explicit skill requirements from your interpretation of guidelines.
```

Use this prompt to find silent and conflicting guidance when your application loads many skills and instruction files such as `AGENTS.md`.

### Personality and writing style

GPT-6 Astra tends to use lists, tables and Markdown to make responses scannable. If your application needs prose with less formatting, specify that preference.

```text
Default to using clear, concise paragraphs, each developing one main idea. Use lists only when the information is genuinely parallel, sequential, or easier to compare, and avoid nested lists unless the hierarchy cannot be expressed clearly in prose. Use plain, simple language: familiar words, concrete examples, and precise verbs. Prefer active voice and direct statements.

Make sure to state the main point clearly and early, then develop it with the explanation and detail the reader needs. Let each sentence build on what came before. Develop the points that matter and provide enough support to be useful.
```

For technical communication, the following prompt helps strike a balance between using clear, coherent language while remaining domain appropriate:

```text
Use plain language over jargon, and reference technical details only to the degree that it helps illustrate an idea or your work to the user. Communicate complex concepts in a clear and cohesive manner, and calibrate your writing to the level of background knowledge assumed from the user's prompt and context.
```

To reduce jargon and stock phrases in writing, start with this prompt:

```text
Avoid using slop words or phrases like "Bottom Line:" in conclusions, "delve," "foster," "leverage," "it's worth noting," "importantly," "Question? Answer." or "This isn't about X. It's about Y.", "genuinely" or hyphenated compound descriptions and adjectives. Do not use concluding summary statements such as "In short:..", "The simplest mental model is:...".

State the intended action directly. Avoid adding what you won't do, what will remain unchanged, or how you'll separate or categorize results. Do not use contrastive framing such as "X, not Y" or "X—not Y" that introduces an unprompted alternative that the user didn't ask about. Avoid invented compound labels like "exact-head checks" and "editorial-row layouts", vague qualifiers, and canned transitions; use plain verbs and prepositions to state the actual relationship directly.
```

### Subagent delegation

GPT-6 Astra is trained to be able to divide and delegate work to subagents that work in parallel. If you are implementing a multi-agent system in your harness, use the following prompt to tune how much GPT-6 Astra should delegate work:

```text
If at any point you can parallelize work by delegating tasks to another agent (no matter if you are the root or subagent), you should do so using collaboration tools if it could save time or improve quality.
```

Messages between agents may contain grammar or spacing errors. Use this prompt to make inter-agent messages easier to read:

```text
Messages that you send to other agents and your final answer may be read by a human, so ensure they are legible. Always put proper spaces between words and/or numbers.
```

The model tends to respond well to prompting for how and when it should delegate work to subagents, so tune this behavior to fit with your harness and multi-agent implementation.

### Testing and verification

For coding tasks, calibrate how much testing and verification a change requires. This can help avoid unnecessary tests or repeated checks for small changes.

```text
Do not write tests for reversible, low-impact changes that mirror the implementation. If you do choose to verify your work with tests, make sure that the tests are meaningful and necessary to verify implementation.

Run tests appropriate to the change and complete required checks. Once those pass, broaden or repeat testing only when new changes, failures, or unresolved concerns justify it; otherwise, continue toward completing the task.
```

## Migration quickstart

### Migrate with Codex

Codex can apply the recommended changes in this guide with the [OpenAI Docs skill](https://github.com/openai/skills/tree/main/skills/.curated/openai-docs).

```text
$openai-docs migrate this project to GPT-6 Astra
```

To use this skill in other coding agents, download it from the [OpenAI skills repository](https://github.com/openai/skills/tree/main/skills/.curated/openai-docs).

### Update API and model parameters

Set `model` to `gpt-6-astra`, then check the following:

- **Reasoning effort:** If you currently use `none` or `minimal`, start with `low` and compare results. Otherwise, preserve your current effective [reasoning effort](https://developers.openai.com/api/docs/guides/reasoning#reasoning-effort). Use `reasoning.effort` in Responses or `reasoning_effort` in Chat Completions.
- **Tool calling:** Use the [Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses#migrating-from-chat-completions). GPT-6 Astra supports Chat Completions, but tool calling requires Responses.
- **Unsupported parameters:** Remove `temperature`, `top_p`, and `top_logprobs`. For Chat Completions, also remove `logprobs`. For Responses, remove `message.output_text.logprobs` from `include`.
- **Fast mode:** For EU data residency, use Standard processing. GPT-6 Astra does not support `service_tier: "fast"` or `service_tier: "priority"` with EU data residency. Fast mode for GPT-6 Astra does not include a latency SLA. See [Fast mode compatibility](https://developers.openai.com/api/docs/guides/fast-mode#is-fast-mode-compatible-with-data-residency-zero-data-retention-and-a-baa).
- **Changing reasoning effort:** If your application changes effort between responses, use `configuration_update` items in standard, single-agent requests. Keep request-level `reasoning.effort` unchanged to preserve the prompt prefix for caching. Check the [compatibility limits](https://developers.openai.com/api/docs/guides/reasoning#change-reasoning-mid-conversation) before adopting this feature.
- **Prompt caching:** When migrating from GPT-5.5 or earlier, replace `prompt_cache_retention` with `prompt_cache_options.ttl` set to `"30m"`. Review the [prompt caching changes](https://developers.openai.com/api/docs/guides/prompt-caching#summary-of-model-differences), including cache boundaries and cache-write billing.
- **Unnecessary approval pauses:** If you run into issues where the model keeps asking for approval before proceeding, use the [initiative and follow-through guidance](#initiative-and-follow-through) to prompt for more autonomous execution. See the rest of [Prompting best practices](#prompting-best-practices) for guidance on instruction following, writing style, subagent delegation, and testing.

## Rethinking skills and prompts for GPT-6 Astra

Coding agents have come a long way, and best practices are changing fast. With more capable models, what used to require a lot of handholding and scaffolding no longer does.

If you've been using agents like Codex for your projects over the last year, you've likely accumulated a lot of instructions as you worked to steer the models toward good outcomes. With each release, it's been worth revisiting those assumptions, but with GPT-6 Astra, it's more important than ever.

These instructions can take many forms: skills, `AGENTS.md`, and your task prompts are all shaping how the model gets work done.

### Better skills

Skills are essentially prompts stored as Markdown files that can also be packaged with resources and bundled scripts. Generally, they are most useful for guidance around a specific workflow, or when using certain apps.

People now default to packaging a lot of skills into their projects, and each skill comes with a name and description that are loaded into the model's context so it knows when to use them. But many descriptions are far too long, and when you add too many skills, Codex starts shortening their descriptions to fit. The model ends up seeing less of each description, making it harder to know which skill to pick.

What's worse is that descriptions can often contradict each other or over-emphasize when skills should be used, leading the model to load instructions that don't actually help the task.

A common workflow to create skills is to use the `$skill-creator` skill. We recently updated its guidance to help mitigate many of the failure modes we've seen in practice.

First, skill descriptions should be as short as possible while making it clear when the model should use them:

> Illustration: Skill descriptions. Bad: Create and validate Postgres schema migrations. Use when working with databases, queries, models, or persistence. Good: Create and validate Postgres schema migrations. Use when adding or changing a migration, or reviewing its rollout.

_Here, the bad skill description can push the model to use it anytime it touches anything related to a database, rather than only when it has to handle a migration._

Second, one of the key markers of a useful skill is progressive disclosure. Reading a skill takes up context, bringing you closer to compaction and introducing guidance that may not apply to the task. For skills with multiple workflows, make the root document a minimal router that points to supporting docs and scripts. Give the model enough guidance to know where to look without forcing it to read things that don't matter in the moment.

Third, many skills were written as elaborate itineraries or recipes. Models have gotten much better at understanding nuance and ambiguity, so overly specific guidance can now hinder results where it previously helped.

Repository skills also guide other contributors' agents, which may use different models. Guidance that helps Sol or Luna may overconstrain GPT-6 Astra, so consider which models will use the instructions you leave behind.

### Up-to-date AGENTS.md

Because [`AGENTS.md`](https://agents.md) applies whenever the model works in your repository, you should frequently revisit each instruction and ask yourself whether it's still needed.

Requiring a stack of docs or a full repo map before every edit is excessive for a typo fix. GPT-6 Astra can work out what it needs to read without being pushed to review the whole project before every change.

> Illustration: AGENTS.md context. Bad: Before every edit, read architecture.md, database.md, and deployment.md. Good: Use architecture.md for service boundaries, database.md for schema changes, and deployment.md when preparing a deployment.

_Prompting the model to read files before every edit is a great way to burn context and slow work down. Pointing to some docs can still be helpful, however, so long as it is contextual. Be sure to keep your docs updated too!_

Previous models needed encouragement to run tests and check their work. GPT-6 Astra does that on its own, so the same instructions can lead to unnecessary testing.

You can use `AGENTS.md` to give it permission for a specific workflow you know is safe, such as a local test suite:

> The local tests use disposable fixtures and have no production access. Run them, fix failures caused by the requested change, and rerun affected tests without asking for approval at each step.

### Decision boundaries

Pay careful attention to how you describe boundaries. If a previous model did things on your behalf without permission, you may have added strong language to make it ask first. That can be useful, but GPT-6 Astra has much better judgment and will not perform tasks unless it knows it is safe – so you should treat it as such.

Consider updating that language: Astra could take it too seriously and may stop work where you'd actually be happy for it to continue.

### Persistence

GPT-6 Astra may reach a first implementation and come back for your review while there's still work to do.

This is where it helps to define completion before starting. If the task includes getting the implementation running, inspecting the result, and fixing what fails, make that part of the request. A requirement to stop for review after the first implementation will pull the model toward an earlier stopping point, so check whether that's a decision you actually need to make.

If you want it to keep exploring beyond a first pass, say what you want explored and where it should stop. The prompts in [Initiative and follow-through](#initiative-and-follow-through) encourage this more autonomous behavior.

A new model is a good opportunity to clean your house, but you don't need to review everything manually: ask GPT-6 Astra to do an audit based on what was discussed in this section, then go build something you wouldn't have attempted before!