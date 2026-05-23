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

## Analysis & Evaluation

### Impact analysis
Enumerate what a proposed change affects, assess severity, flag risks. Covers blast radius, regression risk, complexity cost, and idiom fit.

**Use when:** You have a feature idea and want to understand system-level consequences before deciding to build it.

**Example:** "I want to switch our user ID format from auto-increment integers to UUIDs. Give me an impact analysis — what tables, APIs, caches, and downstream services does this touch, and what's the migration risk?"

### Blast radius
Scope of what breaks or changes when you touch something. Activates coupling analysis, dependency graphs, change propagation.

**Use when:** You want to know specifically what breaks — narrower than impact analysis, focused on damage surface.

**Example:** "If I delete the `UserPreferences` table and move those columns into the `Users` table, what's the blast radius? Which queries, repos, and API responses break?"

### Trade-off analysis
Evaluate competing options against named criteria. Forces the LLM to present runner-ups and what you're giving up.

**Use when:** You've identified multiple approaches and want a structured comparison, not a recommendation.

**Example:** "Trade-off analysis: REST vs GraphQL vs tRPC for our internal dashboard API. Compare on type safety, learning curve for the team, caching story, and client code generation."

### Spike
Time-boxed investigation to reduce uncertainty. Produces findings, not production code.

**Use when:** You don't know enough to plan yet. "Spike on whether X is feasible" prevents the LLM from jumping to implementation.

**Example:** "Spike on whether we can replace our Elasticsearch cluster with Postgres full-text search for our current query patterns. I need findings, not a migration plan."

### Sanity check
Quick verification that something is reasonable — not a deep review, not a full analysis. Activates lightweight "does this pass the smell test?" mode.

**Use when:** You want a fast gut-check, not a thorough review. "Sanity check this approach" gets a paragraph, not an essay.

**Example:** "Sanity check: I'm planning to store JWT refresh tokens in an HttpOnly cookie and access tokens in memory. Does this approach hold up, or am I missing something obvious?"

---

## Architecture & Design

### Seam
A place where behavior can be altered without editing surrounding code (Feathers). Activates testability, modularity, and change-point reasoning.

**Use when:** You need to find where to inject new behavior or test boundaries in existing code.

**Example:** "I need to add rate limiting to our payment processing flow without rewriting the controller. Where's the seam — where can I inject this behavior without touching the existing payment logic?"

### Deep module
A module that hides significant complexity behind a simple interface (Ousterhout). Activates interface-vs-implementation reasoning.

**Use when:** Evaluating whether an abstraction is pulling its weight or just adding indirection.

**Example:** "Our `NotificationService` has 15 public methods and callers need to understand retry logic, channel routing, and template rendering to use it. Is this a deep module or just a thin wrapper that leaks everything?"

### Conceptual integrity
The system speaks with one voice — consistent patterns, naming, and mental model throughout (Brooks).

**Use when:** Assessing whether a new addition fits the existing system's idioms or introduces a second way of doing things.

**Example:** "The rest of our codebase uses repository pattern for data access, but this new module uses inline SQL queries with a query builder. Does this break conceptual integrity, and should I refactor it to match?"

### Idiomatic
A solution that follows the established patterns, conventions, and style of the existing codebase (or language/framework). Prevents the LLM from introducing a "correct but foreign" approach.

**Use when:** You want the solution to look like it belongs — "give me the idiomatic way to do X" or "is this idiomatic for our codebase?"

**Example:** "What's the idiomatic way to handle errors in this Go codebase? I see some files using sentinel errors and others using custom error types — which pattern does this project actually follow?"

### Essential vs. accidental complexity
Complexity inherent to the problem vs. complexity introduced by the solution (Brooks).

**Use when:** Questioning whether implementation difficulty comes from the problem itself or from poor abstraction choices.

**Example:** "This billing calculation is 400 lines with nested conditionals for proration, tax regions, and plan tiers. How much of this complexity is essential to billing rules vs. accidental complexity from how we structured the code?"

### Leaky abstraction
When implementation details bleed through the interface (Spolsky). The caller has to understand what's behind the abstraction to use it correctly.

**Use when:** Evaluating interface quality — "is this abstraction leaking?" catches APIs that promise simplicity but demand internal knowledge.

**Example:** "Our `CacheManager.get()` method requires callers to pass a `region` parameter that maps to specific Redis cluster shards. Is this a leaky abstraction? Should callers need to know about our sharding topology?"

