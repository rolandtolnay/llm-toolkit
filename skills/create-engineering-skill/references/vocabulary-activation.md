# Vocabulary Activation

## The Mechanism

Frontier LLMs have read canonical software engineering texts during training. When a prompt uses a term like "deep module," it doesn't communicate a concept — it activates the entire network of associated knowledge the LLM absorbed from reading Ousterhout. The LLM recalls the definition, the examples, the trade-offs, the relationship to other concepts, and the failure modes.

One canonical term replaces paragraphs of explanation. "Test at the seam" activates Feathers' entire framework — the definition of a seam, the types, the techniques for exploiting them. Writing "find the place where you can alter behavior without editing the code" is longer, less precise, and activates less.

## How to Apply

**Use the canonical term, not a synonym.** "Seam" not "injection point" or "boundary." "Tracer bullet" not "thin vertical slice." Synonyms activate weaker or different associations.

**Use terms as native language.** Write "identify the seams" not "what Michael Feathers calls a 'seam.'" The citation frame signals the term needs introduction — wasting tokens and weakening activation. The LLM already knows the term; use it as if both parties have read the book.

**List rejected framings.** For each key term, explicitly list synonyms and near-synonyms to avoid. This prevents vocabulary drift in the skill and in the LLM's output:
- Say "module," not "component" or "service"
- Say "seam," not "boundary" or "injection point"
- Say "interface," not "API" (reserve API for HTTP endpoints)

**Test activation empirically.** Replace a canonical term with its plain-language equivalent and compare output quality. If outputs are equivalent, the term isn't earning its place. If the canonical term produces more precise, nuanced, or structurally sound output — it's working.

## Density Target

3-8 activation terms per skill. Fewer than 3 and the skill lacks the vocabulary density that distinguishes engineering skills from generic prompts. More than 8 and terms start competing with each other for the LLM's attention rather than reinforcing a coherent framework.

## When Activation Fails

Vocabulary activation works because the LLM has deep training-data coverage of the source material. It fails when:
- The concept is from an obscure or recent source the LLM may not have absorbed
- The term is overloaded (means different things in different contexts)
- The skill targets a small or local model with less training coverage

In these cases, fall back to a one-sentence inline definition — just enough to disambiguate, not a full explanation.
