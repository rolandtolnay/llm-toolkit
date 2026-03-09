# Skill Patterns

Common skill categories, structural patterns, and conventions.

## Skill Categories

### Document & Asset Creation

Create consistent, high-quality output (docs, code, reports, presentations).

**Key techniques:**
- Embedded style guides and templates
- Quality checklists before finalizing
- Output format specifications with examples
- Usually simple structure (single SKILL.md)

### Workflow Automation

Multi-step processes with ordering, validation, and iterative refinement.

**Key techniques:**
- Step-by-step workflow with validation gates
- Iterative refinement loops (draft -> validate -> refine -> finalize)
- Decision trees for choosing approaches
- Simple if single workflow, complex if multiple distinct workflows

### MCP Enhancement

Teaching Claude to use MCP tools effectively with domain expertise.

**Key techniques:**
- Workflow guidance on top of tool access
- Embedded domain expertise and best practices
- Error handling for common MCP issues
- Coordination across multiple MCP calls

## Common Patterns

### Sequential Workflow Orchestration

Explicit step ordering with dependencies and validation at each stage.

```markdown
## Step 1: Gather inputs
Collect required parameters. Validate before proceeding.

## Step 2: Process
Execute the main operation using validated inputs from Step 1.

## Step 3: Validate output
Check results against success criteria. If validation fails, return to Step 2.

## Step 4: Deliver
Present results in the specified format.
```

### Iterative Refinement

Draft -> validate -> refine -> finalize cycle.

```markdown
## Initial draft
Generate first version based on requirements.

## Quality check
Run validation. Identify: missing sections, formatting issues, data errors.

## Refinement
Address each issue. Regenerate affected sections. Re-validate.
Repeat until quality threshold met.

## Finalization
Apply final formatting. Generate summary.
```

### Context-Aware Tool Selection

Decision trees for choosing approaches based on context.

```markdown
## Determine approach
1. Check input type and constraints
2. Select method:
   - Small dataset: process inline
   - Large dataset: use script from scripts/
   - External data: fetch via MCP
3. Execute chosen approach
```

### Domain-Specific Intelligence

Embedded expertise, compliance checks, and audit trails.

```markdown
## Before processing
Apply domain rules:
- Check against compliance requirements
- Verify jurisdiction allowances
- Document compliance decision

## Processing
Execute only if compliance passed. Otherwise flag for review.

## Audit trail
Log all checks and decisions for traceability.
```

## File Structure Conventions

```
skill-name/
├── SKILL.md               # Main instructions (required)
├── scripts/               # Executable code Claude runs
│   └── validate.py        # Should work standalone
├── references/            # Domain knowledge Claude reads
│   └── api-guide.md       # Lazy-loaded when needed
└── assets/                # Templates, fonts, icons
    └── report-template.md # Used in output generation
```

- **scripts/**: Executable code for deterministic/repetitive tasks. Should work standalone.
- **references/**: Domain knowledge loaded into context as needed. Lazy-loaded.
- **assets/**: Templates, fonts, icons used in output generation.

## Structure Decision

**Default to simple** (single SKILL.md file).

Simple criteria:
- Single workflow or use case
- Under 200 lines of instructions
- One primary user intent

Complex criteria (any one triggers):
- Multiple distinct user intents requiring different workflows
- Large domain knowledge base (>300 lines would bloat SKILL.md)
- Reusable scripts that benefit from separate files
- Expected significant growth in scope

An empty `scripts/` or `references/` folder signals premature abstraction. Only add directories that earn their place.

## Progressive Disclosure

- Keep SKILL.md under 500 lines
- Reference files one level deep from SKILL.md
- For reference files >100 lines, include a table of contents
- Reference files clearly from SKILL.md with guidance on when to read them