### Surface area
How much of a module is exposed to consumers. Large surface area = more to learn, more to break, more to maintain.

**Use when:** You want the LLM to minimize what's public — "reduce the surface area" activates API trimming and encapsulation.

**Example:** "This SDK client exposes 47 public methods but our users only use about 12 of them. Help me reduce the surface area — which methods should be internal, and what's the minimal public API?"

### Escape hatch
A deliberate way out of an abstraction when it doesn't fit the use case. The difference between a flexible design and a rigid one.

**Use when:** Evaluating whether a design is too opinionated — "where's the escape hatch?" asks if users can break out when the happy path doesn't apply.

**Example:** "Our form validation library handles 90% of cases, but for the address field we need custom async validation against a geocoding API. Where's the escape hatch — can I bypass the standard validation pipeline for just this field?"

### Invariant
A condition that must always hold, regardless of code path. "What invariant does this violate?" is dramatically sharper than "what's wrong?"

**Use when:** Reasoning about correctness — forces the LLM to name the specific rule being broken rather than describe symptoms.

**Example:** "Users are seeing negative wallet balances, which should be impossible. What invariant is being violated — walk me through every code path that modifies the balance and find where the check is missing."

---

## Debugging & Diagnosis

### Minimise the reproducer
Reduce a failing case to the smallest input that still triggers the bug.

**Use when:** You have a bug report and want the LLM to isolate rather than guess-and-fix.

**Example:** "This 200-line integration test is flaking on CI. Help me minimise the reproducer — strip it down to the smallest test case that still triggers the race condition."

### Bisect
Binary search through a range (commits, inputs, config) to find where behavior changed.

**Use when:** Something worked before and doesn't now, and you want a systematic approach rather than shotgun debugging.

**Example:** "Image uploads worked on Friday but return 413 errors now. Help me bisect — there were 30 commits over the weekend. What's the fastest way to binary search for the commit that broke it?"

---

## Planning & Scoping

### Solution horizon
Tactical (patch it now), pragmatic (fix it properly), strategic (redesign the area). Forces the LLM to present options at different investment levels.

**Use when:** You want to see the full spectrum of fix depth before choosing how much to invest.

**Example:** "Our search is slow on large result sets. Show me the solution horizon: what's the tactical patch to ship today, the pragmatic fix for next sprint, and the strategic redesign if we invest a full quarter?"

### Pragmatic
Favor the solution that works and ships over the one that's theoretically optimal. Accept trade-offs, minimize investment, tolerate imperfection.

**Use when:** You want to prevent over-engineering — "give me the pragmatic approach" cuts off gold-plating and premature abstraction.

**Example:** "I need to deduplicate incoming webhook events but we only get ~100 per hour. Give me the pragmatic approach — I don't want a distributed idempotency framework, I want the simplest thing that works."

### First principles
Derive the answer from fundamentals rather than pattern-matching from conventions or prior examples. The opposite of "idiomatic."

**Use when:** You suspect the existing approach is wrong and want the LLM to reason from scratch rather than copy what's already there.

**Example:** "Everyone says we need a message queue for this, but our throughput is 50 events per minute. Reason from first principles — do we actually need a queue, or is there a simpler architecture that fits our actual constraints?"

### Pareto (80/20)
Identify the 20% of effort that delivers 80% of the value. Activates scope-cutting and prioritization reasoning.

**Use when:** Scoping work, trimming feature lists, or asking "what's the minimum that actually matters here?"

**Example:** "We have 20 feature requests for the admin panel. Apply the Pareto principle — which 4-5 features would satisfy 80% of the admin users' daily workflows?"

### Tracer bullet
A thin end-to-end implementation that touches every layer, proving the architecture works before filling in details (Hunt & Thomas).

**Use when:** Starting a new feature and you want the skeleton working across all layers before fleshing anything out.

**Example:** "I'm building a new notifications system. Help me write a tracer bullet — one notification type, hardcoded content, hitting the real database, the real API, and the real push service. No templates, no preferences, just prove the path works."

### Walking skeleton
Similar to tracer bullet but emphasizes the minimal deployable version that exercises the full stack.

**Use when:** You want to validate integration and deployment pipeline early, not just architecture.

**Example:** "We're starting a new microservice. Build me a walking skeleton — a single health-check endpoint that deploys through our full CI/CD pipeline to staging with a real Dockerfile, Helm chart, and monitoring. No business logic yet."

