Re-check the guidance of tickets whose Linear content changed since their guidance was written, and rewrite only what no longer matches.

Findings from the last refresh (current guidance is included so you can compare):

```json
{{findings}}
```

For each ticket, read the live ticket with the Linear CLI (`get <ID> -V -c`) and compare the description, labels and blockers against the page's `title`, `summary`, `detail`, `input` and `workflow`. When the guidance is still accurate, leave the prose alone. When it is stale, rewrite the affected fields in the same plain style. Do not change `workflow` between owner work and agent work unless the owner-action label changed. In every case set `reviewedHash` to the ticket's current `sourceHash` so the review flag clears.

If a change in the ticket removes or adds a real decision the person has to make, say so in `input` rather than deciding it, and name the ticket in your final message. Success means no ticket in the findings still has `reviewRequired` true after a refresh, and no Linear fact changed.
