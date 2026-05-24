# Vocabulary Activation Reference

Canonical terms that produce structured, precise LLM output. Use the exact term — synonyms activate weaker associations.

## Daily Drivers

Seven terms that cover ~80% of daily LLM steering. Memorise these first.

| Term | What it steers |
|------|---------------|
| **idiomatic** | "match existing patterns, not textbook patterns" |
| **sanity check** | "quick gut-check, not a deep review" |
| **pragmatic** | "good enough, don't over-engineer" |
| **enumerate** | "give me all of them, not a sample" |
| **impact analysis** | "what does this change affect across the system?" |
| **invariant** | "what specific rule is broken?" |
| **trade-off analysis** | "compare options, don't just recommend one" |

Everything below is the full reference, organised by category.

---

## Quick Reference

Scan this to jog your memory — click through to the full entry for usage guidance and examples.

### Analysis & Evaluation
| Term | One-liner |
|------|-----------|
| **impact analysis** | what does this change affect across the system? |
| **blast radius** | what specifically breaks when I touch this? |
| **trade-off analysis** | compare options against named criteria |
| **spike** | time-boxed investigation — findings, not code |
| **sanity check** | quick gut-check, not a deep review |

### Architecture & Design
| Term | One-liner |
|------|-----------|
| **seam** | where can I inject behavior without editing surrounding code? |
| **deep module** | complex inside, simple interface — is this abstraction earning its keep? |
| **conceptual integrity** | does this fit the system's one voice, or introduce a second way? |
| **idiomatic** | match existing patterns, not textbook patterns |
| **essential vs. accidental complexity** | is the difficulty from the problem or the solution? |
| **leaky abstraction** | callers need to know what's behind the interface to use it |
| **surface area** | how much is exposed? minimize what's public |
| **escape hatch** | how do I drop to a lower level when the abstraction doesn't fit? |
| **invariant** | what specific rule is being violated? |

### Debugging & Diagnosis
| Term | One-liner |
|------|-----------|
| **minimise the reproducer** | strip to the smallest input that still triggers the bug |
| **bisect** | binary search for where behavior changed |

### Planning & Scoping
| Term | One-liner |
|------|-----------|
| **solution horizon** | tactical / pragmatic / strategic — show all investment levels |
| **pragmatic** | good enough, ship it, don't over-engineer |
| **first principles** | reason from fundamentals, not conventions |
| **pareto (80/20)** | what 20% of effort delivers 80% of value? |
| **tracer bullet** | thin end-to-end slice proving the architecture works |
| **walking skeleton** | minimal deployable version exercising the full stack |
| **one-way / two-way door** | how hard is this to reverse? |
| **strangler fig** | incrementally replace, don't big-bang rewrite |

### Interrogation & Challenge
| Term | One-liner |
|------|-----------|
| **walk every path** | enumerate every branch in the decision tree |
| **stress-test** | what breaks under edge cases and failure modes? |
| **steel-man** | strongest version of the counter-argument |
| **devil's advocate** | actively poke holes in my reasoning |

### Code Quality
| Term | One-liner |
|------|-----------|
| **change propagation** | how far does this change ripple? |
| **shotgun surgery** | one logical change, edits scattered across many files |
| **feature envy** | this method uses another module's data more than its own |

### Output Shaping
| Term | One-liner |
|------|-----------|
| **enumerate** | give me all of them, not a sample |
| **distill** | compress to essentials — extract signal, discard noise |
| **rubber duck** | narrate understanding step by step before solving |

---

## Analysis & Evaluation

### Impact analysis
Enumerate what a proposed change affects, assess severity, flag risks. Covers blast radius, regression risk, complexity cost, and idiom fit.

**Use when:** You have a feature idea and want to understand system-level consequences before deciding to build it.

**Avoid:** "what are the consequences of this change?", "what could go wrong?", "review this idea", "is this safe to do?"

**Example:** "I want to switch our user ID format from auto-increment integers to UUIDs. Give me an impact analysis — what tables, APIs, caches, and downstream services does this touch, and what's the migration risk?"

### Blast radius
Scope of what breaks or changes when you touch something. Activates coupling analysis, dependency graphs, change propagation.

