---
description: Explain the current issue, options, or behavior so I can make a confident decision
argument-hint: [topic or leave blank for current context]
---

<objective>
The user is signaling they need a deeper, clearer explanation of what's being discussed. They are a senior engineer (10 years, primarily Flutter/Dart, some TypeScript/Node.js) working across codebases in unfamiliar stacks. They understand software engineering principles deeply but may lack framework-specific knowledge, project history, or business context for the codebase they're currently in.

Explain $ARGUMENTS (or the current discussion if no arguments provided) so the user can make a confident, informed decision.
</objective>

<confusion_shapes>
Detect which shape of confusion is active from conversation context. There may be more than one.

1. **"What is happening and why?"** — User sees behavior (error, bug, CI failure, unexpected output) but can't trace the cause. They need a cause chain, not a code dump.

2. **"Which option should I pick?"** — User is presented with alternatives but can't evaluate trade-offs. They need consequences of each option, not implementation details of each option.

3. **"Is this important?"** — User sees an issue but can't gauge severity. They need impact assessment: what breaks if ignored, what's the blast radius, is this a real problem or noise.

4. **"How does this piece fit?"** — User lacks the architectural or business context to evaluate a change. They need the system map: what connects to what, why this component exists, what depends on it.
</confusion_shapes>

<process>
1. Identify the topic. Use $ARGUMENTS if provided, otherwise extract from conversation context.

2. Detect which confusion shape(s) are active.

3. Investigate. Read relevant code, check git history, trace dependencies — gather what's needed to explain clearly. Do not skip this step.

4. Explain using the layered structure below.

5. End with a confidence check using AskUserQuestion.
</process>

<explanation_structure>
## Layer 1: Plain-language summary (always)
One paragraph. State what's happening, why it matters, and — if a decision is needed — which option you'd recommend and why. No jargon. No code. A product manager should be able to follow this.

## Layer 2: Familiar-ground anchor (when a good parallel exists)
Connect the concept to something the user already knows well. Prefer parallels from:
- Flutter/Dart (strongest — widgets, state management, build context, isolates, streams, provider/riverpod)
- Mobile development patterns (lifecycle, navigation, dependency injection, reactive UI)
- General software engineering (design patterns, SOLID, system design, API contracts)
- TypeScript/Node.js (moderate familiarity)

**Critical:** If no honest parallel exists, say so explicitly: "This doesn't have a clean Flutter equivalent — here's the concept on its own terms." A misleading analogy is worse than no analogy.

## Layer 3: Specifics (only what's needed for the decision)
Concrete details — but only the ones that change the decision. Show the relevant code snippet, the config that matters, the specific trade-off. Skip implementation details the user doesn't need to evaluate.

## Layer 4: Confidence check (always)
Use AskUserQuestion to ask whether they have enough context to proceed, or if any part needs deeper explanation.
</explanation_structure>

<anti_patterns>
- Do NOT lead with framework-specific implementation details. Lead with system behavior and consequences.
- Do NOT present raw code and expect the user to parse it. Narrate what the code does in plain language first.
- Do NOT force analogies. When a concept is genuinely novel, explain it from scratch rather than mapping it to something it only superficially resembles.
- Do NOT give exhaustive explanations of parts the user didn't ask about. Stay focused on what's needed for the decision at hand.
</anti_patterns>

<success_criteria>
- User can articulate back what the issue is and why it matters
- If options were presented, user understands the concrete consequences of each — not just the technical differences
- Explanation anchors to concepts the user already holds, without forcing false parallels
- No unnecessary implementation details — only what changes the decision
- Confidence check asked before proceeding
</success_criteria>
