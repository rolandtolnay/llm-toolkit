---
name: linear
description: >
  Create, update, and comment on Linear tickets. Use when creating issues,
  adding comments, changing status, assigning work, or referencing issue IDs
  like ABC-123. Examples: "create a ticket", "add a comment", "mark done",
  "my issues".
---

<objective>
Conversational interface to Linear for fast issue management. Primary use case: user describes work → ask high-impact questions → create ticket immediately.

**Speed over polish.** Get tickets into Linear quickly.

**Do NOT explore the codebase** (launch agents, read files, analyze code) **unless the user explicitly asks.** Work from user's description only.
</objective>

<cli_reference>
**CLI script:** `~/.claude/skills/linear/scripts/linear.py`

Run with: `uv run ~/.claude/skills/linear/scripts/linear.py <command> [options]`

**Verbose flag (`-V`):** Available on `get` and `list` subcommands. **Always use concise (no `-V`) unless the user explicitly needs data only verbose provides.** Verbose adds URL, internal UUIDs, relations, and commit SHAs — data that inflates context without helping most operations.

Use `-V` only when the user:
- Asks for the URL or link to the issue
- Needs internal IDs (team, state, project UUIDs) for API calls
- Asks about relations (blocks, blocked-by) or linked commits
- Explicitly says "verbose", "full details", or "all fields"

**Commands:**
| Command | Usage | Purpose |
|---------|-------|---------|
| `create` | `create "<title>" [-d desc] [-p priority] [-e estimate] [--parent ID] [--project name] [--no-project] [--label name] [--assignee <name-or-email>]` | Create issue |
| `update` | `update <ID> [-t title] [-d desc] [-p priority] [-e estimate] [--parent ID] [--label name] [--no-labels] [--assignee <name-or-email>] [--no-assignee] [--project name] [--no-project]` | Update fields |
| `done` | `done <ID>` | Mark completed |
| `state` | `state <ID> "<name>"` | Change state |
| `break` | `break <ID> --issues '[{...}]' [--project name] [--no-project] [--label name] [--no-labels]` | Create sub-issues |
| `relate` | `relate <ID> <type> <target>` | Create relation (blocks, blocked-by, relates-to, duplicates) |
| `unrelate` | `unrelate <ID> <target>` | Remove relation between two issues |
| `comment` | `comment <ID> "<body>"` | Post a comment on an issue |
| `attach` | `attach <ID> <file_path> [-t title] [-s subtitle]` | Upload binary file (image, PDF) as download link |
| `attach-commit` | `attach-commit <ID> [commit-sha]` | Link git commit to issue (defaults to HEAD) |
| `document` | `document <ID> "<title>" [-c content] [-f file] [--project name]` | Create native markdown document viewable inline |
| `get` | `get <ID> [-c/--comments]` | Fetch details (add -c for comments) |
| `list` | `list [--mine] [--assignee X] [--creator X] [--priority X] [--project X] [--state X] [--estimate X] [--label name] [--limit N]` | List/filter issues |
| `states` | `states` | List workflow states |
| `projects` | `projects` | List available projects |
| `create-project` | `create-project "<name>" [-d desc] [--color hex] [--icon id] [--state state] [--start-date date] [--target-date date]` | Create project |
| `delete-project` | `delete-project "<name>"` | Delete project by name |
| `update-project` | `update-project "<name>" [--name new] [-d desc] [--color hex] [--icon id] [--state state] [--start-date date] [--target-date date]` | Update project |
| `members` | `members` | List active workspace members |
| `labels` | `labels [--team ID]` | List labels |
| `create-label` | `create-label "<name>" [--color hex] [-d desc]` | Create label |
| `delete-label` | `delete-label "<name>"` | Delete label by name |
| `update-label` | `update-label "<name>" [--name new] [--color hex] [-d desc]` | Update label (preserves issue associations) |

**Priority values:** 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low

**List filters:**
- `--mine` / `-m`: Issues assigned to current user
- `--assignee` / `-a`: By assignee email or name
- `--creator` / `-c`: By creator email or name
- `--priority` / `-p`: By priority (0-4 or none/urgent/high/normal/low)
- `--project`: By project name
- `--state` / `-s`: By state name or type (backlog/todo/started/done/canceled)
- `--estimate` / `-e`: By estimate (number or 'none' for unestimated)
- `--label`: By label name (repeatable for AND logic)
- `--limit` / `-l`: Max results (default 25)

