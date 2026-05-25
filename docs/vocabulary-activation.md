# Vocabulary activation reference

Specific terms that reliably steer LLMs toward structured, precise output. Use the exact wording — close synonyms trigger weaker associations and you get vaguer results.

## Daily drivers

Eight terms that cover ~80% of daily LLM steering. Start here.

| Term | What it steers |
|------|---------------|
| **pragmatic** | "good enough, don't over-engineer" |
| **idiomatic** | "match existing patterns, not textbook patterns" |
| **sanity check** | "quick gut-check, not a deep review" |
| **first principles** | "reason from fundamentals, not conventions" |
| **pareto (80/20)** | "what 20% of effort delivers 80% of value?" |
| **impact analysis** | "what does this change affect across the system?" |
| **trade-off analysis** | "compare options, don't just recommend one" |
| **audit** | "check every item against defined criteria — pass/fail, not vibes" |

Everything below is the full reference, organised by category.

---

## Quick reference

Scan this to jog your memory — the full entry has usage guidance and examples.

### Analysis & evaluation

| Term | One-liner |
|------|-----------|
| **impact analysis** | what does this change affect across the system? |
| **blast radius** | what specifically breaks when I touch this? |
| **trade-off analysis** | compare options against named criteria |
| **spike** | time-boxed investigation — findings, not code |
| **sanity check** | quick gut-check, not a deep review |
| **audit** | check every item against defined criteria — pass/fail, not vibes |

### Architecture & design

| Term | One-liner |
|------|-----------|
| **seam** | where can I inject behavior without editing surrounding code? |
| **deep module** | complex inside, simple interface — is this abstraction earning its keep? |
| **conceptual integrity** | does this fit the system's one voice, or introduce a second way? |
| **essential vs. accidental complexity** | is the difficulty from the problem or the solution? |
| **leaky abstraction** | callers need to know what's behind the interface to use it |
| **surface area** | how much is exposed? minimize what's public |
| **escape hatch** | how do I drop to a lower level when the abstraction doesn't fit? |
| **invariant** | what specific rule is being violated? |

### Debugging & diagnosis

| Term | One-liner |
|------|-----------|
| **minimise the reproducer** | strip to the smallest input that still triggers the bug |
| **bisect** | binary search for where behavior changed |

### Planning & scoping

| Term | One-liner |
|------|-----------|
| **solution horizon** | tactical / pragmatic / strategic — show all investment levels |
| **pragmatic** | good enough, ship it, don't over-engineer |
| **idiomatic** | match existing patterns, not textbook patterns |
| **first principles** | reason from fundamentals, not conventions |
| **pareto (80/20)** | what 20% of effort delivers 80% of value? |
| **tracer bullet** | thin end-to-end slice proving the architecture works |
| **walking skeleton** | minimal deployable version exercising the full stack |
| **one-way / two-way door** | how hard is this to reverse? |
| **strangler fig** | incrementally replace, don't big-bang rewrite |

### Interrogation & challenge

| Term | One-liner |
|------|-----------|
| **walk every path** | enumerate every branch in the decision tree |
| **stress-test** | what breaks under edge cases and failure modes? |
| **steel-man** | strongest version of the counter-argument |
| **devil's advocate** | actively poke holes in my reasoning |

### Code quality

| Term | One-liner |
|------|-----------|
| **change propagation** | how far does this change ripple? |
| **shotgun surgery** | one logical change, edits scattered across many files |
| **feature envy** | this method uses another module's data more than its own |

### Output shaping

| Term | One-liner |
|------|-----------|
| **enumerate** | give me all of them, not a sample |
| **distill** | compress to essentials — extract signal, discard noise |
| **rubber duck** | narrate understanding step by step before solving |

---

## Analysis & evaluation

### Impact analysis
Map out what a proposed change touches — every table, API, cache, and downstream service — then assess severity and flag risks. This is the broadest analysis term: it covers blast radius, regression risk, complexity cost, and whether the change fits existing idioms.

