---
description: Recommend the best mental framework for your problem
argument-hint: [describe your situation or problem]
---

<objective>
Analyze $ARGUMENTS (or deduce the problem from conversation context) and recommend which mental framework to apply. Identify if research would improve the analysis.
</objective>

<available_frameworks>

## Decision-Making Frameworks

**10-10-10** - Time horizon analysis
- Best when: Making decisions where short-term comfort conflicts with long-term benefit
- Signals: "Should I...", "weighing options", "tempted to...", "worried about regretting"
- Example: Career change, major purchase, difficult conversation

**opportunity-cost** - Tradeoff analysis
- Best when: Choosing between options that consume finite resources (time, money, energy)
- Signals: "Can't do both", "limited budget/time", "either/or", "what am I giving up"
- Example: Which project to take on, where to invest, how to spend a weekend

**eisenhower-matrix** - Task prioritization
- Best when: Overwhelmed with multiple tasks, unclear what to tackle first
- Signals: "Too many things", "everything feels urgent", "where do I start", "drowning in tasks"
- Example: Overflowing to-do list, competing deadlines, role with many responsibilities

## Problem-Solving Frameworks

**5-whys** - Root cause discovery
- Best when: Facing a symptom or recurring problem, need to find the actual cause
- Signals: "Keeps happening", "tried fixes that don't stick", "why does this occur", "symptom of something deeper"
- Example: Bug that keeps returning, team conflict, process breakdown

**first-principles** - Assumption challenging
- Best when: Stuck in conventional thinking, need fresh perspective, building something new
- Signals: "Everyone does it this way", "is there a better way", "starting from scratch", "challenging the norm"
- Example: Redesigning a process, innovation challenge, questioning industry standards

**occams-razor** - Simplest explanation
- Best when: Multiple competing theories or explanations, debugging, confusion about what's really happening
- Signals: "Could be X or Y or Z", "overcomplicating", "what's actually going on", "simplest answer"
- Example: Debugging complex system, interpreting unclear data, diagnosing a problem

**inversion** - Failure avoidance
- Best when: Planning toward a goal, need to identify risks and pitfalls
- Signals: "How do I succeed at...", "what could go wrong", "avoid mistakes", "ensure success"
- Example: Project planning, launch preparation, preventing common failures

## Focus & Efficiency Frameworks

**one-thing** - Highest leverage action
- Best when: Scattered across many activities, need to identify the single most impactful action
- Signals: "Doing too much", "what matters most", "where should I focus", "if I could only do one thing"
- Example: Startup deciding priorities, personal productivity, breaking through stagnation

**pareto** - 80/20 analysis
- Best when: Need to identify the vital few factors driving most results
- Signals: "Lots of factors", "what really matters", "efficiency", "diminishing returns"
- Example: Optimizing a process, focusing marketing efforts, identifying key customers

**via-negativa** - Improvement through removal
- Best when: System/process is bloated, improvement comes from subtraction not addition
- Signals: "Too complex", "what can I remove", "simplify", "less is more", "streamline"
- Example: Simplifying a product, reducing commitments, cleaning up codebase

## Strategic Frameworks

**swot** - Strategic position analysis
- Best when: Evaluating competitive position, making strategic decisions, assessing a project or initiative
- Signals: "Strengths and weaknesses", "competitive advantage", "external threats", "market position"
- Example: Business strategy, career planning, project evaluation

**second-order** - Consequence tracing
- Best when: Need to understand ripple effects and downstream consequences of an action
- Signals: "What happens next", "unintended consequences", "domino effect", "long-term implications"
- Example: Policy change, major decision with many stakeholders, system change

</available_frameworks>

<available_research>
Research subagents gather external information in a fresh context window. Recommend one when the framework would benefit from data the user doesn't have.

- `research-technical` — Implementation approaches, libraries, tradeoffs
- `research-open-source` — Find existing libraries, tools, projects
- `research-feasibility` — Reality check on constraints
- `research-options` — Compare specific choices side-by-side
- `research-competitive` — Who else does this, strengths/weaknesses
- `research-landscape` — Map the domain, players, trends
- `research-history` — Past attempts, lessons learned
- `research-deep-dive` — Comprehensive topic investigation
</available_research>

<process>
1. Identify the problem: use $ARGUMENTS if provided, otherwise deduce from conversation context. Summarize in 1-2 sentences.

2. Match to the best framework based on problem type and signal words. Identify an alternative framework if a second one is a close fit.

3. Assess whether research would improve the framework's effectiveness. Research helps when the user is missing factual context (market data, technical constraints, what exists). Research does not help when the problem is about values, priorities, or internal decisions where all context is already present.

4. Present recommendation and use AskUserQuestion to confirm next action.
</process>

<output_format>
**Your situation:** [1-2 sentence summary]

**Recommended framework:** `/consider:[name]` — [2-3 sentences: why this fits]

**Alternative:** `/consider:[name]` — [1 sentence: when this would be better]

**Research:** [Either "Not needed — [reason]" OR "`research-[type]` — [what gap it fills]. Run before/after the framework."]

<!-- Use AskUserQuestion with header "Next step" -->
</output_format>

<success_criteria>
- Framework recommendation matches the problem type with clear justification
- Research recommended only when external information would change the analysis
- AskUserQuestion used before taking any action
- Alternative framework provided when a second one is a close fit
- Problem accurately captured (from arguments or deduced from conversation)
</success_criteria>