Filters combine with AND logic.

**T-shirt to estimate mapping:**
- XS → 1, S → 2, M → 3, L → 5, XL → 8

**Project handling:**
- `--project "Name"` — Assign to project by name (overrides config default)
- `--no-project` — Don't assign to any project
- If neither specified, uses `projectId` from `.linear.json` if present

**Label handling:**
- `--label "name"` — Apply label by name (repeatable for multiple labels)
- `--no-labels` — Remove all labels (update) or skip parent inheritance (break)
- On `create`: if no `--label`, applies `defaultLabels` from `.linear.json`
- On `update`: `--label` replaces all existing labels
- On `break`: sub-issues inherit parent labels by default
</cli_reference>

<config>
**Project config:** `.linear.json` in project root (searched upward from pwd):

```json
{
  "teamId": "uuid-of-linear-team",
  "projectId": "uuid-of-linear-project (optional)",
  "defaultPriority": 3,
  "defaultLabels": ["mobile"]
}
```

- `teamId` — Required. Your Linear team UUID.
- `projectId` — Optional. Default project for new issues. Can be overridden with `--project` or `--no-project`.
- `defaultLabels` — Optional. Label names auto-applied on `create` when `--label` is not specified.

**API key:** Set `LINEAR_API_KEY` in project's `.claude/settings.local.json` (git-ignored by default):

```json
{
  "env": {
    "LINEAR_API_KEY": "lin_api_..."
  }
}
```
</config>

<process>

<step name="parse_intent">
**Parse the command to determine intent:**

| Pattern | Intent | Action |
|---------|--------|--------|
| `done <ID>` | Mark complete | Execute `done` directly |
| `state <ID> "<name>"` | Change state | Execute `state` directly |
| `get <ID>` | Fetch details | Execute `get` (returns comment count) |
| `get <ID> with comments`, `show comments on <ID>`, `read comments on <ID>` | Fetch with comments | Execute `get <ID> --comments` |
| `states` | List states | Execute `states` directly |
| `projects` | List projects | Execute `projects` directly |
| `"create a project"`, `"new project"` | Create project | Execute `create-project` directly |
| `"delete project"`, `"remove project"` | Delete project | Execute `delete-project` directly |
| `"update project"`, `"rename project"`, `"change project state"` | Update project | Execute `update-project` directly |
| `"move <ID> to project"`, `"set project on <ID>"` | Assign project | Execute `update <ID> --project <name>` |
| `"remove <ID> from project"`, `"unset project on <ID>"` | Remove project | Execute `update <ID> --no-project` |
| `labels`, `"list labels"`, `"show labels"` | List labels | Execute `labels` directly |
| `"create a label"`, `"new label"` | Create label | Execute `create-label` directly |
| `"delete label"`, `"remove label"` | Delete label | Execute `delete-label` directly |
| `"update label"`, `"rename label"`, `"change label color"` | Update label | Execute `update-label` directly |
| `list [filters]`, `my issues`, `show issues` | List/filter issues | Execute `list` with filters |
| `assign <ID> to <name>`, `reassign <ID> to <name>` | Assign/reassign | Execute `update <ID> --assignee <name>` |
| `unassign <ID>`, `remove assignee from <ID>` | Remove assignee | Execute `update <ID> --no-assignee` |
| `members`, `team members`, `who's on the team` | List members | Execute `members` directly |
| `update <ID> <text>` | Update issue | Execute `update` with parsed fields |
| `break <ID>` + user provides sub-issues | Break into sub-issues | Execute `break` with user's list |
| `relate <ID> blocks/blocked-by/relates-to/duplicates <ID>` | Create relation | Execute `relate` directly |
| `<ID> blocks/depends on <ID>`, `link <ID> to <ID>` | Create relation | Parse relation type and execute `relate` |
| `comment on <ID>`, `leave a comment on <ID>`, `add a note to <ID>`, `post comment` | Post comment | Execute `comment` with body text |
| `attach <ID> <file_path>` | Attach file | Execute `attach` directly |
| `attach-commit <ID> [sha]`, "add commit reference to <ID>", "link commit to <ID>" | Link git commit | Execute `attach-commit` directly (pass SHA for non-HEAD commits) |
| `document <ID> "<title>"`, `add document to <ID>`, `create doc on <ID>` | Create document | Execute `document` with title and content |
| User provides text/markdown content to add to an issue | Comment vs document | See **comment vs document** decision below |
| `<ID> <description>` | Create sub-issue | Go to create flow with parent |
| `<description>` | Create issue | Go to create flow |
| (empty) | No input | Ask what they want to do |