**Use when:** You have a feature idea and want to understand system-level consequences before deciding to build it.

**Don't say:** `what are the consequences of this change?`, `what could go wrong?`, `review this idea`, `is this safe to do?`

**Example:** "I want to switch our user ID format from auto-increment integers to UUIDs. Give me an impact analysis — what tables, APIs, caches, and downstream services does this touch, and what's the migration risk?"

### Blast radius
What specifically breaks when you touch something. Narrower than impact analysis — you're asking about damage, not general consequences. You'll get coupling analysis and dependency tracing rather than broad risk assessment.

**Use when:** You want to know what breaks — damage surface, not a general "what could happen."

**Don't say:** `what will this break?`, `what else does this affect?`, `is this a big change?`

**Example:** "If I delete the `UserPreferences` table and move those columns into the `Users` table, what's the blast radius? Which queries, repos, and API responses break?"

### Trade-off analysis
Compare competing options against named criteria. The key word here is "analysis" — you're asking for a structured comparison with runner-ups and what you're giving up, not a single recommendation.

**Use when:** You've identified multiple approaches and want them compared side by side, not ranked.

**Don't say:** `which one should I use?`, `what's the best option?`, `compare these for me`, `pros and cons`

**Example:** "Trade-off analysis: REST vs GraphQL vs tRPC for our internal dashboard API. Compare on type safety, learning curve for the team, caching story, and client code generation."

### Spike
Time-boxed investigation to reduce uncertainty. A spike produces findings, not production code. Saying "spike on whether X is feasible" keeps the LLM in research mode instead of jumping straight to implementation.

**Use when:** You don't know enough to plan yet and need a structured investigation, not a prototype.

**Don't say:** `look into this`, `can you research this?`, `figure out if we can do X`, `how would we do X?`

**Example:** "Our mobile app needs offline support but nobody on the team has built a sync engine. Spike on this — what conflict resolution strategies exist, which ones fit our data model, and what will we still not know until we prototype? Don't build anything."

### Sanity check
Quick verification that something is reasonable — not a deep review, not a full analysis. Think "does this pass the smell test?" You'll get a paragraph, not an essay.

**Use when:** You want a fast gut-check, not a thorough review.

**Don't say:** `does this look right?`, `can you review this?`, `what do you think of this approach?`, `any issues with this?`

**Example:** "Sanity check: I'm planning to store JWT refresh tokens in an HttpOnly cookie and access tokens in memory. Does this approach hold up, or am I missing something obvious?"

### Audit
Systematically check every item against defined criteria, producing a pass/fail inventory. Unlike "review" (subjective, selective) or "sanity check" (quick gut-feel), an audit is exhaustive and criterion-based — nothing gets skipped, nothing is evaluated on vibes.

**Use when:** You want completeness and accountability — every item checked, every gap surfaced.

**Don't say:** `review this for me`, `check this over`, `look through this for issues`, `are there any problems?`

**Example:** "Audit every API endpoint against our error handling contract: does each one return structured error responses with a code, message, and request ID? Give me a pass/fail for each endpoint, not just the ones that look wrong."

---

## Architecture & design

### Seam
A place where behavior can be altered without editing surrounding code (from Michael Feathers' "Working Effectively with Legacy Code"). When you ask "where's the seam?", you get answers about injection points, test boundaries, and modularity — not just "put it here."

**Use when:** You need to find where to inject new behavior or test boundaries in existing code.

**Don't say:** `where should I put this?`, `how do I add this without breaking things?`, `where's a good place to hook into?`

**Example:** "We need to add audit logging to every mutation in our GraphQL API, but the resolvers are spread across 30 files. Where's the seam — is there a single point in the execution pipeline where we can intercept all mutations without modifying individual resolvers?"

