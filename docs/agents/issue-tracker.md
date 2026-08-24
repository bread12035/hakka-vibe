# Issue tracker: Local Markdown

Issues and specs for this repo live as markdown files under `docs/issues/`, committed to version control.

## Conventions

- One feature per directory: `docs/issues/<feature-slug>/`
- The spec is `docs/issues/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `docs/issues/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`, never a single combined tickets file
- Triage state is recorded as a `Status:` line near the top of each file (see the label vocabulary below)
- Blocking edges are recorded as a `Blocked by: NN, NN` line near the top of a ticket. A ticket is unblocked when every file it lists has `Status: done`
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new file under `docs/issues/<feature-slug>/` (creating the directory if needed), then commit it.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the ticket number directly. A bare `01` means the lowest-numbered match under the feature directory currently in play.

## Label vocabulary

The skills speak in terms of five canonical triage roles. Since there is no label system in a markdown tracker, write the role as the `Status:` line value:

| Role              | Meaning                                  |
| ----------------- | ---------------------------------------- |
| `needs-triage`    | Needs to be evaluated                    |
| `needs-info`      | Waiting on more information              |
| `ready-for-agent` | Fully specified, ready for an AFK agent  |
| `ready-for-human` | Requires human implementation            |
| `wontfix`         | Will not be actioned                     |

Add `in-progress` and `done` for the states a ticket passes through once work starts.

`to-spec` publishes a spec with `Status: ready-for-agent`.