Issue ID pattern: 2-4 uppercase letters followed by hyphen and numbers (e.g., `ABC-123`, `PROJ-42`).

**Comment vs document vs attach vs attach-commit decision:**

| Command | Use for | Key signal |
|---------|---------|------------|
| `attach-commit` | **Git commit references** — linking implementation work to a ticket | Any mention of "commit", "commit hash", "link the commit". Always prefer over a comment containing a commit hash. |
| `comment` | **Conversational updates** — status notes, decisions, questions | "leave a comment", "add a note", "post an update" |
| `document` | **Structured editable content** — specs, design docs, research notes | "add a doc", `.md` file references, long-form specs (use `-f` for files, `-c` for inline) |
| `attach` | **Binary files** — images, PDFs, design files | File path to `.png`, `.pdf`, `.fig`, `.zip`; "attach this file", "upload this" |

Combined actions: "mark as done and add the commit" → `done` + `attach-commit`. "mark as done and leave a comment" → `done` + `comment`.

When ambiguous between comment and document, prefer `comment`.

**Comment quality — what to write:**

Focus on decisions, blockers, surprises, and state changes — not mechanical change inventories ("updated file X, changed Y to Z") visible in diffs. Extract the insight, not the inventory.

Good: "Switched from polling to SSE — polling hit rate limits under load. Estimate unchanged since the SSE client is already in the codebase."
Bad: "Updated api.py to use SSE instead of polling. Changed the import on line 12. Added error handler on line 45."

**Scope-change awareness — re-evaluate priority and estimate:**

When adding a comment or updating a ticket's description that changes the scope of work (new ideas, expanded requirements, refined approach), always consider whether the priority and estimate still fit. Users often brainstorm on existing tickets — capturing new ideas via comments or rewriting descriptions — without explicitly thinking about how this affects sizing.

- After writing a comment or updating a description that changes scope, check the current priority and estimate
- If the new content meaningfully expands or narrows the work, adjust priority and/or estimate in the same `update` call
- Mention the adjustment in the output (e.g., "Bumped estimate S→M to reflect expanded scope")
- If scope changed but priority/estimate still fit, no action needed — don't adjust for the sake of it
</step>

<step name="resolve_assignee">
**When the user mentions an assignee casually (e.g., "assign to Roland", "give this to Sarah", "create a ticket for Alex"):**

1. Run `members` to fetch the active member list
2. Fuzzy match the name in-context (first name, last name, display name, or email)
3. If exactly one match, use `--assignee` with that name
4. If multiple matches, use AskUserQuestion to disambiguate with the matching names as options
5. If no match, show available members and ask the user to clarify
</step>

<step name="direct_commands">
**For direct commands (done, state, get, states, projects, create-project, delete-project, update-project, labels, create-label, delete-label, update-label, update, comment, attach-commit, members):**

Execute CLI and format output.

```bash
uv run ~/.claude/skills/linear/scripts/linear.py [command] [args]
```

**Description round-trip sanitization:** When updating a description fetched from `get`, strip Linear's auto-linked URLs before sending — the API rejects angle-bracket URLs as "invalid issue description". Example: `[**state.md**](<http://state.md>)` → `**state.md**`. Match the regex `\[([^\]]+)\]\(<http://[^>]+>\)` and replace with capture group 1.

Parse JSON response and present result:
- Success: Show identifier, title, new state, and URL
- For `projects`/`labels`: List grouped by team
- Error: Show error message and suggestions
</step>

<step name="create_flow">
**For create/sub-issue — FAST PATH:**

