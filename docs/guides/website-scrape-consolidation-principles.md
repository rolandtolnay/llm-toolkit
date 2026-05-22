# Website Scrape Consolidation Principles

Guide for turning raw website scrapes into practical, LLM-consumable business context documents. Designed to be referenced when building a Claude Code skill that scrapes and consolidates website content for use in feature design and product development.

---

## Purpose

Raw website scrapes are page-by-page dumps that mirror the site's navigation structure. This structure is optimized for marketing and SEO, not for an LLM agent that needs to quickly understand a business and make informed product decisions. Consolidation restructures the information around *what the business is and does* rather than *how the website is laid out*.

---

## Phase 1: Strip Scraping Artifacts

Every scraped page typically contains repeated boilerplate that must be removed before consolidation. Identify and discard:

### Always Remove
- **Navigation bars** - The same nav links appear on every page (`- Platforms`, `- Products`, `- Company`, etc.)
- **Footer content** - Repeated footer with product links, platform links, contact links, copyright notices
- **Image markdown** - `![alt text](url)` references to images that won't render in text context. Only keep alt text if it contains meaningful information not captured elsewhere
- **Login/CTA button links** - `[Login](...)`, `[Get Started](...)` repeated across pages
- **Powered-by badges** - `[![Synapto](logo.svg)](url)`
- **Duplicate CTAs** - "Want to know more? Get in touch today..." blocks that appear on every page
- **URL frontmatter** - The `---url: ... title: ...---` metadata block from the scraper

### Remove With Caution
- **Marketing fluff** - Superlative claims like "best-in-class" or "world's most innovative" can be dropped *unless* they contain a specific, factual claim embedded within them (e.g., "3-4x revenue increase" is worth keeping even if the surrounding sentence is fluffy)
- **UI mockup text** - Scraped text from screenshot-like UI elements (e.g., `Total Revenue £124,500`) is usually demo/placeholder data, not real content. Drop it unless it reveals a specific feature capability

---

## Phase 2: Identify Semantic Clusters

Website pages are organized by marketing goals (landing pages, product pages, audience pages, legal pages). Consolidation should reorganize by **knowledge domain**. The typical clusters for a B2B SaaS/product company are:

### Recommended Output Structure

| File | What Goes In It | Why It's Useful |
|---|---|---|
| **company-overview** | Identity, positioning, value proposition, architecture, third-party partners, business model, contact info | Grounds the agent in *who* and *why* - essential context for any feature work |
| **products-and-features** | Every product and its capabilities, organized by product line | The agent needs to know *what exists* to avoid redesigning existing features or to identify cross-product synergies |
| **audiences-and-partners** | Target customer segments, their specific value propositions, partner programs | Tells the agent *who uses this* and *what they care about* - critical for UX and prioritization decisions |
| **legal-and-compliance** | Synthesized key terms from privacy policy, ToS, EULA, acceptable use | Constraints the agent must respect when designing features (data handling, liability boundaries, compliance obligations) |

