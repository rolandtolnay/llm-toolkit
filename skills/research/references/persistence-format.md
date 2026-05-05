# Research Persistence Format

STANDARD and DEEP research runs are persisted to the configured research directory (default: `~/Documents/Research/`; override with `RESEARCH_DIR`). Each run becomes a directory with one file per sub-agent plus a short orchestrator synthesis. QUICK lookups are NOT persisted.

**Opt-out:** Set `RESEARCH_NO_PERSIST=1` in an env file (see `<configuration>` in SKILL.md) or shell.

## Directory layout

```
~/Documents/Research/
  INDEX.md
  _archive/                              # populated only during backfill migrations
  2026-04-15-nmi-gpay-double-confirm/
    00-synthesis.md                      # orchestrator, decision-focused
    01-nmi-iframe-limitation.md          # sub-agent A
    02-google-pay-direct-pattern.md      # sub-agent B
    03-transient-user-activation.md      # sub-agent C
    04-community-discussion.md           # sub-agent D
  2026-04-14-claude-code-adaptive-thinking/
    00-synthesis.md
    01-official-env-var-source.md
    02-github-issues.md
    03-reddit-hn-community.md
```

**Run-id (directory name):** `YYYY-MM-DD-<slug>` where slug is a 3-5 word kebab-case summary of the query.
**Angle filename:** `0N-<angle-slug>.md` where N starts at `01` and angle-slug is a short kebab of the sub-question (3-5 words).
**Synthesis filename:** always `00-synthesis.md`.

## Authorship model

- **Angle files are written by sub-agents** directly to a target path the orchestrator assigns. This preserves source URLs, verbatim quotes, per-claim confidence, and methodological detail that a single-author synthesis pass would compress away.
- **The synthesis file is written by the orchestrator** after all sub-agents return. It is short, decision-oriented, and links to angle files for evidence. It does not duplicate finding bodies.
- **Write-failure fallback:** if a sub-agent returns without writing its expected file, the orchestrator writes it from the text return and sets `write_fallback: true` in the frontmatter.

## Angle file format

```markdown
---
title: "NMI iframe limitation and escape hatch"
date: 2026-04-15
run_id: 2026-04-15-nmi-gpay-double-confirm
role: angle
sub_question: "Has anyone else encountered NMI Collect.js Google Pay cross-domain iframe limitation? What workarounds exist?"
source_strategy: [WebSearch, "research ask", "research scrape"]
confidence: verified
tags: [payment-gateway, nmi, google-pay, iframe, browser-security]
sources:
  - url: https://docs.nmi.com/docs/digital-wallet-setup
    role: primary
  - url: https://docs.nmi.com/docs/collectjs
    role: primary
  - url: https://developers.googleblog.com/google-pay-inside-sandboxed-iframe-for-pci-dss-v4-compliance/
    role: secondary
write_fallback: false
---

# <Descriptive heading>

<Findings written by the sub-agent, with inline source citations, verbatim quotes where relevant, and methodological notes (what was searched and found empty). Length is not bounded — angle files are the evidence layer.>
```

**Frontmatter field rules:**
- `tags`: 3-7 free-form, specific nouns chosen by the sub-agent. Prefer `google-pay-iframe` over `web`. No controlled vocabulary.
- `sources.role`: `primary` (official docs, source code, author's post), `secondary` (well-known blogs, curated lists), `tertiary` (Perplexity synthesis, random forum posts).
- `confidence`: `verified` (checked against primary source), `likely` (multiple secondary sources agree), `unverified` (single source).
- `source_strategy`: list of commands + built-in tools actually used. Reflects what happened, not what was prescribed.

## Synthesis file format

```markdown
---
title: "NMI Google Pay Double-Confirm UX"
date: 2026-04-15
run_id: 2026-04-15-nmi-gpay-double-confirm
role: synthesis
query: "Why does NMI Google Pay require a second tap? How do we fix it?"
tags: [payment-gateway, google-pay, iframe, browser-security, user-activation, nmi]
angles:
  - 01-nmi-iframe-limitation.md
  - 02-google-pay-direct-pattern.md
  - 03-transient-user-activation.md
  - 04-community-discussion.md
confidence: verified
---

# <Topic> — Synthesis

**Query:** <original user question>
**Context:** <optional project/background>

## Answer

<1-3 paragraphs: the recommended decision + the single most important reason.>

## Why

<Key mechanism, with links to angle files for evidence.>
- Cross-origin DOM isolation — see [transient activation](03-transient-user-activation.md)
- Escape hatch exists — see [NMI iframe limitation](01-nmi-iframe-limitation.md)

## Implementation critical path

1. Step with pointer to [pattern](02-google-pay-direct-pattern.md)
2. ...

## Contradictions / open items

- <Flagged contradictions between sources — not silently resolved.>
- <Verification items deferred to support/stakeholders.>

## Evidence

See angle files in this directory for full findings, source URLs, and verbatim quotes.
```

**Style rules:**
- Decision-first. Lead with the recommended action; explain the mechanism second.
- Do not duplicate finding bodies. Link to the angle file.
- Target length: under 1500 words.
- `tags`: union of angle-file tags plus any synthesis-level additions.

## INDEX.md format

```markdown
# Research Index

### NMI Google Pay Double-Confirm UX — 2026-04-15
**Tags:** payment-gateway, google-pay, iframe, browser-security, user-activation, nmi
- [Synthesis](2026-04-15-nmi-gpay-double-confirm/00-synthesis.md) — Drop Collect.js GPay button; go direct to Google Pay with NMI Direct Connect tokenization.
- [NMI iframe limitation](2026-04-15-nmi-gpay-double-confirm/01-nmi-iframe-limitation.md) — `googlepay-token` Direct Post escape hatch; Collect.js button only works for card flows.
- [Google Pay direct pattern](2026-04-15-nmi-gpay-double-confirm/02-google-pay-direct-pattern.md) — `loadPaymentData()` must be inside sync click handler; Braintree default, Stripe legacy.
- [Transient user activation](2026-04-15-nmi-gpay-double-confirm/03-transient-user-activation.md) — HTML spec filters activation downward to same-origin only.
- [Community discussion](2026-04-15-nmi-gpay-double-confirm/04-community-discussion.md) — W3C issue #917 confirms root cause; zero NMI-specific complaints.
```

- Entries prepended (newest first).
- Run-level `**Tags:**` line enables grep-based discovery across topics.
- One bullet per angle file plus one for the synthesis. Each bullet has a one-line finding, NOT a generic heading.
- No within-file anchors — each bullet links to a dedicated file.

Create the configured research directory and `INDEX.md` if they don't exist.
