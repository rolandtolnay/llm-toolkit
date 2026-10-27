---
name: roadmap-page
description: Create or update a self-contained HTML roadmap page from a set of tickets (Linear today), with a local server that refreshes it and a self-heal button that runs headless Claude Code. Use when asked for a roadmap, a plan view or a "what should I work on next" page built from ticket projects.
---

# Roadmap page

The output is one committed HTML file in the consumer project, usually `etc/roadmap/<name>.html`, built from `~/.agents/skills/roadmap-page/templates/roadmap.html`, plus a git-ignored `<name>.snapshot.js` beside it that the server writes on every refresh. The page shows a release-phase plan: an "In progress right now" strip, three next-up cards (the ready agent ticket that unblocks the most work, the owner action that unblocks the most, and a second agent ticket that runs alongside), areas of work with recommended order, a filterable list, and a drawer per ticket with blockers, dependents and a copyable session prompt. Linear facts (status, assignee, blockers, estimates) are authoritative; the page adds humanized titles and short guidance for a person choosing their next session.

The shared server `~/.agents/skills/roadmap-page/scripts/roadmap.mjs` refreshes the page from Linear through the toolkit's `linear.py`, serves it on localhost, and runs self-heal passes with `claude -p` on Opus at medium effort. The page's data model and status rules are in `~/.agents/skills/roadmap-page/references/page-contract.md`; read it before writing the config or data blocks.

Requirements in the consumer project: a `.linear.json` with `teamId`, a `LINEAR_API_KEY` reachable through the project env files or the shell, `uv`, Node 22+, and `claude` (Claude Code) on PATH for self-heal.

## Creating a page

Ask these three things in one round, recommending answers from what you can see in Linear (`uv run ~/.agents/skills/linear/scripts/linear.py projects`, `states`, `labels`):

1. Which Linear projects to include, and which one is the current focus. Each project becomes a phase; order them by delivery.
2. The goal the focus phase works towards. The countdown follows the projects' dated Linear milestones; ask for a fallback target date and label only when the focus projects have none.
3. Which label marks work the person must do themselves (often "Owner Action"), or none. If the board has no such label, recommend creating one with the linear skill before the page is built: the server derives owner work from it, so without one every owner ticket has to be marked by hand.

Then build the page without further questions:

- Read every ticket in the chosen projects (`list --project NAME`, then `get ID -V -c` for each) and the team's workflow states. Note which state types the team starts work from; if work starts from Backlog, set `startableStateTypes` to include it.
- Give every ticket a `workflow` by the session workflow rules in the contract: `/scope` for bounded work the agent can decide on its own, `/prep` for anything substantial or anything the person will want to steer, and `owner` only for work with no code output, such as provider setup or business decisions. Lean to `prep` when unsure.
- Write the config: phases (each with `sources`, the issues its plan is written in, such as a Wayfinder map or a brief, so a rewrite of the plan or a milestone change flags the phase copy for a re-check), four to five lanes that group the focus phase by area of the system (lanes are groupings, not blockers), a `nextUp` order for the focus phase (the page ranks the cards by the work each ticket unblocks, so this order only settles ties; put the riskier ticket first), a short guide that explains the three kinds of session, and a `finalTicket` if the phase converges on one ticket such as a final acceptance check. Add a `roadmap` recipe to the project's justfile (create the justfile if there is none) that runs `node ~/.agents/skills/roadmap-page/scripts/roadmap.mjs <page> "$@"` with `*args` pass-through under `set positional-arguments`, so a quoted `--instruction` survives, and set `command` to `just roadmap`. Use a different entry point only when the person asks for one. Write skill commands in config text as `{skill:name}` (`{skill:wayfinder} HGN-1 {id}`); the page spells each for the harness its skill runs in (Wayfinder in Claude Code, `/scope`, `/prep` and `/cook-prd` in Pi), and a drawer can respell its prompt for another. Fill the template's `{{SNAPSHOT}}` with `<name>.snapshot.js` and add that path to the project's `.gitignore`.
- Write the guidance block from the Linear reads: one entry per ticket with its `id` and the curated fields in the contract, and `curated: true`. The `sourceHash` is computed by the server; leave `reviewedHash` null, run a refresh so the server writes the snapshot, copy each ticket's `sourceHash` from the snapshot into its `reviewedHash` and each phase's `sourceHash` (the snapshot's `phases[]`) into the phase's `reviewedHash`, then confirm no ticket shows "New: needs integration" or "Guidance needs review" and the hero shows no phase note.
- Run the copy pass. The guidance the creating session writes reads like notes; an isolated Claude run under the contract's Writing guidance, which rewrites each entry from the ticket's meaning, reads like a colleague explaining the work. Tell the person it runs on their Claude login, then run `node ~/.agents/skills/roadmap-page/scripts/roadmap.mjs <page> --heal custom --instruction "<text>"` once per batch of eight to ten tickets, with this instruction:

  > Rewrite the guidance of these tickets: <ids>. Treat the current title, summary, detail and input as a first draft written by the agent that created the page. Rewrite each from the ticket's meaning, reading the ticket with the Linear CLI, rather than trimming the draft, so every entry follows the Writing guidance section of the contract. Keep workflow, opener, gates, curated, reviewedHash and every id exactly as they are, and do not add aiGuidance. Keep every fact the draft carries from outside the ticket, such as milestone slices, delivery rules and prerequisites on the page, unless Linear contradicts it. In your final message list, per ticket, any fact you dropped or kept from outside the ticket.

  The last batch adds: "Then, under the same rules, rewrite the reader-facing prose in roadmap-config: each phase's description, intro, body and allWork, each lane's summary and detail, the guide items and guideFooter. Keep every {skill:...} token, every id list and every other config value unchanged." After the batches, diff the page against a copy taken before them: only the text fields and the config prose change, and `linearTitle` is untouched. Read each batch's final message and put back any dropped fact that still holds. In Pi, `humanize_text` is a lighter alternative for a single entry, not a replacement for the pass.
- Show the proposed lanes and next-up order to the person once, as a compact list, and apply their corrections before finishing.

Validate before handing over: run the server with `--check` (reads Linear, merges, writes nothing), then start it with `--no-open`, fetch `/api/status`, and open the page in a browser to confirm the in-progress strip, next-up cards and drawer render with the real data. Stop the server afterwards.

Hand over with: the command that opens the page, the number of tickets tracked, which tickets ended up in each next-up card, and anything you left uncurated with the reason.

## Updating an existing page

Prefer the page's own loop over editing by hand: run the server and use Refresh, then the Self-heal templates the page marks as pending (integrate new tickets, reconcile unexpected states, re-check changed guidance, move to the next phase). A change to the plan itself, such as milestones renamed or added or a source issue's delivery rules rewritten, surfaces as pending re-check work the same way a changed ticket does, so the person never has to know that the phase copy, lanes or guide went stale. A custom instruction is for a change the page cannot detect, such as a rendering request. Lanes and next-up cards exist only for the focus phase; when that phase is done, the "Move to the next phase" self-heal switches the focus and writes areas and an order for the phase that follows. Edit the file directly only when the person asks for a change in the rendering that self-heal should not be trusted with, and keep the two JSON blocks and the snapshot tag valid. Never edit the snapshot file; a refresh rewrites it.

## Boundaries

Reading Linear and editing the page are routine. Never write to Linear from this skill, never copy the API key into the page or any tracked file, and do not commit unless asked. Apart from the copy pass at creation, a self-heal run is started by the person from the page or the CLI, not on their behalf.