**Use when:** You want to know specifically what breaks — narrower than impact analysis, focused on damage surface.

**Avoid:** "what will this break?", "what else does this affect?", "is this a big change?"

**Example:** "If I delete the `UserPreferences` table and move those columns into the `Users` table, what's the blast radius? Which queries, repos, and API responses break?"

### Trade-off analysis
Evaluate competing options against named criteria. Forces the LLM to present runner-ups and what you're giving up.

**Use when:** You've identified multiple approaches and want a structured comparison, not a recommendation.

**Avoid:** "which one should I use?", "what's the best option?", "compare these for me", "pros and cons"

**Example:** "Trade-off analysis: REST vs GraphQL vs tRPC for our internal dashboard API. Compare on type safety, learning curve for the team, caching story, and client code generation."

### Spike
Time-boxed investigation to reduce uncertainty. Produces findings, not production code.

**Use when:** You don't know enough to plan yet. "Spike on whether X is feasible" prevents the LLM from jumping to implementation.

**Avoid:** "look into this", "can you research this?", "figure out if we can do X", "how would we do X?"

**Example:** "Spike on whether we can replace our Elasticsearch cluster with Postgres full-text search for our current query patterns. I need findings, not a migration plan."

### Sanity check
Quick verification that something is reasonable — not a deep review, not a full analysis. Activates lightweight "does this pass the smell test?" mode.

**Use when:** You want a fast gut-check, not a thorough review. "Sanity check this approach" gets a paragraph, not an essay.

**Avoid:** "does this look right?", "can you review this?", "what do you think of this approach?", "any issues with this?"

**Example:** "Sanity check: I'm planning to store JWT refresh tokens in an HttpOnly cookie and access tokens in memory. Does this approach hold up, or am I missing something obvious?"

---

## Architecture & Design

### Seam
A place where behavior can be altered without editing surrounding code (Feathers). Activates testability, modularity, and change-point reasoning.

**Use when:** You need to find where to inject new behavior or test boundaries in existing code.

**Avoid:** "where should I put this?", "how do I add this without breaking things?", "where's a good place to hook into?"

**Example:** "I need to add rate limiting to our payment processing flow without rewriting the controller. Where's the seam — where can I inject this behavior without touching the existing payment logic?"

### Deep module
A module that hides significant complexity behind a simple interface (Ousterhout). Activates interface-vs-implementation reasoning.

**Use when:** Evaluating whether an abstraction is pulling its weight or just adding indirection.

**Avoid:** "is this abstraction good?", "is this class doing too much?", "should I split this up?"

**Example:** "Our `NotificationService` has 15 public methods and callers need to understand retry logic, channel routing, and template rendering to use it. Is this a deep module or just a thin wrapper that leaks everything?"

### Conceptual integrity
The system speaks with one voice — consistent patterns, naming, and mental model throughout (Brooks).

**Use when:** Assessing whether a new addition fits the existing system's idioms or introduces a second way of doing things.

**Avoid:** "is this consistent?", "does this fit the codebase?", "this feels different from the rest"

**Example:** "The rest of our codebase uses repository pattern for data access, but this new module uses inline SQL queries with a query builder. Does this break conceptual integrity, and should I refactor it to match?"

### Idiomatic
A solution that follows the established patterns, conventions, and style of the existing codebase (or language/framework). Prevents the LLM from introducing a "correct but foreign" approach.

**Use when:** You want the solution to look like it belongs — "give me the idiomatic way to do X" or "is this idiomatic for our codebase?"

**Avoid:** "what's the right way to do this?", "what's best practice?", "how should I write this?"

**Example:** "What's the idiomatic way to handle errors in this Go codebase? I see some files using sentinel errors and others using custom error types — which pattern does this project actually follow?"

### Essential vs. accidental complexity
Complexity inherent to the problem vs. complexity introduced by the solution (Brooks).

**Use when:** Questioning whether implementation difficulty comes from the problem itself or from poor abstraction choices.

**Avoid:** "why is this so complicated?", "can we simplify this?", "is this over-engineered?"

