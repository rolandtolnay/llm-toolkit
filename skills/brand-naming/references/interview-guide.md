# Interview Guide — Intake and Strategy

Two interactive rounds. Round 1 gathers facts. Round 2 is the strategic core of the entire
pipeline — everything downstream (territories, team briefs, scoring) derives from it. Do not rush
Round 2 or reduce it to a form-filling exercise; it is a conversation.

AskUserQuestion accepts max 4 questions per call. Batch accordingly. For questions where the
user's own words matter (product description, definition of winning), prefer free-form
conversation over multiple-choice — options bias answers toward comfort.

## Round 1: Intake

Cover these, skipping anything already known from conversation context or the project's
PROJECT.md / CONTEXT.md (check for them first — they often answer half of this round):

1. **What is it?** One-paragraph description in the user's own words. What does it do, for whom?
2. **Naming subject type**: company | product | app | feature | rename of existing brand.
   A company name must stretch across future products; a product name can be sharper and more
   specific. A rename triggers the rename branch below.
3. **Category and competitors** the user already knows about (the landscape research will go
   deeper — this seeds it).
4. **Audience**: who buys, who uses, B2B or consumer, sophistication level.
5. **Markets and languages**: where will this launch? Which languages must the name survive in?
   (Drives linguistic screening and CVCV/pronounceability weighting.)
6. **Hard constraints**: words or associations to avoid, legal entity name already fixed?,
   domain requirements (is exact-match .com a must-have or nice-to-have?), tone boundaries.
7. **Existing candidates**: any names the user already has or loves/hates. Capture them with the
   *reason* for the reaction — these are calibration data, and existing candidates enter the
   convergence funnel to be scored honestly alongside generated names.

### Rename branch

If the subject is a rename, apply Placek's rename framework before proceeding:

- Bad names create friction daily; the right name compounds — the longer it's in market, the more
  advantage. So the question is friction vs. re-education cost.
- The fear of losing equity/momentum is, per Lexicon's experience, unsupported in practice —
  *provided* the relaunch is done with enthusiasm and a story: "we were here, now we're going
  there, and the benefits for you are A, B, C."
- Early-stage (pre-Series B, small audience): renaming is cheap. Do it if the name has friction.
  Established brand with large equity: requires a compelling reason (legal threat, market pivot,
  unsearchable/unspellable name — the Codium→Windsurf case: nobody could spell it, SEO was dead).

Ask: What friction does the current name create? What equity does it actually hold (search
volume, press, word of mouth)? If friction is low and equity is real, say so and confirm the user
still wants to proceed before burning the pipeline on it.

## Round 2: The Four Questions

Ask these **in order**, one at a time, conversationally. Reflect each answer back sharpened
before moving on. Expect vague first answers — push once, gently, on each.

1. **"How do you define winning here?"**
   Every stakeholder answers this differently; the first answer is usually a platitude
   ("be the market leader"). Push for the concrete picture: winning in 18 months looks like
   what? Revenue, category position, acquisition, a movement?

2. **"What do you have to win?"**
   Inventory of actual assets: what's genuinely different about the product, team, tech,
   distribution, story. If the honest answer is "nothing novel — we're a very good version of a
   commodity," that is fine and common; note it, because then the name must do MORE work
   (the Swiffer situation: same mop-adjacent product, the name carried the reframe).

3. **"What do you need to win?"**
   The breakthrough required. Usually a communication problem: "we need people to understand
   that X done this way is better," or "we need retailers to see this as a new category, not a
   better mop."

4. **"What does the name need to say?"**
   The name's specific job — distinct from what packaging, copy, and product will say. The name
   is the highest-frequency asset; it gets one job. Force a choice: the name cannot say three
   things.

## The Benefit Ladder

After the four questions, ladder up to the **ultimate benefit** — this becomes the primary
creative territory. Run it live with the user:

```
attribute → functional benefit → emotional payoff → ultimate benefit
fiber, ground finer → better digestion → comfort, regularity → "you feel lighter"
```

Technique:
1. Propose 3-4 candidate ultimate benefits derived from their answers (for fiber: gut health /
   better metabolism / feeling lighter / daily ritual of self-care).
2. Ask which one makes them sit up. Watch for the energy — the "feel lighter" moment in the
   transcript came from noticing what animated the founder, not from analysis. If the user's
   free-text answer glows about one option, that's the signal; the picked checkbox matters less.
3. Confirm: "So the ultimate benefit we're naming toward is ___." One sentence.

The ultimate benefit is deliberately NOT the product description. Metamucil-era competitors all
name the ingredient (fiber); the winning move names the outcome (Feather territory: lightness).

## Handoff contract (write to 01-intake.md and 02-strategy.md)

```yaml
subject: <what is being named>
subject_type: company | product | app | feature | rename
category: <market category>
audience: <who>
markets: [list of countries/regions]
languages: [languages the name must survive]
constraints: [hard constraints, words to avoid, domain requirements]
existing_candidates:
  - name: <name>
    user_reaction: <love/hate + why>
rename_context: <friction vs equity summary, or omit>
winning_definition: <sharpened answer>
have_to_win: <assets>
need_to_win: <the breakthrough>
name_must_say: <the name's one job>
ultimate_benefit: <one sentence>
benefit_ladder: <attribute → functional → emotional → ultimate>
raw_qa: [full Q&A for exact phrasing — user's own words are generation fuel]
```
