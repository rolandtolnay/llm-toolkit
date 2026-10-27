Integrate the tickets that are new to this roadmap page so each one has reader-facing guidance and a place in the plan.

Findings from the last refresh (`uncurated` are tickets with only Linear facts, each with its `description` and recent `comments` as Linear holds them now; `unplaced` are curated focus-phase tickets missing from every lane; `inProgress` shows what is currently being worked on):

```json
{{findings}}
```

For each uncurated ticket, add an entry with its `id` to `roadmap-guidance`:
- write `title`, `summary`, `detail` and `input` as the contract's Writing guidance section describes;
- set `workflow` by the contract's session workflow rules: `scope` for bounded work the agent can decide on its own, `prep` for anything substantial or anything the person will want to steer (the default when unsure), `owner` only for work with no code output, such as provider setup or business decisions;
- set `curated` to true and copy the ticket's `sourceHash` from the findings into `reviewedHash`;
- keep `gates` empty unless the ticket text clearly depends on a tracked prerequisite that is not a native blocker.

Then update `roadmap-config`: add each focus-phase ticket to the lane that fits its area (create a lane only when no existing lane fits and at least two tickets would share it, keeping four to five lanes in total), and insert it into the `nextUp` order where it belongs relative to its neighbours. Tickets in later phases need no lane.

Success means every ticket in `uncurated` and `unplaced` is curated and placed with a session prompt that fits it, no Linear fact changed, and the two JSON blocks still parse. If a ticket's description is too thin to write honest guidance, write a cautious summary that says what is known, set `workflow` to `prep` so the interview fills the gaps, and name it in your final message.
