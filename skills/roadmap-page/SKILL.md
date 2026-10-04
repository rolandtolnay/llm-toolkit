---
name: roadmap-page
description: Create or update a self-contained HTML roadmap page from a set of tickets (Linear today), with a local server that refreshes it and a self-heal button that runs headless pi. Use when asked for a roadmap, a plan view or a "what should I work on next" page built from ticket projects.
---

# Roadmap page

The output is one HTML file in the consumer project, usually `etc/roadmap/<name>.html`, built from `~/.agents/skills/roadmap-page/templates/roadmap.html`. The page shows a release-phase plan: an "In progress right now" strip, three next-up cards (an agent task, an owner task, something to plan together), areas of work with recommended order, a filterable list, and a drawer per ticket with blockers, dependents and a copyable session prompt. Linear facts (status, assignee, blockers, estimates) are authoritative; the page adds humanized titles and short guidance for a person choosing their next session.

The shared server `~/.agents/skills/roadmap-page/scripts/roadmap.mjs` refreshes the page from Linear through the toolkit's `linear.py`, serves it on localhost, and runs self-heal passes with `pi -p` on `openai-codex/gpt-6.1-sol` at medium effort. The page's data model and status rules are in `~/.agents/skills/roadmap-page/references/page-contract.md`; read it before writing the config or data blocks.

Requirements in the consumer project: a `.linear.json` with `teamId`, a `LINEAR_API_KEY` reachable through the project env files or the shell, `uv`, Node 22+, and `pi` on PATH for self-heal.

## Creating a page

Ask these four things in one round, recommending answers from what you can see in Linear (`uv run ~/.agents/skills/linear/scripts/linear.py projects`, `states`, `labels`):

1. Which Linear projects to include, and which one is the current focus. Each project becomes a phase; order them by delivery.
2. The goal the focus phase works towards, with an optional target date and a short label for the countdown.
3. Which label marks work the person must do themselves (often "Owner Action"), or none.
4. Which session-starter skills the project has for planning and scoping (for example `/prep`, `/scope`), so session prompts point at them. None is fine; the defaults are plain prompts.

Then build the page without further questions:

- Read every ticket in the chosen projects (`list --project NAME`, then `get ID -V -c` for each) and the team's workflow states. Note which state types the team starts work from; if work starts from Backlog, set `startableStateTypes` to include it.
- Write the config: phases, four to five lanes that group the focus phase by area of the system (lanes are groupings, not blockers), `nextUp` orderings that reflect dependency order and risk, openers, a short guide, and a `finalTicket` if the phase converges on one ticket such as a final acceptance check. Add a `roadmap` recipe to the project's justfile (create the justfile if there is none) that runs `node ~/.agents/skills/roadmap-page/scripts/roadmap.mjs <page> {{args}}` with `*args` pass-through, and set `command` to `just roadmap`. Use a different entry point only when the person asks for one.
- Write the data block from the Linear reads using the task shape in the contract, with `curated: true` and `reviewedHash: sourceHash` for every ticket you write guidance for. The `sourceHash` is computed by the server; leave it null and run a refresh immediately after writing so the server fills in facts and hashes, then confirm no ticket shows "New: needs integration" or "Guidance needs review".
- Humanize the reader-facing text (`title`, `summary`, `detail`, `input`, lane and phase copy, guide). In Pi, use the `humanize_text` tool; in Claude Code, load the `humanizer` skill; otherwise rewrite for a human reader yourself: short sentences, ordinary words, no marketing language, and keep every requirement, number and permission boundary from the ticket. Keep `linearTitle` untouched.
- Show the proposed lanes and next-up order to the person once, as a compact list, and apply their corrections before finishing.

Validate before handing over: run the server with `--check` (reads Linear, merges, writes nothing), then start it with `--no-open`, fetch `/api/status`, and open the page in a browser to confirm the in-progress strip, next-up cards and drawer render with the real data. Stop the server afterwards.

Hand over with: the command that opens the page, the number of tickets tracked, which tickets ended up in each next-up card, and anything you left uncurated with the reason.

## Updating an existing page

Prefer the page's own loop over editing by hand: run the server and use Refresh, then the Self-heal templates (integrate new tickets, reconcile unexpected states, re-check changed guidance, or a custom instruction). Edit the file directly only when the person asks for a change in the rendering that self-heal should not be trusted with, and keep the two JSON blocks valid.

## Boundaries

Reading Linear and editing the page are routine. Never write to Linear from this skill, never copy the API key into the page or any tracked file, and do not commit unless asked. The self-heal run can only be started by the person from the page or the CLI; do not start it on their behalf during page creation.
