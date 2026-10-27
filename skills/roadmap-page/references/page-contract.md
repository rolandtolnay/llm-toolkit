# Roadmap page contract

A roadmap page is one HTML file plus a Linear snapshot beside it. The page holds everything a person wrote for it in two embedded JSON blocks and is committed; the snapshot holds only what anyone can fetch again from Linear, so the project ignores it in git. A fixed script renders them with no build, server or network; its web fonts load from Google Fonts when online and fall back to system faces offline. The server script `roadmap.mjs` refreshes the snapshot from Linear and runs self-heal passes; the page shows its Refresh and Self-heal buttons only when served by that script.

```html
<script id="roadmap-config"   type="application/json">{ ...curated content... }</script>
<script id="roadmap-guidance" type="application/json">{ "tasks": [ ...per-ticket guidance... ] }</script>
<script id="roadmap-snapshot" src="<page>.snapshot.js"></script>
```

The `src` names the snapshot file relative to the page, usually `<page name>.snapshot.js`, and the project's `.gitignore` lists it. It is a script (`window.ROADMAP_SNAPSHOT = {...};`) rather than JSON so the page still loads it when opened as a plain file. Without it, as in a fresh checkout, the page renders its config, shows no tickets and asks for a refresh.

Ticket identifiers are Linear identifiers such as `ORF-19`, everywhere.

## roadmap-config: curated content

Written when the page is created and edited by self-heal passes. Nothing here is read from Linear.

| Field | Meaning |
|---|---|
| `product` | Product name for the wordmark and tab title. |
| `title` | Subtitle next to the wordmark, usually "Your roadmap". |
| `command` | How to open the page from the project, shown in the footer and hints. |
| `focus` | The `id` of the phase shown first. Defaults to the first phase. |
| `targetDate`, `targetLabel` | Optional ISO date and a short label ("the wedding") for the focus phase's countdown, used only when none of its projects has an open milestone with a target date. |
| `phases[]` | Ordered release phases. Each has `id`, `name`, `short` (nav caption), `title` and `description` (hero), `projects` (Linear project names that belong to it), and for later phases `intro` and `body` (the explanation shown instead of next-up cards). Optional `allWork` and `laterNote` replace the default work-list descriptions. Optional `sources`: identifiers of the Linear issues the phase's plan is written in (a Wayfinder map, a brief); the server reads them on refresh. `reviewedHash`: the phase `sourceHash` (snapshot) the phase copy, its lanes and the guide were last checked against; the recheck pass sets it. |
| `lanes[]` | Areas of the focus phase. Each has `id`, `name`, `summary`, `detail`, `ids` (identifiers in recommended order). Lanes group work; they are not blockers. |
| `nextUp` | Identifiers in the order the person would start them. Next-up cards rank by leverage and use this order to break ties; see Next-up cards below. An older `{agent, owner, plan}` object is read as one list. |
| `finalTicket` | Optional `{id, label, note, enables}` for the ticket the phase converges on. |
| `ownerLabel` | Linear label that marks work the person must do themselves. The server sets `owner` on tasks from it. |
| `excludeLabelPrefixes` | Tickets with a label starting with one of these prefixes are not tracked (planning or meta tickets). |
| `startableStateTypes` | State types the page treats as "selected to start". Default `["unstarted"]` (Todo). Add `"backlog"` for teams that start work straight from Backlog. |
| `workflowLabels`, `estimateLabels` | Optional display overrides. |
| `openers` | Session prompt overrides per workflow (`scope`, `prep`, `owner`) and for guidance reviews (`review`, `new`). `{id}` and `{title}` are replaced. The defaults follow the session workflows below. |
| `prepFollowUp` | Optional override for the sentence shown after a prep opener, which by default points at `{skill:cook-prd}`. |
| `gates` | Optional titles and bodies for the gate sections: `title`, `body`, `enablesTitle`, `enablesBody`. |
| `guide[]`, `guideFooter` | The "Working with an agent" section: `{title, body}` items and a closing note. |
| `fallbacks` | Optional `{title, paragraphs[]}` for a "if the schedule gets tight" section. |

