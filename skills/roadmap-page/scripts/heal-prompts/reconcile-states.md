Reconcile this roadmap page with Linear data it does not recognise, so it renders every tracked ticket with a sensible status.

Findings from the last refresh:

```json
{{findings}}
```

Meaning of the findings:
- `unknownStates`: tickets whose Linear state type is not one the page's rules cover. Use `{{linearCli}} states` to see the workflow. Decide how each type should behave (closed, active, waiting, or ready to start) and extend the page's status rules so the type is handled explicitly; `startableStateTypes` in `roadmap-config` covers the common case of a team that starts work from Backlog as well as Todo.
- `missing`: tickets referenced by the page that Linear no longer returns. Check whether they were deleted, moved to another team, or renumbered; remove stale references from `roadmap-config` (lanes, nextUp, finalTicket) and from other tickets' `gates`, or point them at the replacement.
- `truncated`: tickets whose relation or comment lists were cut off by the CLI. Note it in the ticket's `detail` if a dependency might be hidden.
- `emptyProjects`: configured Linear projects that returned no tickets. Confirm the project name with `{{linearCli}} projects` and fix the spelling, or remove the project from its phase if it was retired.
- `danglingConfig`: identifiers in `roadmap-config` that match no ticket in `roadmap-data`.
- `stateTypes`: the full state name to type map Linear reported.

Success means a refresh would produce no unknown states, no dangling references and no empty projects, with Linear facts untouched. Keep rule changes minimal and consistent with the existing code; prefer config over code. Name anything you could not resolve, such as a ticket that genuinely disappeared, in your final message so the person can decide.
