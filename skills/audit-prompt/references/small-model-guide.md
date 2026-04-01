# Small and Local Model Prompting Guide

Principles for prompting small models (sub-10B parameters — Qwen 4B, Phi-3 mini, Gemma 2B, Llama 3.2 3B, quantized variants). These models follow a different optimization curve than frontier models.

---

## Core Difference

The "start minimal, add for failures" principle **inverts** for small models — they fail with sparse prompts and succeed with well-anchored ones. The goal is not fewer tokens but the **right** tokens.

A frontier model can infer intent from a sparse prompt; a small model given the same sparse prompt may drift into planning loops, reasoning spirals, or generic output. Small models are more sensitive to prompt content — they degrade faster with irrelevant content, yet they also need more anchoring to stay on task.

---

## Key Principles

- **Role-setting is load-bearing, not waste.** "You are a slug generator" prevents a small model from entering conversational or planning mode. On a frontier model this is unnecessary; on a 4B model it's the difference between a clean output and a 50-token reasoning spiral.
- **Goal-framing outperforms role-framing.** A/B testing on Qwen3.5-4B showed that "You summarize coding sessions for a searchable index. Future AI assistants will search these summaries..." (goal-oriented) outperformed "You are a session summarizer" (role-only) on searchability, conciseness, and "why" capture. Goal-framing tells the model both what it IS and what the output is FOR, producing output optimized for the stated use case. When the downstream consumer is known, name it in the prompt.
- **Examples are the primary instruction mechanism.** Small models pattern-match from examples far more reliably than they follow abstract directives. "Structure: action-target-detail" is noise to a 4B model; three concrete examples showing that structure are the actual instruction. Prefer 2-3 brief, high-quality examples over structural descriptions.
- **Abstract directives have lower ROI.** Instructions like "capture WHAT is being done and WHERE" require reasoning to interpret. Small models may ignore them entirely or interpret them unpredictably. Convert abstract directives to concrete examples or remove them.
- **Completion prompts anchor output format.** Ending the user message with an incomplete pattern (e.g., "Output only the slug:") forces the model to complete the pattern rather than explain it. This is more reliable than instructing "output only X" for small models.
- **Sampling parameters are half the equation.** For constrained generation tasks (short outputs, specific formats), prompt instructions alone are insufficient. Temperature, presence_penalty, repeat_penalty, and num_predict must be tuned together with the prompt. An audit of a small-model prompt that ignores sampling parameters is incomplete.
- **Very low temperature improves consistency without sacrificing quality ceiling.** A/B testing on Qwen3.5-4B showed temperature 0.1 produced near-deterministic output while the best individual outputs matched temperatures 0.3 and 0.5. For production summarization/extraction tasks where reproducibility matters, temperature 0.1 is preferable.
- **Input metadata that creates "gaps to fill" triggers confabulation.** Including structured metadata like tool usage counts (`Read:4, Edit:2, Bash:3`) caused 27% hallucination in Qwen3.5-4B — the model tried to narrativize what the tools did and invented plausible but false details. Removing tool counts dropped hallucinations to 0%. Only include input fields the model can meaningfully reason about.

---

## Anti-Patterns Caveat

Anti-pattern examples can backfire on small models. A/B testing on Qwen3.5-4B showed that adding "Bad example: 'Modified auth/session.ts to fix the timeout issue.' — This just restates file names. Capture WHY and HOW instead" actually *increased* hallucination — the instruction to "capture HOW" pushed the model to fabricate implementation details not present in the input. The prompt without the anti-pattern performed better.

**Rule:** For small models, anti-patterns that implicitly instruct the model to add information ("capture WHY and HOW") are riskier than anti-patterns that instruct it to remove information ("don't list file names").

---

## The Reliability Test (Small Model Variant)

Instead of "does removing this degrade output?", ask: **"Does this instruction produce a behavioral change that the examples alone don't cover?"**

- If the examples already demonstrate the pattern → the abstract instruction is redundant for this model class
- If the instruction adds a behavioral dimension not shown in examples → it earns its place

---

## Audit Behavior Overrides

When auditing a prompt targeting a small/local model, apply these instead of the main guide's frontier-oriented defaults:

- Do NOT flag role-setting as budget waste
- Do NOT recommend reducing examples below 2-3
- Weight examples as the primary instruction mechanism over abstract directives
- Note when sampling parameters should be reviewed alongside the prompt
- Apply the small-model reliability test variant (above) instead of the standard one
