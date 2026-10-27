Re-check the guidance of tickets whose Linear content changed since their guidance was written, and the copy of phases whose milestones or source tickets changed, and rewrite only what no longer matches.

Findings from the last refresh (`review` lists the tickets, each with its current guidance and its `description` and recent `comments` as Linear holds them now; `phases` lists the phases whose facts changed, with their current `milestones` and `sources`, each source with its `description`):

```json
{{findings}}
```

For each ticket in `review`, compare its description, comments, labels and blockers against the page's `title`, `summary`, `detail`, `input`, `workflow` and `opener`. When the guidance is still accurate, leave the prose alone. When it is stale, rewrite it as the contract's Writing guidance section describes. Do not change `workflow` between owner work and agent work unless the owner-action label changed. In every case set the entry's `reviewedHash` in `roadmap-guidance` to the ticket's current `sourceHash` from the findings so the review flag clears.

If a change in the ticket removes or adds a real decision the person has to make, say so in `input` rather than deciding it, and name the ticket in your final message.

Each phase in `phases` is there because the plan it describes moved: a milestone was renamed, added or removed, or a source ticket (the map or brief the phase follows) was rewritten; a `reviewedHash` of null means the copy was never checked against them. The person reading the page should not have to notice this themselves, so bring the phase's copy back in line with the current milestones and source: the phase's hero and later-phase text, its lanes' summaries, details and membership, the `nextUp` order, the guide, and the ticket guidance that places work in a slice or states a delivery rule. Milestone slices, delivery rules and sequencing stated in a source ticket are facts the page may carry. Leave what still reads true alone, and set the phase's `reviewedHash` in `roadmap-config` to its `sourceHash` from the findings.

Success means no ticket or phase in the findings is still flagged after a refresh, nothing on the page contradicts the current milestones or sources, and no Linear fact changed.
