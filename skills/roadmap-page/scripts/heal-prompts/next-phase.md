Move this roadmap page on to its next phase, so the person who opens it tomorrow sees that phase's work grouped into areas with a suggested order, the way the current focus phase is shown today.

Findings from the last refresh (`focus` is the current focus phase and `remaining` its open tickets; `next` is the first later phase with open work and `candidates` are those tickets; `milestones` are that phase's Linear milestones; `inProgress` shows what is being worked on now):

```json
{{findings}}
```

The page draws areas and next-up cards only for the phase named in `focus`, so the switch is a change to `roadmap-config`: set `focus` to `next`, replace `lanes` with four to five areas that group the candidates by area of the system in a sensible working order, rebuild the `nextUp` lists from dependency order and risk, and set or remove `finalTicket` depending on whether the phase converges on one ticket. Give each phase the copy its new position needs: the new focus phase carries `title`, `description` and `allWork` for the hero and the work list, the old one carries `intro` and `body` as a later phase, and the `short` captions still read correctly in the navigation. `targetDate` and `targetLabel` only matter when the phase's projects have no dated milestone, so update or remove them to keep the countdown honest.

Read each candidate ticket with the Linear CLI before grouping it; titles alone misplace work. Existing guidance may still describe a candidate as later work that waits for the old phase, so correct the `detail` and `input` sentences the switch makes wrong and leave guidance that still reads true alone.

Tickets still open in the old phase stay tracked and visible under it; a ticket changes phase only through its Linear project. Name each one in your final message with what it still gates, so the person can decide whether to finish it or let it trail.

If `next` is null there is no later phase with open work: change nothing and say so.

Success means the page opens on the new phase with every candidate in exactly one area, next-up cards that point at work that can start, phase copy that reads correctly for the new order, and no Linear fact changed. Your final message lists each area with its tickets on one line and the tickets left open in the old phase, so the person can correct the grouping with a custom self-heal.