**Example:** "This billing calculation is 400 lines with nested conditionals for proration, tax regions, and plan tiers. How much of this complexity is essential to billing rules vs. accidental complexity from how we structured the code?"

### Leaky abstraction
When implementation details bleed through the interface (Spolsky). The caller has to understand what's behind the abstraction to use it correctly.

**Use when:** Evaluating interface quality — "is this abstraction leaking?" catches APIs that promise simplicity but demand internal knowledge.

**Avoid:** "this API is confusing", "callers need to know too much", "the interface is bad"

**Example:** "Our `CacheManager.get()` method requires callers to pass a `region` parameter that maps to specific Redis cluster shards. Is this a leaky abstraction? Should callers need to know about our sharding topology?"

### Surface area
How much of a module is exposed to consumers. Large surface area = more to learn, more to break, more to maintain.

**Use when:** You want the LLM to minimize what's public — "reduce the surface area" activates API trimming and encapsulation.

**Avoid:** "this exposes too much", "there are too many public methods", "can we hide some of this?"

**Example:** "This SDK client exposes 47 public methods but our users only use about 12 of them. Help me reduce the surface area — which methods should be internal, and what's the minimal public API?"

### Escape hatch
An intentional "break glass" path that lets you drop to a lower level when an abstraction doesn't cover your case — without abandoning the abstraction entirely. A system without one forces you to fight it or rewrite around it.

**Use when:** Choosing a library ("does this ORM let me drop to raw SQL?"), reviewing a design ("where's the escape hatch for the 10% of cases this wasn't built for?"), or building an abstraction ("what break-glass path should I provide?").

**Avoid:** "can I override this?", "how do I work around this limitation?", "what if it doesn't fit my use case?"

**Example:** "Our form validation library handles 90% of cases, but for the address field we need custom async validation against a geocoding API. Where's the escape hatch — can I bypass the standard validation pipeline for just this field?"

### Invariant
A condition that must always hold, regardless of code path. "What invariant does this violate?" is dramatically sharper than "what's wrong?"

**Use when:** Reasoning about correctness — forces the LLM to name the specific rule being broken rather than describe symptoms.

**Avoid:** "what's wrong with this?", "why is this broken?", "find the bug", "this shouldn't happen"

**Example:** "Users are seeing negative wallet balances, which should be impossible. What invariant is being violated — walk me through every code path that modifies the balance and find where the check is missing."

---

## Debugging & Diagnosis

### Minimise the reproducer
Reduce a failing case to the smallest input that still triggers the bug.

**Use when:** You have a bug report and want the LLM to isolate rather than guess-and-fix.

**Avoid:** "make a simpler test", "can you reproduce this?", "why is this test failing?"

**Example:** "This 200-line integration test is flaking on CI. Help me minimise the reproducer — strip it down to the smallest test case that still triggers the race condition."

### Bisect
Binary search through a range (commits, inputs, config) to find where behavior changed.

**Use when:** Something worked before and doesn't now, and you want a systematic approach rather than shotgun debugging.

**Avoid:** "find which commit broke this", "when did this stop working?", "check the recent changes"

**Example:** "Image uploads worked on Friday but return 413 errors now. Help me bisect — there were 30 commits over the weekend. What's the fastest way to binary search for the commit that broke it?"

---

## Planning & Scoping

### Solution horizon
Tactical (patch it now), pragmatic (fix it properly), strategic (redesign the area). Forces the LLM to present options at different investment levels.

**Use when:** You want to see the full spectrum of fix depth before choosing how much to invest.

**Avoid:** "how should we fix this?", "what are our options?", "give me a few approaches"

**Example:** "Our search is slow on large result sets. Show me the solution horizon: what's the tactical patch to ship today, the pragmatic fix for next sprint, and the strategic redesign if we invest a full quarter?"

### Pragmatic
Favor the solution that works and ships over the one that's theoretically optimal. Accept trade-offs, minimize investment, tolerate imperfection.

**Use when:** You want to prevent over-engineering — "give me the pragmatic approach" cuts off gold-plating and premature abstraction.

**Avoid:** "keep it simple", "don't over-think it", "what's the quickest way?", "just make it work"

