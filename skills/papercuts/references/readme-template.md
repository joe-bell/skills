# Papercuts

This directory collects small frictions that agents (and people) hit while
working on this repository: docs that point somewhere stale, setup steps that
are missing, commands that need a flag nobody wrote down.

To add one, use the `papercuts` agent skill, or run its script:

```sh
python3 path/to/papercuts/scripts/papercut.py "what got in the way, and where"
```

## Format

Each branch writes to its own file, `.papercuts/<branch>.jsonl`, with one JSON
object per line:

| field      | required | meaning                                          |
| ---------- | -------- | ------------------------------------------------ |
| `ts`       | yes      | when it was logged, ISO 8601 in UTC              |
| `note`     | yes      | what got in the way                              |
| `category` | no       | a loose label such as `docs`, `tooling`, `tests` |
| `file`     | no       | the repository path it concerns                  |
| `agent`    | no       | the agent that logged it                         |

## Lifecycle

Logs are committed with the branch, so they reach the default branch through
its pull request. A periodic review checks each entry against the current
code, groups entries with the same cause, fixes them, and deletes the log
files it processed in the same change.

If two branches touch the same log file, keep every line from both. Leave
entries alone outside a review, or they never get fixed.