1. **Parse input for hints:**
   - Title from first sentence or quoted text
   - Priority hints: "urgent", "high priority", "low priority", "blocker"
   - Estimate hints: "XS", "S", "M", "L", "XL", "small", "medium", "large"
   - Parent ID if pattern `<ID> <description>`
   - Project hints: "in [Project]", "for [Project]", "(project: [Name])", "[Project] project"

2. **Infer project and labels** from the description:

   Run `projects` and `labels` to fetch available options (cache across the session — don't re-fetch if already retrieved this conversation).

   **Project inference:**
   - If user explicitly named a project in their message → use it
   - Otherwise, match the ticket's domain/area against available project names and descriptions
   - If exactly one project is a clear match → pre-select it (confirm in step 4)
   - If multiple plausible matches or no match → include project selection in step 4's AskUserQuestion
   - If no projects match and the ticket represents a new area of work → include a "Create new project: [suggested name]" option in step 4

   **Label inference:**
   - If user explicitly named labels → use them
   - Otherwise, match against available labels by category (e.g., platform, area, type)
   - Pre-select labels that clearly apply (confirm in step 4)
   - If the ticket's domain suggests a label that doesn't exist → include a "Create label: [suggested name]" option in step 4
   - `defaultLabels` from `.linear.json` still apply as baseline — inferred labels are additive

3. **Infer priority and estimate** from the description:

   **Priority inference — based on user impact:**

   Priority reflects how many users are affected and how central the affected flow is to the product. Not how hard the fix is (that's what estimate captures).

   Score by asking: how many users benefit, how central is this to what makes the product valuable, and does it move a success metric (engagement, growth, retention, monetization)?

   | Priority | Bugs / Issues | New Features / Improvements |
   |----------|--------------|----------------------------|
   | Urgent (1) | **Broken core flow.** Most users hit this. Blocked, losing data, cannot work around it. | Rare for features. Only if a critical gap is actively causing churn or blocking a launch. |
   | High (2) | **Degraded core flow OR broken secondary flow.** Core flow works but with significant friction or incorrect behavior. OR a regularly-used secondary flow is broken. | **Strengthens the core USP.** Directly tied to the product's unique value proposition or the core problem it solves. Benefits most users. Likely to drive engagement, retention, or growth. |
   | Normal (3) | **Non-critical bug.** Affects a moderate number of users or a less common flow. Workaround exists. | **Meaningful improvement.** Elevates an existing flow or adds a useful capability. Benefits a decent user segment. Improves satisfaction but not directly tied to the core differentiator. |
   | Low (4) | **Edge case or cosmetic.** Small subset of users, rare trigger, visual-only. | **Peripheral or niche.** Benefits few users, adds to a rarely-used flow, or is a nice-to-have that doesn't move a success metric. |

   **Quick signals (disambiguation beyond the table):**
   - "Users can't ___" → Urgent or High
   - "Users have to work around ___" → High
   - "This would make ___ much better" → Normal
   - "Sometimes when ___ happens" (edge case) → Low
   - "It would be nice if ___" → Low
   - Feature that drives engagement/retention/monetization → bump up one level

   **Estimate inference — calibrated for Claude Code development:**

   Estimates reflect effort when Claude Code does the implementation. Repetitive refactoring across files may be easy for AI; work needing context discovery may be harder.

   | Estimate | Criteria | Effort signals |
   |----------|----------|----------------|
   | XS (1) | 1 file, clear fix, no ambiguity. Config change, typo fix, remove dead code. | Isolated, no downstream consumers, additive only |
   | S (2) | 1-2 files, known approach. Single-file rewrite, pure research/audit with no code changes. | Known approach, clear root cause |
   | M (3) | 2-5 files, known approach but coordination needed. Template + references update, new agent mirroring existing pattern. | Some coordination, one obvious approach |
   | L (5) | 5+ files, OR requires investigation, OR replaces existing functionality. New command with workflow, multi-file migration. | Investigation required, multiple valid approaches, breaking changes |
   | XL (8) | Architectural change, OR 8+ files, OR fundamentally changes a major system part. New subsystem, cross-cutting refactor, deprecating multiple commands. | Core path with many dependents, fundamentally changes major system |

   **Quick signals:**
   - Pure research/audit (no code changes) → cap at S (2)
   - Root cause already known (in comments/description) → reduce by one size
   - "Evaluate whether" / "investigate" → at least M (3) for the decision overhead
   - Replacing N existing commands/workflows → at least L (5)
   - Parent ticket with sub-issues → remove estimate from parent (sub-issues carry their own)

4. **Check for "problem to solve":**

   If the user only provided implementation details (e.g., "add a retry flag to the API call") without a user-facing problem, ask: "What's the problem you're solving from a user perspective?" before proceeding. The answer becomes the ticket's core framing.

   Skip this check if the user already stated a problem (e.g., "users lose data when the connection drops").

5. **Ask UP TO 4 questions in ONE AskUserQuestion call:**

   Combine these into a single batch:

   **Confirmation question:** Show inferred priority/estimate and inferred project/labels, ask to confirm or adjust

   **Project/label question (if needed):**
   - If project is ambiguous or unmatched → list matching projects as options, include "Create new project: [name]" if appropriate
   - If labels need confirmation or a new label is suggested → list as multi-select options, include "Create label: [name]" for new ones
   - If project and labels were confidently inferred → just show them in the confirmation question, no separate question needed

   **High-impact domain questions (pick 1-2 most relevant):**
   - Scope clarification: "Should this [specific behavior] or [alternative]?"
   - Edge cases: "What should happen when [edge case]?"
   - Acceptance criteria: "What's the minimum for this to be done?"
   - Context: "Is this related to [existing feature/area]?"

   Skip questions with obvious answers from description. If description is very clear, may only need confirmation.

6. **Create immediately after answers:**

   If user approved creating a new project or label, create it first via `create-project` or `create-label`, then use the result in the `create` command.

   Structure the description as:

   ```markdown
   ## Problem
   [1-2 sentences: the user-facing problem or need]

   ## Solution
   [1-3 sentences: what this ticket delivers]

   ## Details
   - [Key requirements or constraints from user's answers]
   ```

   Omit `## Details` if there's nothing beyond what Problem/Solution already covers. Keep it concise — a few lines beats a wall of text.

   ```bash
   uv run ~/.claude/skills/linear/scripts/linear.py create "[title]" \
     -d "[structured description]" -p [priority] -e [estimate] \
     [--parent ID] [--project "Name"] [--label "name"] [--no-project]
   ```

7. **Format result:**

   ```
   Created: **[identifier]** — [title]
   Project: [project name] | Labels: [label1, label2]
   [url]
   ```
</step>

<step name="break_flow">
**For breaking down issues:**

User provides the sub-issues in conversation. Do NOT propose or generate sub-issues.

1. **Get sub-issue list from user** (they specify titles/estimates in their message)

2. **Build JSON and execute:**

   ```bash
   uv run ~/.claude/skills/linear/scripts/linear.py break [ID] \
     --issues '[{"title":"...","estimate":3},{"title":"...","estimate":2}]'
   ```

3. **Format result:**

   ```
   Created N sub-issues under [parent-identifier]:
   - **[ID-1]** — [title 1]
   - **[ID-2]** — [title 2]
   ```
</step>

<step name="error_handling">
**Handle errors gracefully:**

- **MISSING_API_KEY:** Explain how to set LINEAR_API_KEY in project `.claude/settings.local.json`
- **MISSING_CONFIG:** Explain how to create .linear.json
- **ISSUE_NOT_FOUND:** Suggest checking the identifier
- **STATE_NOT_FOUND:** List available states from `states` command
- **PROJECT_NOT_FOUND:** List available projects from `projects` command
- **LABEL_NOT_FOUND:** List available labels from `labels` command
- **FILE_NOT_FOUND:** Suggest checking the file path
- **UPLOAD_FAILED:** Suggest retrying or checking connectivity

Always parse JSON error response and present human-friendly message with suggestions.
</step>

</process>

<success_criteria>
- [ ] No codebase exploration unless user explicitly requests it
- [ ] Create flow infers project and labels from available options before asking questions
- [ ] Create flow asks max 4 questions in ONE AskUserQuestion call
- [ ] Issue created immediately after user answers questions
- [ ] Errors handled with helpful suggestions
- [ ] Direct commands execute immediately without questions
- [ ] CLI output parsed and formatted for readability
</success_criteria>
