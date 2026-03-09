# Complex Skill Template

For skills with multiple workflows, large reference material, or reusable scripts.

## Directory Structure

```
{{skill-name}}/
├── SKILL.md               # Main instructions + essential principles
├── references/            # Domain knowledge (lazy-loaded)
│   ├── {{topic-1}}.md
│   └── {{topic-2}}.md
├── scripts/               # Executable code (if needed)
│   └── {{script}}.py
└── templates/             # Output structures (if needed)
    └── {{template}}.md
```

Only add directories that earn their place.

## SKILL.md Template

```yaml
---
name: {{skill-name}}
description: {{What it does — distinct verb}}. Use when {{trigger conditions}}.
---
```

```xml
<essential_principles>
{{Principles that always apply, regardless of workflow. Keep to 3-5 items, 1-2 sentences each.}}

1. {{First principle — why it matters}}
2. {{Second principle — why it matters}}
3. {{Third principle — why it matters}}
</essential_principles>

<process>
## Step 1: {{First action}}
{{Instructions}}

## Step 2: {{Second action}}
{{Instructions}}

## Step 3: {{Third action}}
{{Instructions — include lazy-load triggers for reference files}}
Read `references/{{topic-1}}.md` before proceeding.
</process>

<reference_index>
Supporting files in `references/`:
- `{{topic-1}}.md` — {{purpose, when to read}}
- `{{topic-2}}.md` — {{purpose, when to read}}
</reference_index>

<success_criteria>
- [ ] {{Highest skip-risk criterion first}}
- [ ] {{Second highest}}
- [ ] {{Third}}
- [ ] {{Fourth}}
- [ ] {{Fifth}}
</success_criteria>
```

## Notes

- Keep SKILL.md under 500 lines — move detailed content to references
- Reference files should be one level deep
- For reference files >100 lines, include a table of contents
- `<essential_principles>` should contain only what's needed on every execution path
- Scripts in `scripts/` should work standalone
