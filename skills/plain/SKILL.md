---
name: plain
description: Rephrase an explanation in plain language without losing substance. Use when a synthesis is too dense to act on — legal, tax, accounting, product research, or technical — and the reader needs to understand it well enough to decide.
disable-model-invocation: true
---

Rephrase the target explanation for an intelligent reader with no background in this domain. They are not reading out of curiosity: they need to understand the material well enough to make a decision and act on it themselves, so the rewrite succeeds only if it is both understandable and complete enough to act on.

**Target:** $ARGUMENTS — if empty, rephrase your most recent substantive explanation in this conversation, or the material the user just referenced.

## Style

Write in the style of the SEC Plain English Handbook, at roughly an 8th-grade reading level: short sentences, one idea per sentence, active voice with a named actor ("you must file X by Y", not "a filing obligation arises"), everyday words over terms of art, concrete examples over abstractions.

Lead with the answer — what this means for the reader and what they should do. Explanation and evidence come after. Default to plain paragraphs; use lists or tables only when the content is a genuine comparison or enumeration.

Keep a term of art when the reader will encounter it again — on forms, in laws, in contracts, in vendor docs, in error messages — and define it in plain words the first time, in the same sentence. Otherwise replace it.

## Substance

Plain language must not cost substance. Preserve every fact that changes what the reader would decide or do:

- every obligation, requirement, or action item, and who it falls on
- every number: deadlines, amounts, thresholds, prices, limits
- every condition that changes the outcome ("this applies only if…")
- every material risk, penalty, or trade-off
- the citations and sources behind factual claims

If simplifying would collapse a distinction that changes the decision, keep the distinction and explain it plainly instead.

If sources disagree, or the answer depends on a fact about the reader's situation you don't have, say so plainly and name the fact that decides it. Do not average disagreement into a vague middle ground, and do not let missing evidence silently become a "no".

## Before answering

Compare the rewrite against the original. If a decision-relevant fact from the list above was dropped, put it back. A rewrite that survives this check is done — do not pad it back toward the original's length or density.
