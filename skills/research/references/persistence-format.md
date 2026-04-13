# Research Persistence Format

STANDARD and DEEP research runs are persisted to `~/Documents/Research/` so paid API results are never lost. QUICK lookups are NOT persisted.

**Opt-out:** Set `RESEARCH_NO_PERSIST=1` in an env file (see `<configuration>` in SKILL.md) or shell to disable persistence.

## File structure

```
~/Documents/Research/
  INDEX.md                              # Scannable topic index
  2026-03-30-bank-account-verification.md
  2026-03-31-nextjs-auth-patterns.md
```

**File naming:** `YYYY-MM-DD-<slug>.md` — slug is a short kebab-case summary of the query (3-5 words max).

## Research file format

```markdown
# <Research Topic>
**Date:** YYYY-MM-DD
**Query:** <original user question>

---

## <Sub-question 1 heading>
**Source strategy:** <commands used>
**Confidence:** <verified | likely | unverified>

<sub-agent findings with citations — written as-is from the sub-agent return>

---

## <Sub-question 2 heading>
...

---

## Synthesis

<orchestrator's final synthesized answer with citations>
```

Sub-question headings MUST be descriptive topic labels (e.g., "Compliance Requirements & Regulations"), not generic names like "Sub-agent 1". These headings become anchor targets for the index AND the matching surface for STEP 2 of `research_mode` — future research runs scan INDEX.md sub-question by sub-question to decide whether to skip or refine. Vague headings break that match and waste prior work.

## INDEX.md format

Each research run gets a heading with its sub-questions listed individually. This makes the index a topic discovery tool — readers can scan all angles covered across all past research.

```markdown
# Research Index

### Bank Account Verification Best Practices — 2026-03-30
- [Compliance requirements & regulations](2026-03-30-bank-account-verification.md#compliance-requirements--regulations)
- [Backend architecture & implementation patterns](2026-03-30-bank-account-verification.md#backend-architecture--implementation-patterns)
- [Competitor approaches to verification](2026-03-30-bank-account-verification.md#competitor-approaches-to-verification)

### Next.js Auth Patterns — 2026-03-28
- [Official Next.js auth support](2026-03-28-nextjs-auth-patterns.md#official-nextjs-auth-support)
- [Community patterns & libraries](2026-03-28-nextjs-auth-patterns.md#community-patterns--libraries)
```

**Anchor format:** GitHub-style — lowercase, spaces→hyphens, strip special chars except hyphens. E.g., heading `## Compliance Requirements & Regulations` → anchor `#compliance-requirements--regulations`.

Prepend new entries at the top of INDEX.md (most recent first). Create `~/Documents/Research/` and `INDEX.md` if they don't exist.