**Example:** "I need to deduplicate incoming webhook events but we only get ~100 per hour. Give me the pragmatic approach — I don't want a distributed idempotency framework, I want the simplest thing that works."

### First principles
Derive the answer from fundamentals rather than pattern-matching from conventions or prior examples. The opposite of "idiomatic."

**Use when:** You suspect the existing approach is wrong and want the LLM to reason from scratch rather than copy what's already there.

**Avoid:** "think about this differently", "ignore what everyone else does", "why do we actually need this?"

**Example:** "Everyone says we need a message queue for this, but our throughput is 50 events per minute. Reason from first principles — do we actually need a queue, or is there a simpler architecture that fits our actual constraints?"

### Pareto (80/20)
Identify the 20% of effort that delivers 80% of the value. Activates scope-cutting and prioritization reasoning.

**Use when:** Scoping work, trimming feature lists, or asking "what's the minimum that actually matters here?"

**Avoid:** "what's most important?", "what should we prioritize?", "what's the MVP?"

**Example:** "We have 20 feature requests for the admin panel. Apply the Pareto principle — which 4-5 features would satisfy 80% of the admin users' daily workflows?"

### Tracer bullet
A thin end-to-end implementation that touches every layer, proving the architecture works before filling in details (Hunt & Thomas).

**Use when:** Starting a new feature and you want the skeleton working across all layers before fleshing anything out.

**Avoid:** "build a quick prototype", "make a basic version first", "start with something simple"

**Example:** "I'm building a new notifications system. Help me write a tracer bullet — one notification type, hardcoded content, hitting the real database, the real API, and the real push service. No templates, no preferences, just prove the path works."

### Walking skeleton
Similar to tracer bullet but emphasizes the minimal deployable version that exercises the full stack.

**Use when:** You want to validate integration and deployment pipeline early, not just architecture.

**Avoid:** "get the deployment working first", "build the simplest version", "scaffold the project"

**Example:** "We're starting a new microservice. Build me a walking skeleton — a single health-check endpoint that deploys through our full CI/CD pipeline to staging with a real Dockerfile, Helm chart, and monitoring. No business logic yet."

### One-way door / two-way door
A one-way door is hard or impossible to reverse; a two-way door is cheap to undo (Bezos). Changes how the LLM weighs risk and recommends caution.

**Use when:** Making architectural or infrastructure decisions — "is this a one-way door?" forces explicit reversibility reasoning.

**Avoid:** "can we undo this later?", "how risky is this?", "is this reversible?", "what if we change our mind?"

**Example:** "We're considering moving from PostgreSQL to DynamoDB for the orders table. Is this a one-way door? How hard is it to reverse once we've migrated production data and built services around DynamoDB's access patterns?"

### Strangler fig
Incrementally replace a legacy system by building the new one around it, routing traffic piece by piece until the old one is dead (Fowler).

**Use when:** Discussing migrations or rewrites — prevents the LLM from proposing big-bang replacements.

**Avoid:** "how do we migrate gradually?", "can we do this incrementally?", "how do we avoid a big rewrite?"

**Example:** "We need to migrate from our monolith's auth module to a dedicated auth service. Design a strangler fig approach — how do we route requests incrementally so we can migrate endpoint by endpoint without a flag day cutover?"

---

## Interrogation & Challenge

### Walk every path of the decision tree
Exhaustively enumerate every branching choice in a design, resolving each one before moving on. Prevents the LLM from collapsing options into a single recommendation too early.

**Use when:** You have a plan or design and want every hidden assumption surfaced — not just the happy path.

**Avoid:** "think through all the cases", "what am I missing?", "are there edge cases?", "what about the unhappy path?"

**Example:** "We're designing the retry logic for failed payments. Walk every path of the decision tree: what if the charge fails vs. times out vs. returns unknown? What if the user cancels mid-retry? What if the webhook arrives before the retry completes?"

### Stress-test
Challenge a design against edge cases, failure modes, and adversarial inputs. Activates "what breaks if..." reasoning.

**Use when:** You have a plan you're fairly confident in and want it pressure-tested, not interrogated from scratch.

**Avoid:** "what could go wrong?", "test this against edge cases", "is this robust enough?"

