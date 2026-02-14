---
description: Analyze what you give up by choosing this option
argument-hint: [choice or leave blank for current context]
---

<objective>
Apply opportunity cost analysis to $ARGUMENTS (or the current discussion if no arguments provided).
</objective>

<process>
1. State the choice being considered
2. List what resources it consumes (time, money, energy, attention). For coding decisions with AI-assisted development, implementation time is often trivial — focus on complexity introduced, cognitive load, and whether the approach is proportionate to the problem.
3. Identify the best alternative use of those same resources
4. Compare value of chosen option vs. best alternative
5. Determine if the tradeoff is worth it
</process>

<output_format>
**Choice:** [what you're considering doing]

**Resources consumed:** [list the resources this choice requires — time, money, energy, attention, etc.]

**Best alternative use of those resources:** [what you'd do instead, and the value it would provide]

**True Cost:**
Choosing this means NOT doing [best alternative], which would have provided [value].

**Verdict:**
[Is the chosen option worth more than the best alternative?]
</output_format>

<success_criteria>
- Compares to best alternative, not just any alternative
- Makes hidden costs explicit — reveals when "affordable" things are actually expensive
- Accounts for all relevant resource types (not just money)
</success_criteria>