### One-way door / two-way door
A one-way door is hard or impossible to reverse; a two-way door is cheap to undo (Bezos). Changes how the LLM weighs risk and recommends caution.

**Use when:** Making architectural or infrastructure decisions — "is this a one-way door?" forces explicit reversibility reasoning.

**Example:** "We're considering moving from PostgreSQL to DynamoDB for the orders table. Is this a one-way door? How hard is it to reverse once we've migrated production data and built services around DynamoDB's access patterns?"

### Strangler fig
Incrementally replace a legacy system by building the new one around it, routing traffic piece by piece until the old one is dead (Fowler).

**Use when:** Discussing migrations or rewrites — prevents the LLM from proposing big-bang replacements.

**Example:** "We need to migrate from our monolith's auth module to a dedicated auth service. Design a strangler fig approach — how do we route requests incrementally so we can migrate endpoint by endpoint without a flag day cutover?"

---

## Interrogation & Challenge

### Walk every path of the decision tree
Exhaustively enumerate every branching choice in a design, resolving each one before moving on. Prevents the LLM from collapsing options into a single recommendation too early.

**Use when:** You have a plan or design and want every hidden assumption surfaced — not just the happy path.

**Example:** "We're designing the retry logic for failed payments. Walk every path of the decision tree: what if the charge fails vs. times out vs. returns unknown? What if the user cancels mid-retry? What if the webhook arrives before the retry completes?"

### Stress-test
Challenge a design against edge cases, failure modes, and adversarial inputs. Activates "what breaks if..." reasoning.

**Use when:** You have a plan you're fairly confident in and want it pressure-tested, not interrogated from scratch.

**Example:** "Stress-test our session management design: what happens with concurrent logins from two devices, a clock-skewed JWT, a Redis failover mid-session, and a user changing their password while sessions are active?"

### Steel-man
Present the strongest possible version of a counter-argument or alternative approach before dismissing it.

**Use when:** You've made a decision but want to verify you're not ignoring a legitimately better option out of anchoring bias.

**Example:** "We decided to build our own feature flag system instead of using LaunchDarkly. Steel-man the case for LaunchDarkly — what's the strongest argument that we're making a mistake by building in-house?"

### Devil's advocate
Argue the opposite position to find weaknesses. More adversarial than steel-man — the LLM actively tries to break your reasoning.

**Use when:** You want someone to poke holes, not just present alternatives politely.

**Example:** "I'm convinced we should rewrite this service in Rust for performance. Play devil's advocate — why is this a terrible idea, and what am I underestimating about the migration cost?"

---

## Code Quality

### Change propagation
How far a single change ripples through the system. High propagation = high coupling.

**Use when:** Evaluating whether a proposed change is isolated or will cascade across modules.

**Example:** "If I rename the `userId` field to `accountId` in the `Order` model, what's the change propagation? How many files, API contracts, and client apps need to update?"

### Shotgun surgery
A single logical change requires edits scattered across many files (Fowler).

**Use when:** You notice a change touching many files and want the LLM to assess whether the code needs consolidation.

**Example:** "Adding a new user role required changes in 14 files across 6 directories — the auth middleware, three route guards, the admin UI, the seed script, and the docs. This feels like shotgun surgery. Where should this logic be consolidated?"

### Feature envy
A method that uses another module's data more than its own (Fowler). Signals misplaced responsibility.

**Use when:** Reviewing code placement decisions — "does this logic belong here?"

**Example:** "This `OrderController` method reaches into `User.subscription.plan.limits.maxOrders` to check if the user can place an order. That's feature envy — should this validation live in the `User` or `Subscription` model instead?"

---

## Output Shaping

### Enumerate
Forces exhaustive listing rather than a selective sample. "Enumerate all X" vs "what are some X" is the difference between a complete inventory and a few examples.

**Use when:** You need every instance, option, or case — not a representative sample.

**Example:** "Enumerate every environment variable this service reads, including defaults and optional ones. I'm writing the deployment docs and need the complete list, not just the critical ones."

### Rubber duck
Make the LLM narrate its understanding step by step rather than jump to a solution. Forces the explanation to come before the answer.

**Use when:** You want to verify the LLM actually understands the problem before it starts solving — "rubber duck this for me" surfaces wrong assumptions early.

**Example:** "Before you suggest a fix, rubber duck this for me: walk through what happens step by step when a user hits 'checkout' with an expired coupon code. I want to make sure we both understand the current flow before changing anything."