### Clustering Heuristics
- If the same fact appears on 3+ pages, it belongs in the **company-overview** (it's a core message)
- If content describes *what a thing does*, it goes in **products-and-features**
- If content describes *who benefits and why*, it goes in **audiences-and-partners**
- If content describes *what you can/cannot do*, it goes in **legal-and-compliance**
- Pages that are mostly CTAs with thin content (like "Get Started" contact forms) get dissolved into other files - the contact info goes to company-overview, the rest is discarded

---

## Phase 3: Consolidation Principles

### 1. Organize by entity, not by source page

Bad: One output file per source page (mirrors the website)
Good: One output file per knowledge domain (mirrors how an agent thinks)

A "Products" landing page, a "For Merchants" page, and a "For SaaS" page may all mention the same product. Consolidate all mentions of that product into a single authoritative section.

### 2. Deduplicate aggressively, but keep specifics

The same feature (e.g., "next-day settlement") may be mentioned in 5 different contexts with slightly different framing. Keep **one** canonical description. But if one page adds a specific detail not mentioned elsewhere (e.g., "1.2% card processing fee"), merge that detail into the canonical entry.

### 3. Prefer bullet lists and bold-key patterns

LLMs scan structured content much faster than prose paragraphs. The most effective format is:

```markdown
### Section Name
- **Key Term** - One-line explanation with specific details
- **Another Term** - Concrete capability, not vague promise
```

This pattern is:
- Scannable (bold terms act as an index)
- Dense (one line per concept, no filler)
- Greppable (agents can search for specific terms)

### 4. Preserve the company's own terminology

Keep branded terms, product names, and specific phrases the company uses (e.g., "Subscribed Services", "Authorised Users", "Permitted Purpose"). These terms may appear in APIs, database schemas, and UI copy. An agent that knows the canonical vocabulary will write more consistent code.

### 5. Keep numbers and specific claims

Strip generic marketing ("best-in-class solution") but keep anything concrete:
- Pricing: "1.2% card processing fee", "4.5% funding fee"
- Capabilities: "up to 8 hours battery life", "two most recent major versions of Android and iOS"
- Business metrics: "3-4x revenue increase from payments alone"
- Timeframes: "30 days written notice to terminate"
- Limits: "data deleted within 60 days post-termination"

### 6. Cross-reference between documents, don't duplicate

If the legal document defines what the "Synapto Platform" comprises (web + mobile + POS), put the canonical definition in company-overview and reference it from products-and-features rather than repeating it in both.

### 7. Add synthesized insights that aren't explicit on any single page

When reading across multiple pages reveals something that no individual page states directly, add it as a synthesized insight. For example:
- A business model summary derived from combining pricing info, partner descriptions, and EULA fee structures
- A platform architecture diagram reconstructed from multiple product descriptions
- Relationships between entities mentioned on different pages (e.g., connecting "Griffin" from the EULA to "Embedded Bank Accounts" from the product page)

Label these clearly so they're distinguishable from direct quotes.

### 8. For legal content: synthesize, don't reproduce

Legal documents (EULAs, privacy policies) are often 50-100KB of dense legalese. An LLM agent doesn't need the full text - it needs:
- The key constraints that affect feature design (data handling rules, liability boundaries)
- The defined terms that appear in the product (user types, service categories)
- Technical requirements (browser support, OS versions)
- Business rules (termination terms, fee structures, compliance obligations)

Summarize these into structured sections. Note that this is a summary and not a substitute for the full legal text. Keep the raw documents available for reference.

---

## Phase 4: Quality Checklist

After consolidation, verify:

- [ ] **No orphaned content** - Every meaningful fact from the raw scrape appears somewhere in the output
- [ ] **No duplicate facts** - Each specific claim appears in exactly one place
- [ ] **No scraping artifacts** - No nav bars, footers, image links, or repeated CTAs
- [ ] **Consistent heading hierarchy** - H1 for file title, H2 for major sections, H3 for subsections
- [ ] **Bold-key pattern** used for feature lists and data points
- [ ] **Company terminology preserved** - Branded terms and defined terms kept intact
- [ ] **Numbers and specifics retained** - No concrete data points lost during deduplication
- [ ] **Raw files preserved** - Original scrape kept in a subdirectory (e.g., `raw-scrape/`) for reference

---

## Skill Design Considerations

When building this as a reusable Claude Code skill:

### Input
- A directory of scraped markdown files (one per page)
- Optionally: the project context (what product is being built) to inform which content is most relevant

### Output
- 3-5 consolidated markdown files organized by knowledge domain
- Raw files moved to a `raw-scrape/` subdirectory
- The skill should NOT delete raw files - only move them

### Key Decisions the Skill Should Make
1. **How many output files?** - Typically 3-5. Fewer than 3 loses useful separation. More than 5 creates fragmentation. The exact split depends on the site's content.
2. **What to include in legal summary?** - Focus on constraints that affect feature design. Skip boilerplate liability clauses unless they contain specific business rules.
3. **How much marketing copy to keep?** - Keep taglines and value propositions (they define the brand voice the dashboard should reflect). Drop generic promotional paragraphs.
4. **What about thin pages?** - Pages with very little unique content (contact forms, simple landing pages) should be dissolved into other files rather than getting their own output file.

### Dealing with Edge Cases
- **PDF-sourced content** (like EULAs) often has OCR artifacts (e.g., `${ 3 ^ { \mathrm { r d } } }$` instead of "3rd"). Clean these during consolidation.
- **Dynamic/interactive content** (calculators, forms, carousels) gets scraped as flat text. Reconstruct the logical structure (e.g., a pricing table scraped as disconnected text blocks should be reformatted as a clear list).
- **Duplicate pages with slight variations** (e.g., two EULA variants) - identify the shared baseline and note only the differences.

### Bias Toward Retention
When uncertain whether to keep or discard content, **keep it**. The cost of including slightly-too-much context in a file is low (a few extra tokens). The cost of discarding something that turns out to be relevant for a future feature is high (forces re-scraping or guessing). Err on the side of more complete output.
