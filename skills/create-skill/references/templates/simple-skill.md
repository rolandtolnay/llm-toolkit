# Simple Skill Template

Fill in `{{placeholders}}` with your content.

```yaml
---
name: {{skill-name}}
description: {{What it does — distinct verb}}. Use when {{trigger conditions}}.
---
```

```xml
<objective>
{{Clear statement of what this skill accomplishes and why}}
</objective>

<process>
## Step 1: {{First action}}
{{Instructions — be specific and actionable}}

## Step 2: {{Second action}}
{{Instructions}}

## Step 3: {{Third action}}
{{Instructions}}
</process>

<success_criteria>
- [ ] {{Highest skip-risk criterion first}}
- [ ] {{Second highest}}
- [ ] {{Third}}
</success_criteria>
```

## Notes

- Add `<examples>` when output format matters — show, don't tell
- Add anti-patterns only for observed failure modes
- Keep total skill under 200 lines
- Optional: `<context>` tag for background information that frames the task
- Optional: `<references>` tag pointing to supporting files if needed