**Example:** "Stress-test our session management design: what happens with concurrent logins from two devices, a clock-skewed JWT, a Redis failover mid-session, and a user changing their password while sessions are active?"

### Steel-man
Present the strongest possible version of a counter-argument or alternative approach before dismissing it.

**Use when:** You've made a decision but want to verify you're not ignoring a legitimately better option out of anchoring bias.

**Avoid:** "what's the argument for the other option?", "are we sure about this?", "what would someone who disagrees say?"

**Example:** "We decided to build our own feature flag system instead of using LaunchDarkly. Steel-man the case for LaunchDarkly — what's the strongest argument that we're making a mistake by building in-house?"

### Devil's advocate
Argue the opposite position to find weaknesses. More adversarial than steel-man — the LLM actively tries to break your reasoning.

**Use when:** You want someone to poke holes, not just present alternatives politely.

**Avoid:** "poke holes in this", "challenge my thinking", "tell me why this is wrong"

**Example:** "I'm convinced we should rewrite this service in Rust for performance. Play devil's advocate — why is this a terrible idea, and what am I underestimating about the migration cost?"

---

## Code Quality

### Change propagation
How far a single change ripples through the system. High propagation = high coupling.

**Use when:** Evaluating whether a proposed change is isolated or will cascade across modules.

**Avoid:** "how many files does this touch?", "will this change cascade?", "what else needs updating?"

**Example:** "If I rename the `userId` field to `accountId` in the `Order` model, what's the change propagation? How many files, API contracts, and client apps need to update?"

### Shotgun surgery
A single logical change requires edits scattered across many files (Fowler).

**Use when:** You notice a change touching many files and want the LLM to assess whether the code needs consolidation.

**Avoid:** "this change touches too many files", "why do I need to edit so many places?", "this is scattered everywhere"

**Example:** "Adding a new user role required changes in 14 files across 6 directories — the auth middleware, three route guards, the admin UI, the seed script, and the docs. This feels like shotgun surgery. Where should this logic be consolidated?"

### Feature envy
A method that uses another module's data more than its own (Fowler). Signals misplaced responsibility.

**Use when:** Reviewing code placement decisions — "does this logic belong here?"

**Avoid:** "this method knows too much about other classes", "should this logic live somewhere else?", "this reaches into too many objects"

**Example:** "This `OrderController` method reaches into `User.subscription.plan.limits.maxOrders` to check if the user can place an order. That's feature envy — should this validation live in the `User` or `Subscription` model instead?"

---

## Output Shaping

### Enumerate
Forces exhaustive listing rather than a selective sample. "Enumerate all X" vs "what are some X" is the difference between a complete inventory and a few examples.

**Use when:** You need every instance, option, or case — not a representative sample.

**Avoid:** "list everything", "give me all of them", "what are the options?", "show me what's available"

**Example:** "Enumerate every environment variable this service reads, including defaults and optional ones. I'm writing the deployment docs and need the complete list, not just the critical ones."

### Distill
Compress something complex into a smaller, simpler form that preserves the essential behavior or information. The opposite of "enumerate" — instead of listing everything, extract only what matters.

**Use when:** You have a large, noisy input (spec, conversation, logs, architecture doc) and want the LLM to extract the core signal rather than summarize or paraphrase the whole thing.

**Avoid:** "summarize this", "give me the key points", "what's the TL;DR?", "can you shorten this?"

**Example:** "Distill this 20-page architecture doc into the 5 rules an engineer needs to know before writing code in this repo. I don't want a summary — I want the load-bearing constraints that actually shape daily decisions."

### Rubber duck
Make the LLM narrate its understanding step by step rather than jump to a solution. Forces the explanation to come before the answer.

**Use when:** You want to verify the LLM actually understands the problem before it starts solving — "rubber duck this for me" surfaces wrong assumptions early.

**Avoid:** "explain this to me", "walk me through the code", "how does this work?", "think step by step"

**Example:** "Before you suggest a fix, rubber duck this for me: walk through what happens step by step when a user hits 'checkout' with an expired coupon code. I want to make sure we both understand the current flow before changing anything."