### Deep module
A module that hides significant complexity behind a simple interface (from John Ousterhout's "A Philosophy of Software Design"). The question you're really asking: is this abstraction earning its keep, or is it just indirection?

**Use when:** Evaluating whether an abstraction is pulling its weight.

**Don't say:** `is this abstraction good?`, `is this class doing too much?`, `should I split this up?`

**Example:** "We're debating whether to merge our `EmailService`, `SMSService`, and `PushService` into a single `NotificationService` with one `send()` method. Would that be a deep module that simplifies things for callers, or are the channels different enough that a unified interface would just hide complexity callers still need to manage?"

### Conceptual integrity
The system speaks with one voice — consistent patterns, naming, and mental model throughout. Fred Brooks coined this in *The Mythical Man-Month*, and it's still one of the sharpest design concepts around. When you ask about conceptual integrity, you're asking whether a new addition fits the existing idioms or introduces a second way of doing things.

**Use when:** Assessing whether a new addition fits the system or creates a parallel convention.

**Don't say:** `is this consistent?`, `does this fit the codebase?`, `this feels different from the rest`

**Example:** "Half our services use event-driven communication through Kafka and the other half use synchronous REST calls. We're adding a new service — does it matter which pattern we pick, or has the system already lost conceptual integrity and we should just use whatever fits this service best?"

### Essential vs. accidental complexity
Complexity inherent to the problem vs. complexity introduced by the solution — another Brooks distinction. Before you try to simplify something, this helps you figure out which parts are genuinely hard and which are artifacts of how the solution was built.

**Use when:** You suspect the difficulty comes from poor abstraction choices, not the problem itself.

**Don't say:** `why is this so complicated?`, `can we simplify this?`, `is this over-engineered?`

**Example:** "Our deployment pipeline takes 45 minutes and involves 12 steps across three tools. Before we try to simplify it, help me separate essential vs. accidental complexity — which steps exist because our architecture genuinely requires them (multi-region, canary, database migrations) and which are artifacts of how we stitched the pipeline together over time?"

### Leaky abstraction
When implementation details bleed through the interface — Joel Spolsky's term. The caller has to understand what's behind the abstraction to use it correctly, which defeats the point of having one.

**Use when:** Evaluating interface quality — "is this abstraction leaking?" catches APIs that promise simplicity but demand internal knowledge.

**Don't say:** `this API is confusing`, `callers need to know too much`, `the interface is bad`

**Example:** "Our `CacheManager.get()` method requires callers to pass a `region` parameter that maps to specific Redis cluster shards. Is this a leaky abstraction? Should callers need to know about our sharding topology?"

### Surface area
How much of a module is exposed to consumers. More surface area means more to learn, more to break, and more to maintain. "Reduce the surface area" gets you API trimming and encapsulation advice, not vague suggestions to "simplify."

**Use when:** You want to minimize what's public.

**Don't say:** `this exposes too much`, `there are too many public methods`, `can we hide some of this?`

**Example:** "This SDK client exposes 47 public methods but our users only use about 12 of them. Help me reduce the surface area — which methods should be internal, and what's the minimal public API?"

### Escape hatch
An intentional "break glass" path that lets you drop to a lower level when an abstraction doesn't cover your case — without abandoning the abstraction entirely. A system without one forces you to fight it or rewrite around it.

**Use when:** Choosing a library ("does this ORM let me drop to raw SQL?"), reviewing a design ("where's the escape hatch for the edge cases?"), or building an abstraction ("what break-glass path should I provide?").

**Don't say:** `can I override this?`, `how do I work around this limitation?`, `what if it doesn't fit my use case?`

**Example:** "Our form validation library handles 90% of cases, but for the address field we need custom async validation against a geocoding API. Where's the escape hatch — can I bypass the standard validation pipeline for just this field?"

### Invariant
A condition that must always hold, regardless of code path. "What invariant is violated?" is dramatically sharper than "what's wrong?" — it makes the LLM name the specific rule being broken rather than describe symptoms.

**Use when:** Reasoning about correctness — you want the specific rule that's being violated, not a description of what went wrong.

**Don't say:** `what's wrong with this?`, `why is this broken?`, `find the bug`, `this shouldn't happen`

**Example:** "Users are seeing negative wallet balances, which should be impossible. What invariant is being violated — walk me through every code path that modifies the balance and find where the check is missing."

---

## Debugging & diagnosis

### Minimise the reproducer
Reduce a failing case to the smallest input that still triggers the bug. This keeps the LLM focused on isolation rather than guessing at fixes.

**Use when:** You have a bug report and want to isolate the problem first, not jump to solutions.

**Don't say:** `make a simpler test`, `can you reproduce this?`, `why is this test failing?`

**Example:** "This 200-line integration test is flaking on CI. Help me minimise the reproducer — strip it down to the smallest test case that still triggers the race condition."

### Bisect
Binary search through a range (commits, inputs, config) to find where behavior changed. Systematic narrowing instead of shotgun debugging.

**Use when:** Something worked before and doesn't now, and you want a systematic approach.

**Don't say:** `find which commit broke this`, `when did this stop working?`, `check the recent changes`

**Example:** "Image uploads worked on Friday but return 413 errors now. Help me bisect — there were 30 commits over the weekend. What's the fastest way to binary search for the commit that broke it?"

---

## Planning & scoping

### Solution horizon
Three investment levels: tactical (patch it now), pragmatic (fix it properly), strategic (redesign the area). This term makes the LLM present all three instead of picking one for you.

**Use when:** You want to see the full spectrum of fix depth before choosing how much to invest.

**Don't say:** `how should we fix this?`, `what are our options?`, `give me a few approaches`

**Example:** "Our API response times spike to 3 seconds during peak hours because of N+1 queries in the order listing endpoint. Show me the solution horizon: what's the tactical fix I can ship this afternoon, the pragmatic refactor for next sprint, and the strategic approach if we invest in redesigning the data access layer?"

### Pragmatic
Favor the solution that works and ships over the one that's theoretically optimal. Accept trade-offs, minimize investment, tolerate imperfection. "Give me the pragmatic approach" cuts off gold-plating before it starts.

**Use when:** You want to prevent over-engineering.

**Don't say:** `keep it simple`, `don't over-think it`, `what's the quickest way?`, `just make it work`

**Example:** "I need to deduplicate incoming webhook events but we only get ~100 per hour. Give me the pragmatic approach — I don't want a distributed idempotency framework, I want the simplest thing that works."

### Idiomatic
A solution that follows the established patterns, conventions, and style of the codebase (or language/framework). "Idiomatic" keeps the answer grounded in how this project actually works, not how a textbook says it should work.

**Use when:** You want the solution to look like it belongs here, not just be technically correct.

**Don't say:** `what's the right way to do this?`, `what's best practice?`, `how should I write this?`

**Example:** "What's the idiomatic way to handle errors in this Go codebase? I see some files using sentinel errors and others using custom error types — which pattern does this project actually follow?"

### First principles
Derive the answer from fundamentals rather than pattern-matching from conventions or prior examples. The opposite of "idiomatic" — you're asking the LLM to reason from scratch rather than copy what's already there.

**Use when:** You suspect the existing approach is wrong and want fresh reasoning.

**Don't say:** `think about this differently`, `ignore what everyone else does`, `why do we actually need this?`

**Example:** "Everyone says we need a message queue for this, but our throughput is 50 events per minute. Reason from first principles — do we actually need a queue, or is there a simpler architecture that fits our actual constraints?"

### Pareto (80/20)
Identify the 20% of effort that delivers 80% of the value. You'll get scope-cutting and prioritization, not comprehensive coverage.

**Use when:** Scoping work, trimming feature lists, or asking "what's the minimum that actually matters here?"

**Don't say:** `what's most important?`, `what should we prioritize?`, `what's the MVP?`

**Example:** "We have 15 tickets for improving the onboarding flow — email verification, SSO, invite links, progressive profiling, role selection, and more. Apply the Pareto principle — which 3-4 changes would eliminate 80% of the drop-off we're seeing between signup and first meaningful action?"

### Tracer bullet
A thin end-to-end implementation that touches every layer, proving the architecture works before you fill in details. From *The Pragmatic Programmer* — and the distinction matters: a tracer bullet uses real infrastructure with minimal scope, whereas a prototype can be throwaway.

**Use when:** Starting a new feature and you want the skeleton working across all layers before fleshing anything out.

**Don't say:** `build a quick prototype`, `make a basic version first`, `start with something simple`

**Example:** "I'm building a new notifications system. Help me write a tracer bullet — one notification type, hardcoded content, hitting the real database, the real API, and the real push service. No templates, no preferences, just prove the path works."

### Walking skeleton
Similar to tracer bullet but with a deployment emphasis — the minimal version that goes through your full CI/CD pipeline and runs in a real environment.

**Use when:** You want to validate integration and deployment early, not just architecture.

**Don't say:** `get the deployment working first`, `build the simplest version`, `scaffold the project`

**Example:** "We're starting a new microservice. Build me a walking skeleton — a single health-check endpoint that deploys through our full CI/CD pipeline to staging with a real Dockerfile, Helm chart, and monitoring. No business logic yet."

### One-way door / two-way door
A one-way door is hard or impossible to reverse; a two-way door is cheap to undo. Bezos popularized this framing at Amazon, and the distinction changes how much caution is warranted — spend time on one-way doors, move fast through two-way doors.

**Use when:** Making architectural or infrastructure decisions where reversibility matters.

**Don't say:** `can we undo this later?`, `how risky is this?`, `is this reversible?`, `what if we change our mind?`

**Example:** "We're considering moving from PostgreSQL to DynamoDB for the orders table. Is this a one-way door? How hard is it to reverse once we've migrated production data and built services around DynamoDB's access patterns?"

### Strangler fig
Incrementally replace a legacy system by building the new one around it, routing traffic piece by piece until the old one is dead. Martin Fowler named this after the actual plant — the fig that wraps around a tree and eventually replaces it. Without this term, you tend to get "rebuild from scratch" plans.

**Use when:** Discussing migrations or rewrites — you want an incremental approach, not a "rebuild from scratch" plan.

**Don't say:** `how do we migrate gradually?`, `can we do this incrementally?`, `how do we avoid a big rewrite?`

**Example:** "Our billing system is a 10-year-old Rails monolith that handles invoicing, payment processing, and subscription management. We want to extract payment processing into a new service. Design a strangler fig — how do we start routing payment calls to the new service while the monolith still handles invoicing, without any downtime or data inconsistency?"

---

## Interrogation & challenge

### Walk every path of the decision tree
Exhaustively enumerate every branching choice in a design, resolving each one before moving on. This stops the LLM from collapsing options into a single recommendation too early or designing only for the happy path.

**Use when:** You have a plan or design and want every hidden assumption surfaced.

**Don't say:** `think through all the cases`, `what am I missing?`, `are there edge cases?`, `what about the unhappy path?`

**Example:** "We're designing the user deletion flow for GDPR compliance. Walk every path of the decision tree: what if they have active subscriptions? Pending orders? Shared team resources? Connected OAuth apps? Referral credits owed to others? Resolve each branch before moving to the next — I don't want a happy-path design that misses half the real cases."

### Stress-test
Challenge a design against edge cases, failure modes, and adversarial inputs. Unlike "walk every path" (which is about completeness), stress-test is about pressure — what breaks under load, bad data, or hostile conditions?

**Use when:** You have a plan you're fairly confident in and want it pressure-tested.

**Don't say:** `what could go wrong?`, `test this against edge cases`, `is this robust enough?`

**Example:** "Stress-test our session management design: what happens with concurrent logins from two devices, a clock-skewed JWT, a Redis failover mid-session, and a user changing their password while sessions are active?"

### Steel-man
Present the strongest possible version of a counter-argument or alternative approach before dismissing it. The opposite of straw-manning — you're asking for the best case against your position.

**Use when:** You've made a decision but want to verify you're not ignoring a legitimately better option out of anchoring bias.

**Don't say:** `what's the argument for the other option?`, `are we sure about this?`, `what would someone who disagrees say?`

**Example:** "We decided to build our own feature flag system instead of using LaunchDarkly. Steel-man the case for LaunchDarkly — what's the strongest argument that we're making a mistake by building in-house?"

### Devil's advocate
Argue the opposite position to find weaknesses. More adversarial than steel-man — you're not asking for the best version of the counter-argument, you're asking the LLM to actively try to break your reasoning.

**Use when:** You want someone to poke holes, not just present alternatives politely.

**Don't say:** `poke holes in this`, `challenge my thinking`, `tell me why this is wrong`

**Example:** "I'm convinced we should rewrite this service in Rust for performance. Play devil's advocate — why is this a terrible idea, and what am I underestimating about the migration cost?"

---

## Code quality

### Change propagation
How far a single change ripples through the system. High propagation means high coupling — and a signal that something might need restructuring.

**Use when:** Evaluating whether a proposed change is isolated or will cascade across modules.

**Don't say:** `how many files does this touch?`, `will this change cascade?`, `what else needs updating?`

**Example:** "If I rename the `userId` field to `accountId` in the `Order` model, what's the change propagation? How many files, API contracts, and client apps need to update?"

### Shotgun surgery
A single logical change requires edits scattered across many files — one of Fowler's code smells. The opposite of good encapsulation: you change one thing, and you're touching 14 files in 6 directories.

**Use when:** You notice a change touching many files and want to assess whether the code needs consolidation.

**Don't say:** `this change touches too many files`, `why do I need to edit so many places?`, `this is scattered everywhere`

**Example:** "Adding a new user role required changes in 14 files across 6 directories — the auth middleware, three route guards, the admin UI, the seed script, and the docs. This feels like shotgun surgery. Where should this logic be consolidated?"

### Feature envy
A method that uses another module's data more than its own — another Fowler code smell. It's a signal that the logic probably belongs somewhere else.

**Use when:** Reviewing code placement decisions — "does this logic belong here?"

**Don't say:** `this method knows too much about other classes`, `should this logic live somewhere else?`, `this reaches into too many objects`

**Example:** "This `OrderController` method reaches into `User.subscription.plan.limits.maxOrders` to check if the user can place an order. That's feature envy — should this validation live in the `User` or `Subscription` model instead?"

---

## Output shaping

### Enumerate
Exhaustive listing rather than a selective sample. "Enumerate all X" vs "what are some X" is the difference between a complete inventory and a few examples.

**Use when:** You need every instance, option, or case — not a representative sample.

**Don't say:** `list everything`, `give me all of them`, `what are the options?`, `show me what's available`

**Example:** "Enumerate every environment variable this service reads, including defaults and optional ones. I'm writing the deployment docs and need the complete list, not just the critical ones."

### Distill
Compress something complex into a smaller form that preserves what actually matters. The opposite of "enumerate" — instead of listing everything, extract only the signal and drop the noise.

**Use when:** You have a large, noisy input (spec, conversation, logs, architecture doc) and want the core meaning extracted, not a summary or paraphrase of the whole thing.

**Don't say:** `summarize this`, `give me the key points`, `what's the TL;DR?`, `can you shorten this?`

**Example:** "Distill this 20-page architecture doc into the 5 rules an engineer needs to know before writing code in this repo. I don't want a summary — I want the load-bearing constraints that actually shape daily decisions."

### Rubber duck
Make the LLM narrate its understanding step by step before solving anything. The explanation comes first, the answer comes second — which surfaces wrong assumptions early.

**Use when:** You want to verify the LLM actually understands the problem before it starts solving it.

**Don't say:** `explain this to me`, `walk me through the code`, `how does this work?`, `think step by step`

**Example:** "We have a race condition where two concurrent checkout requests can both succeed for the last item in stock. Before you suggest a fix, rubber duck this for me — narrate exactly what you think happens between the stock check and the decrement, including where locks are or aren't held. I want to verify you've got the right mental model before we pick a solution."
