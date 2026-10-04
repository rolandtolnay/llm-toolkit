# Roadmap page contract

A roadmap page is one self-contained HTML file. It renders two embedded JSON blocks with a fixed script and needs no build, server or network to display. The server script `roadmap.mjs` refreshes the data block from Linear and runs self-heal passes; the page shows its Refresh and Self-heal buttons only when served by that script.

```html
<script id="roadmap-config" type="application/json">{ ...curated content... }</script>
<script id="roadmap-data"   type="application/json">{ ...Linear snapshot... }</script>
```

Ticket identifiers are Linear identifiers such as `ORF-19`, everywhere.

## roadmap-config: curated content

Written when the page is created and edited by self-heal passes. Nothing here is read from Linear.

| Field | Meaning |
|---|---|
| `product` | Product name for the wordmark and tab title. |
| `title` | Subtitle next to the wordmark, usually "Your roadmap". |
| `command` | How to open the page from the project, shown in the footer and hints. |
| `focus` | The `id` of the phase shown first. Defaults to the first phase. |
| `targetDate`, `targetLabel` | Optional ISO date and a short label ("the wedding") for the countdown. |
| `phases[]` | Ordered release phases. Each has `id`, `name`, `short` (nav caption), `title` and `description` (hero), `projects` (Linear project names that belong to it), and for later phases `intro` and `body` (the explanation shown instead of next-up cards). Optional `allWork` and `laterNote` replace the default work-list descriptions. |
| `lanes[]` | Areas of the focus phase. Each has `id`, `name`, `summary`, `detail`, `ids` (identifiers in recommended order). Lanes group work; they are not blockers. |
| `nextUp` | `{agent:[], owner:[], plan:[]}` identifier lists that order the three next-up cards before priority ordering takes over. |
| `nextUpReasons` | Optional overrides for the card captions: `agent`, `agentScope`, `owner`, `plan`, `soon`. |
| `finalTicket` | Optional `{id, label, note, enables}` for the ticket the phase converges on. |
| `ownerLabel` | Linear label that marks work the person must do themselves. The server sets `owner` on tasks from it. |
| `excludeLabelPrefixes` | Tickets with a label starting with one of these prefixes are not tracked (planning or meta tickets). |
| `startableStateTypes` | State types the page treats as "selected to start". Default `["unstarted"]` (Todo). Add `"backlog"` for teams that start work straight from Backlog. |
| `workflowLabels`, `estimateLabels` | Optional display overrides. |
| `openers` | Session prompt templates per workflow: `go`, `scope`, `prep`, `owner`, `review`, `new`. `{id}` and `{title}` are replaced. Point them at the project's own skills where they exist. |
| `prepFollowUp` | Optional sentence shown after a prep opener. |
| `gates` | Optional titles and bodies for the gate sections: `title`, `body`, `enablesTitle`, `enablesBody`. |
| `guide[]`, `guideFooter` | The "Working with an agent" section: `{title, body}` items and a closing note. |
| `fallbacks` | Optional `{title, paragraphs[]}` for a "if the schedule gets tight" section. |

## roadmap-data: Linear snapshot

Written by the server. Fields marked **fact** come from Linear and must not be edited by hand or by a self-heal; the next refresh overwrites them anyway. Fields marked *curated* survive refreshes.

Top level: `checkedAt` (fact), `trackingSince`, `stateTypes` (fact: state name to type map), `refresh` (`{ok, attemptedAt, error?}`), `heal.lastRun` (written after each self-heal), `tasks[]`.

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
| `workflow` | curated | `go`, `scope`, `prep`, `owner` or `review`. |
| `gates[]` | curated | Identifiers of prerequisites that are not native blockers (service approvals, access). Local work may start before gates clear. |
| `curated` | curated | False until guidance was written for the ticket. The page shows "New: needs integration" while false. |
| `reviewedHash` | curated | The `sourceHash` the guidance was last checked against. |
| `reviewRequired` | derived | `sourceHash` differs from both `reviewedHash` and `aiGuidance.sourceHash`. |
| `aiGuidance` | curated | Optional `{sourceHash, updatedAt, model}` when a self-heal wrote the guidance; the page labels it "AI-updated". |

## Status rules the page applies

Order matters; the first matching rule wins.

1. Missing in Linear, unrecognised state type, archived, done, canceled or duplicate: shown as closed or alert, never suggested.
2. `started`: shown in the "In progress right now" strip with the tickets it unblocks; never suggested. Tickets whose unmet blockers are all in progress show "Waiting on work in progress" and can appear as "Ready after current work" when nothing else is ready.
3. Assigned but not started: "Assigned to …", not suggested.
4. Not curated: "New: needs integration". Curated but `reviewRequired`: "Guidance needs review". Both appear in the review notice with a Self-heal shortcut.
5. Unmet blockers: waiting. Outside the focus phase or reference-only: outside the current phase.
6. State type not in `startableStateTypes`: "Not selected to start" (Backlog work is visible but not suggested).
7. Owner work: "Your move". Unmet gates: "Local work can start". Otherwise: "Can start".

Next-up cards pick the first eligible ticket from `nextUp.agent` (workflow go or scope), `nextUp.owner`, `nextUp.plan` (workflow prep), falling back to Linear priority.

## Self-heal passes

The server launches `pi -p` (model `openai-codex/gpt-6.1-sol`, medium effort, tools read/edit/write/bash, no project extensions or context files) in the project root with `heal-prompts/contract.md` appended to the system prompt and one of the templates as the prompt. Templates: `integrate-new`, `reconcile-states`, `recheck-guidance`, `custom`. Before the run the page is backed up to `~/.cache/roadmap-page/<hash>/`; after it the file must still contain both JSON blocks, a parseable script, a body and the task list, or it is restored. Files changed outside the page are reported, not reverted. The page's "Revert last self-heal" button restores the latest backup.