Skill commands in `openers`, `prepFollowUp` and `guide` are written as `{skill:name}`. The page spells them per harness: `/name` for Claude Code, `/skill:name` for Pi, `$name` for Codex. Each skill has a home harness set in the template: `wayfinder` runs in Claude Code, and `scope`, `prep` and `cook-prd` in Pi. A session prompt opens in the home of its first skill, and a prompt that names no skill, such as an owner walk-through, opens in Claude Code. The drawer's session box can respell its prompt and the prep follow-up for another harness; the choice is not remembered, so the next drawer opens on its own default. The guide spells each command for its skill's home.

## roadmap-guidance: per-ticket guidance

Written when the page is created and edited by self-heal passes; a refresh never changes it. `tasks[]` holds one entry per curated ticket with its `id` and the *curated* fields in the table below. The page and the server overlay each entry on the snapshot task with the same `id`. A curated ticket stays tracked after it leaves the configured projects until its entry is removed.

## Snapshot file: Linear facts

Written by the server on every refresh and never edited by hand or by a self-heal. Fields marked **fact** and *derived* live here; fields marked *curated* live in `roadmap-guidance`, and the snapshot carries placeholder values for them only on tickets that have no guidance entry yet.

Top level: `checkedAt` (fact), `trackingSince`, `stateTypes` (fact: state name to type map), `milestones[]` (fact: `{project, name, targetDate, status}` for every milestone of the configured projects, `status` as Linear computes it), `phases[]` (fact: `{id, sourceHash, sources[]}` per config phase, where `sourceHash` hashes the names and dates of its projects' milestones and the title and description of each issue in its `sources`, never milestone status, and `sources[]` carries `{id, title, url}`), `refresh` (`{ok, attemptedAt, error?}`), `heal.lastRun` (written after each self-heal), `tasks[]`.

Each task:

| Field | Kind | Meaning |
|---|---|---|
| `id`, `number`, `url` | fact | Identifier, numeric part, Linear URL. |
| `linearTitle` | fact | The title in Linear. |
| `state`, `stateType` | fact | State name and Linear type (`triage`, `backlog`, `unstarted`, `started`, `completed`, `canceled`, `duplicate`). `unknownState` is set when the type is not one of these. |
| `assignee`, `estimate`, `priority`, `labels`, `projectName`, `projectId`, `parent`, `children`, `truncated` | fact | As reported. |
| `blockedBy[]` | fact | Identifiers of native "blocked by" relations. |
| `phase` | derived | Phase id whose `projects` include the ticket's project, else `later`. |
| `referenceOnly` | derived | True for blockers pulled in from outside the configured projects. They render in relations but not in lists. |
| `missing` | derived | Linear no longer returns the ticket. |
| `owner` | derived | Ticket carries `ownerLabel`. |
| `sourceHash` | fact | Hash of title, description, project, labels and blockers. Status, assignee, estimate and comments are deliberately excluded so routine changes never flag a review. |
| `title`, `summary`, `detail`, `input` | curated | Reader-facing guidance. `title` is a humanized name; `linearTitle` stays as the source. |
| `workflow` | curated | `scope`, `prep` or `owner`; see Session workflows. The server gives uncurated tickets the placeholder `review` until they are integrated. |
| `opener` | curated | Optional session prompt for this ticket alone, filled like `openers`; see Session workflows. |
| `gates[]` | curated | Identifiers of prerequisites that are not native blockers (service approvals, access). Local work may start before gates clear. |
| `curated` | curated | False until guidance was written for the ticket. The page shows "New: needs integration" while false. |
| `reviewedHash` | curated | The `sourceHash` the guidance was last checked against. |
| `reviewRequired` | derived | Computed when guidance and snapshot are combined, not stored: the ticket is missing, or `sourceHash` differs from both `reviewedHash` and `aiGuidance.sourceHash`. |
| `aiGuidance` | curated | Optional `{sourceHash, updatedAt, model}` when a self-heal wrote the guidance; the page labels it "AI-updated". |

## Session workflows

Each ticket gets one `workflow`, which picks the session prompt in its drawer. Classify by how the person will start the work:

- `scope`: bounded code work where the agent can make the remaining decisions itself, because the risk is low or few decisions are left. Opens with `{skill:scope} {id}`: the skill confirms a short frame, then builds in the same session.
- `prep`: every other code change, and the default for anything substantial: a feature, work across several areas, a new provider or data migration, or work whose product, UX or architecture choices the person will want to steer. Also the choice when the ticket is too thin to judge. Opens with `{skill:prep} {id}`: an interview that produces a PRD, which `{skill:cook-prd} <prd path>` then builds in a fresh session.
- `owner`: no code output. The person does the work in a conversation with the agent: setting up third-party providers, accounts and credentials, or making business and policy decisions. Opens with a walk-through prompt that takes one step or decision at a time and verifies each step before the next. Tickets carrying `ownerLabel` are always owner work.

When unsure between `scope` and `prep`, choose `prep`. The estimate is a hint, not the rule: a small ticket that settles a product rule (who gets access, what a user sees) is `prep`, and a large ticket whose behaviour is fully specified can be `scope`. Session prompts are the skill command and the ticket identifier only; the skills read the ticket themselves.

The drawer's prompt is the one the person copies, so it must fit the ticket. When the workflow's prompt in `openers` does not fit one ticket, for example owner work outside the skill that `openers.owner` names, set that ticket's `opener` to a prompt that does.

## Status rules the page applies

Order matters; the first matching rule wins.

1. Missing in Linear, unrecognised state type, archived, done, canceled or duplicate: shown as closed or alert, never suggested.
2. `started`: shown in the "In progress right now" strip with the tickets it unblocks; never suggested. Tickets whose unmet blockers are all in progress show "Waiting on work in progress" and can appear as "Ready after current work" when nothing else is ready.
3. Assigned but not started: "Assigned to …", not suggested.
4. Not curated: "New: needs integration". Curated but `reviewRequired`: "Guidance needs review". Both appear in the review notice with a Self-heal shortcut.
5. Unmet blockers: waiting. Outside the focus phase or reference-only: outside the current phase.
6. State type not in `startableStateTypes`: "Not selected to start" (Backlog work is visible but not suggested).
7. Owner work: "Your move". Unmet gates: "Local work can start". Otherwise: "Can start".

The hero counts down to the earliest milestone of the viewed phase's projects that has a target date and is not `done`, showing it as overdue once the date passes. Milestones without a date are skipped, and with none left the focus phase falls back to `targetDate`.

## Next-up cards

The three cards rank the open tickets of the focus phase by leverage: the number of open tickets that wait on a ticket through `blockedBy` or `gates`, directly or through other tickets. `nextUp` order, then Linear priority, break ties.

1. "Start here": the ready agent ticket (`scope` or `prep`) with the most leverage. When none is ready, the card shows an agent ticket whose unmet blockers are all in progress as "Ready after current work", or names the blocked agent ticket with the most leverage and what it waits on.
2. "Waiting on you": the ready owner ticket with the most leverage.
3. "Also ready": the next ready agent ticket, which can proceed in parallel with the first.

Each card states what the ticket unblocks, and an empty card says why nothing qualifies.

## Self-heal passes

The server launches `claude -p` (model `opus`, medium effort, `--safe-mode` so no CLAUDE.md, skills, plugins, hooks or MCP servers; tools Read, Edit, Write, Bash, Grep and Glob, with edits and Bash pre-approved and anything else denied) in the project root with `heal-prompts/contract.md` and this contract appended to the system prompt and one of the templates as the prompt. The findings a template receives carry the description and the last ten comments of every ticket they name (and of a flagged phase's sources), read by the server through the CLI just before the run, so the agent reads Linear itself only for tickets outside the findings. Templates: `integrate-new`, `reconcile-states`, `recheck-guidance` (tickets whose `sourceHash` moved, and phases whose `sourceHash` differs from their `reviewedHash`: milestones renamed, added or removed, or a source issue rewritten; the pass rewrites the phase copy, lanes and guide the change contradicts and sets `reviewedHash`), `next-phase` (makes the next phase with open work the focus: new lanes, next-up order and phase copy; offered as pending once the focus phase has no open work left), `custom`. Self-heal edits only the page, never the snapshot file. Before the run the page is backed up to `~/.cache/roadmap-page/<hash>/`; after it the file must still contain both JSON blocks, the snapshot tag, a parseable script, a body and the task list, or it is restored. Files changed outside the page are reported, not reverted. The page's "Revert last self-heal" button restores the latest backup.
