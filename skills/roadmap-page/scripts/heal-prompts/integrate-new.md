Integrate the tickets that are new to this roadmap page so each one has reader-facing guidance and a place in the plan.

Findings from the last refresh (`uncurated` are tickets with only Linear facts; `unplaced` are curated focus-phase tickets missing from every lane; `inProgress` shows what is currently being worked on):

```json
{{findings}}
```

For each uncurated ticket, read it with the Linear CLI (`get <ID> -V -c`) and then, in `roadmap-data`:
- write `title` (a short human name, at most 100 characters), `summary` (one sentence), `detail` (what the work changes and how it connects to the rest of the plan) and `input` (where the person helps and why the chosen workflow fits);
- set `workflow`: `go` for settled requirements an agent can implement, `scope` when the intent is clear but a first slice needs agreeing, `prep` when product or lifecycle choices need discussing before a plan, `owner` only when the ticket carries the owner-action label or is explicitly the person's own task;
- set `curated` to true and copy `sourceHash` into `reviewedHash`;
- keep `gates` empty unless the ticket text clearly depends on a tracked prerequisite that is not a native blocker.

Then update `roadmap-config`: add each focus-phase ticket to the lane that fits its area (create a lane only when no existing lane fits and at least two tickets would share it, keeping four to five lanes in total), and insert it into the `nextUp` ordering lists where it belongs relative to its neighbours. Tickets in later phases need no lane.

Success means every ticket in `uncurated` and `unplaced` is curated and placed, no Linear fact changed, and the two JSON blocks still parse. If a ticket's description is too thin to write honest guidance, write a cautious summary that says what is known, set `workflow` to `review`, and name it in your final message.
