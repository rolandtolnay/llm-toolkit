# Custom Views Reference

## CLI Commands

| Command | Usage | Purpose |
|---------|-------|---------|
| `views` | `views [--team ID] [-V]` | List custom views. `-V` adds filterData, icon, color, timestamps |
| `create-view` | `create-view "<name>" [--filter-json '{...}'] [--shared] [--team ID] [--color hex] [--icon name] [-d desc]` | Create custom view |
| `delete-view` | `delete-view "<name-or-id>"` | Delete custom view by name or UUID |

## View Creation Process

**Before constructing ANY filter, you MUST run discovery:**

1. `labels` → exact label names available in the workspace
2. `states` → exact state names and types for the team
3. `projects` → exact project names
4. `views` → existing views (avoid duplicates, understand what's already covered)

Construct `--filter-json` using **ONLY** values returned by these commands. Never guess at label names, state names, or project names.

**Principles for useful views:**

- Every view needs a clear purpose: triage, focus, review, or tracking
- Combine 2-3+ filter dimensions to be meaningfully specific — a single-dimension filter ("all bugs") is rarely useful
- Use relative dates over absolute dates so views stay fresh without manual updates
- `assignee.isMe` is powerful for personal views ("my urgent work", "my recent completions")
- Exclude completed/cancelled states unless the view is specifically about completed work
- Name views for what they surface, not how they filter: "Fires" not "Priority 1-2 AND state started"
- Choose icon/color that reinforces the view's purpose at a glance

**Icon and color:**

- `--color` accepts any hex string (e.g. `#FF6B6B`)
- `--icon` accepts a PascalCase string (e.g. `Bug`, `Target`, `Home`, `AlertCircle`, `Clock`, `User`)
- To discover known-good icon values, run `views -V` or query existing projects — reuse values already in use
- Invalid icons are silently ignored by the API (not a crash risk)

## filterData Schema

### Fields

| Field path | Type | Values / notes |
|---|---|---|
| `priority` | number | 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low |
| `state.type` | string | `backlog`, `unstarted`, `started`, `completed`, `cancelled` |
| `state.name` | string | Exact state name from `states` command |
| `assignee.email` | string | User email address |
| `assignee.isMe` | boolean | `{"eq": true}` = current API key owner |
| `assignee` | null check | `{"null": true}` = unassigned |
| `label.name` | string | Exact label name from `labels` command |
| `project.name` | string | Exact project name from `projects` command |
| `cycle.number` | number | Cycle number |
| `estimate` | number | Point value |
| `dueDate` | date | ISO 8601 absolute or relative duration |
| `createdAt` | date | ISO 8601 absolute or relative duration |
| `completedAt` | date | ISO 8601 absolute or relative duration |
| `team.key` | string | Team key (e.g. "ENG") |

### Comparators

| Category | Operators |
|---|---|
| Number / enum | `eq`, `neq`, `in`, `nin`, `lt`, `lte`, `gt`, `gte` |
| String | `eq`, `neq`, `in`, `nin`, `contains`, `notContains`, `startsWith`, `endsWith` (append `IgnoreCase` for case-insensitive) |
| Null check | `{"null": true}` (has no value) / `{"null": false}` (has a value) |
| Date | Same as number, plus relative durations |

### Relative Dates (ISO 8601 durations)

| Duration | Meaning |
|---|---|
| `-P2W` | 2 weeks ago |
| `-P3D` | 3 days ago |
| `-P1M` | 1 month ago |
| `P0D` | today |
| `P1W` | 1 week from now |
| `P1M` | 1 month from now |

### Logic

- **Top-level keys = AND.** All conditions must match.
- **OR:** `"or": [condition1, condition2, ...]` — any must match.
- **Explicit AND:** `"and": [condition1, condition2, ...]` — all must match (useful for grouping).
- **Collections** (label, etc.): default = any match. Use `"every": {...}` for all-must-match.

## Examples

**My urgent/high issues:**
```json
{
  "assignee": {"isMe": {"eq": true}},
  "priority": {"in": [1, 2]},
  "state": {"type": {"nin": ["completed", "cancelled"]}}
}
```

**Bugs in progress:**
```json
{
  "label": {"name": {"in": ["bug"]}},
  "state": {"type": {"in": ["started"]}}
}
```

**Unassigned backlog:**
```json
{
  "assignee": {"null": true},
  "state": {"type": {"in": ["backlog", "unstarted"]}}
}
```

**Overdue issues:**
```json
{
  "dueDate": {"lt": "P0D"},
  "state": {"type": {"nin": ["completed", "cancelled"]}}
}
```

**High priority OR blocker label (OR logic):**
```json
{
  "or": [
    {"priority": {"in": [1, 2]}},
    {"label": {"name": {"in": ["blocker"]}}}
  ],
  "state": {"type": {"nin": ["completed", "cancelled"]}}
}
```

**Created in last 2 weeks, still open:**
```json
{
  "createdAt": {"gt": "-P2W"},
  "state": {"type": {"nin": ["completed", "cancelled"]}}
}
```
