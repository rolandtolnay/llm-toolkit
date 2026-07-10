# Goal log

Append one entry per autonomous goal. Do not rewrite past verdicts. Put product decisions in `PROJECT.md`, domain terms in `CONTEXT.md`, and implementation decisions in `docs/decisions.md` or an ADR.

Retain compact decision-relevant proof under `docs/goal-evidence/<goal-id>/`. Keep secrets, real user data, build caches, and bulky transient logs out of Git; distill their relevant facts here.

No goal runs recorded yet.

---

## Entry template

### <YYYY-MM-DD> — <goal title>

**Goal and outcome**

<Exact outcome-oriented goal and what becomes true.>

**Working-tree baseline**

- Initial `git status --short`: <result>
- Pre-existing changes and ownership: <none or exact paths>
- Overlap risk: <none or blocker>

**Assumptions and defaults**

- <Choice derived from canonical sources and why.>

**Persona, flow, and guardrails**

- Persona and moment: <who, when, and relevant pressure>
- Start state: <where the flow begins>
- End state: <what is true when successful>
- Confusions to kill: <facts that must become obvious>
- Guardrails: <paths, behavior, external effects, or adjacent scope excluded>

**Rubric**

1. <Falsifiable outcome or deterministic check.>
2. <Falsifiable quality, trust, safety, or edge-state check.>

**Implementation summary**

- <What changed and why.>

**Verification and evidence**

- `<command>` — <exact observed result>
- Product/fixture truth comparison: <result or not applicable>
- Retained evidence: `docs/goal-evidence/<goal-id>/` or none
- Transient evidence distilled: <facts or none>

**Judge pass 1**

- Verdict: `GOAL MET` | `BLOCKERS REMAIN`
- Blockers: <findings or none>
- Polish: <findings or none>
- Fixes: <changes after this pass>
- Rejected findings: <item and reason, or none>

<Repeat judge sections after meaningful fixes.>

**Completion**

- Final verdict: `GOAL MET` | `[blocked]`
- If blocked: <exact condition, attempted recovery, current state, safest resume step>
- Commit/deploy/release: <result or not requested>
- Follow-up explicitly left out: <scope>
