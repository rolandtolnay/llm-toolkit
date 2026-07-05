# Screening Guide — Collision, Trademark, Domain, SEO, Linguistic

Run AFTER the user's gut-reaction round, on the 8-12 names that earned energy. Screening is
knockout research, not clearance: the goal is to **kill cheaply and flag honestly**. Never state
or imply a name is legally cleared — every surviving name carries the line "verify with a
trademark attorney before committing."

Screening subagents use the research CLI — read `../../research/references/cli-reference.md`
first. Batch 3-4 names per subagent, run subagents in parallel. Free tools first (WebSearch,
WebFetch); escalate to `research.py search`/`ask` when free results are thin.

## Layer 1: Collision scan (kills most names — run first)

For each name, search: `"<name>" <category>`, `"<name>" app`, `"<name>" company`, and
`"<name>" startup`. Looking for anyone already using the name **in or near the category**.

- Active company/product, same or adjacent category → **kill**.
- Active use in a distant category (a "Feather" furniture rental vs. a fiber supplement) →
  **caution**: note it; distant-category coexistence is common but needs attorney review.
- Dead/parked projects, tiny abandoned repos → note and move on.

## Layer 2: Trademark quick screen

Web-search the trademark registers — do not pretend to run a real clearance search:
`"<name>" trademark`, `site:tmsearch.uspto.gov "<name>"` (or USPTO search via the web UI
results), `site:euipo.europa.eu "<name>"` for EU markets, plus WIPO Global Brand Database
mentions. Match against the product's Nice class informally (software=9/42, food=29/30/5, etc.).

- Live registered mark, same class, same/confusable spelling → **kill**.
- Live marks in other classes, or dead/abandoned marks → **caution** with specifics.
- Nothing found → **clear-ish** (explicitly that word — web screening has false negatives).

## Layer 3: Domain and handles

Check the plausible domains: exact `.com`, plus `.ai`/`.io`/`.app`/`.co` as fits the product,
and prefixed forms (`get<name>.com`, `try<name>.com`, `<name>hq.com`). Method: WebFetch the URL
or search `site:<name>.com` — a parked page or NXDOMAIN both matter.

Modern norms: exact-match .com is a nice-to-have, not a kill criterion (unless the user's intake
said otherwise). Report three states: available-ish / parked-or-squatted (acquirable, unknown
price) / actively used by a real business (raises confusion risk beyond just domains).
Spot-check the obvious social handles (X, Instagram, GitHub org for dev products) only for the
top candidates.

## Layer 4: SEO ownability

The Codium lesson in reverse: can this name be *found*?

- Search the bare name. Is page one dominated by a strong existing meaning (a celebrity, a
  common word with massive query volume, an unrelated famous brand)? Dominant unrelated meaning
  → **caution**: the brand will fight for its own SERP for years. Common words CAN be owned
  (Apple, Slack) with enough marketing force — flag, don't kill, but say what it costs.
- Spellability → searchability: if people who *hear* the name will type three different
  spellings, note which competitor/typosquat each lands on.

## Layer 5: Linguistic and cultural check

You are natively multilingual — this is Lexicon's round-the-world linguist network for free.
For each of the user's target languages plus the big trade languages (Spanish, French, German,
Portuguese, Mandarin, Japanese, Arabic, Hindi):

1. Does the name mean, sound like, or evoke anything negative, vulgar, or comical?
2. Is it pronounceable, and does the pronunciation drift somewhere damaging?
3. For borrowed foreign words: verify the actual meaning and register (poetic? archaic? slang?).

Do this from model knowledge first, then verify anything suspicious with a targeted search
(`"<name>" meaning slang <language>`). Calibration failures to catch: Mitsubishi Pajero
(Spanish slang), Ford Pinto (Brazilian slang), Nokia Lumia (Spanish slang), IKEA Fartfull.
Only genuine, current-usage problems in a target market are kills; a faint archaic echo in a
non-target language is a footnote.

## Verdict format (per name, written to the screening file)

```markdown
### <Name>
verdict: clear-ish | caution | kill
- collisions: <finding + URL, or "none found">
- trademark: <finding + register + class, or "no live same-class marks surfaced">
- domains: <exact .com state; best available alternative>
- seo: <ownable / contested by <what>>
- linguistic: <per-language notes, only where nonzero>
- notes: <anything the recommendation stage should say out loud>
```

Kills go in the file with their reason — the user should see WHY a beloved name died, and a
killed name's territory often points at a sibling name that survives (the "how do we modify
that word so it's legally available?" move: try spelling variants, affixed forms, or the same
concept from an adjacent hunting ground before declaring the territory dead).
