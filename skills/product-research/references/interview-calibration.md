# Interview Calibration

Load this before composing Stage 1 questions. Do NOT use a generic template — generate per-category questions using the frame below, calibrated against the examples.

## The frame

Compose questions as if you were:

> **A trusted friend who has owned this category of product through multiple generations and also happens to understand how they're designed.** Your job is to ask the 4-6 questions that will most change the recommendation — questions that surface what this person actually needs vs. what they think they need. Skip questions whose answers don't change the shortlist. Ask the questions someone would only know to ask after getting it wrong once before.

Two load-bearing clauses in that frame:
- *"questions that will most change the recommendation"* — filters out ceremonial questions
- *"someone would only know to ask after getting it wrong once before"* — pushes toward regret-avoidance, non-obvious questions

## Rules

- **4-6 questions maximum.** Fewer is better if the category is simple (e.g., a kettle doesn't need 6 questions).
- **Never ask budget first.** Budget anchoring narrows options before the real needs are surfaced. Ask budget last or second-to-last.
- **Always allow a "help me decide" escape** on subjective questions. Users often don't know their own preferences for categories they haven't owned before.
- **Ask concrete situations, not abstract priorities.** "What have you replaced that you hated?" beats "rank reliability vs price vs features".
- **Ask about past experience with this category.** First-time buyers and replacement buyers need very different questions.
- **Skip questions your next subagent will answer.** Don't ask "what brands are reliable" — that's what research is for.

## Anti-patterns

| Don't ask | Why |
|---|---|
| "What features matter to you?" | Meaningless without category knowledge — the user doesn't know yet |
| "Rank reliability, performance, price, aesthetics" | People can't accurately rank in the abstract |
| "What's your budget?" as Q1 | Anchors the whole conversation to price before needs |
| "Do you want good quality?" | Ceremonial — no one says no |
| "What brands do you like?" | Shifts interview into research territory |
| "Do you care about energy efficiency?" | Too abstract; ask about usage patterns that imply it instead |

## Calibration examples

Three categories with strong question sets. Do not copy these verbatim for other categories — they show the *shape*, not the template.

### Example 1: Microwave

1. **Usage pattern** — "What do you actually use a microwave for, day to day? Just reheating, or do you cook or defrost in it too?"
   - *Why this and not "features?":* reheating-only vs active-cooking changes which power class and whether convection/grill matters
2. **Counter space and dimensions** — "Where does it live — countertop, shelf, or built-in? Any dimension constraint you're working around?"
   - *Why this:* appliance sizing is the silent dealbreaker; easier to catch now than after ordering
3. **Previous microwave experience** — "What did you have before? Anything about it you specifically want to fix or keep?"
   - *Why this:* previous-ownership data is the highest-signal input for "what you'll actually care about"
4. **Quietness sensitivity** — "How close is the microwave to where people sleep or work? Is a quiet beep-pattern important?"
   - *Why this:* open-plan apartments make microwave noise a real issue; cheap units are notoriously loud
5. **Interior vs exterior priorities** — "Do you care more about how it looks or how long it lasts? Many quiet, durable ones are a bit uglier; many sleek ones die after 3-4 years."
   - *Why this:* forces an explicit tradeoff rather than leaving it to research guess
6. **Budget** — "What's a range you're comfortable with? Or would you prefer I show the market spread and you decide?"

### Example 2: Mattress

1. **Sleep position for each sleeper** — "What position does each of you sleep in primarily — side, back, stomach, mix?"
   - *Why this:* position dominates firmness choice; side sleepers need more give at hips/shoulders
2. **Body weight ranges** — "Rough weight band for each sleeper — light (under 60kg), medium (60-85), heavier (85+)?"
   - *Why this:* a mattress that feels medium-firm to a 60kg person feels soft to a 90kg one
3. **Partner motion / heat** — "Does either of you wake the other moving? Does either of you sleep hot?"
   - *Why this:* motion isolation and heat are the two biggest sources of post-purchase regret
4. **Past mattresses owned** — "What's the last mattress you had that you liked, or hated? Do you know what it was?"
   - *Why this:* reference point lets research match/avoid a known feel
5. **Existing bed frame / slats** — "What are you putting it on — existing slatted frame, box spring, platform? Any gap in the slats?"
   - *Why this:* some mattresses void warranty if slat gap is too wide; constraint you can't fix post-purchase
6. **Trial/return policy tolerance** — "How long a home-trial window would make you comfortable deciding? 30 days? 100?"
   - *Why this:* in EU this varies dramatically by retailer; affects shortlist ordering

### Example 3: Vacuum

1. **Primary flooring** — "Mostly hard floors, mostly carpet, or mix? Any deep-pile rugs or area carpets?"
   - *Why this:* vacuum type (stick/canister/robot) and head design depend entirely on this
2. **Home size and layout** — "Roughly how big, and across how many levels? Stairs?"
   - *Why this:* corded vs cordless decision; robot viability; weight if stairs exist
3. **Pets / allergies** — "Any pets, shedding, or anyone with dust/pollen sensitivity?"
   - *Why this:* filtration class and hair-handling design become must-haves, not nice-to-haves
4. **Storage reality** — "Where would this actually live when not in use? Do you have a closet for it?"
   - *Why this:* stick vacuums that need wall-mount charging are useless if there's no wall to mount to
5. **How often do you vacuum now** — "Daily, weekly, when-you-notice? Would a robot change that, or do you actually want to do it yourself?"
   - *Why this:* different use pattern, different category entirely
6. **Budget** — "Range you're comfortable with, or prefer to see market spread first?"

## Second-round triggers

Fire a follow-up round via AskUserQuestion only when one of these conditions holds:

1. **Contradictory constraints** — e.g., "quiet" + "cheap" + "powerful" for a blender. Ask user to rank the top 2 of the three.
2. **Budget absent when needed** — user gave no budget signal AND the category has a wide price range (10x between entry and premium). Ask for a rough range or permission to show market spread instead.
3. **Critical category variable missed** — orchestrator judgment; rare. For a dishwasher, if built-in vs freestanding wasn't captured. For a camera, if the primary use case (stills vs video) wasn't captured.

Do NOT fire a second round for mild gaps. Preliminary phase research can fill those in. A second round is expensive in attention budget — use it only when the first round's output would lead to bad shortlisting.
