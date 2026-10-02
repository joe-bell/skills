# `.github/rulesets/` — branch protection as code

GitHub **rulesets** guard the default branch server-side. **GitHub does not
read this directory**: `main.json` is the source of truth, applied with one API
call by a repository admin. Edit the JSON, re-apply, commit.

## `main.json`

- **`non_fast_forward`** blocks force-pushes (history rewrites).
- **`deletion`** blocks deleting the branch.
- **`update`** restricts updates to the bypass actor, so only the maintainer
  can merge a pull request or otherwise move `main`. Contributors and bots can
  still open pull requests and run checks.
- **`pull_request`** makes every change land through a pull request, merged
  by squash only. It asks for no approving review, so a PR merges once its
  checks pass.
- **`required_status_checks`** requires `check` (the CI job, from GitHub
  Actions, app `15368`). `strict_required_status_checks_policy` is `false`: a
  branch need not be up to date with `main`, but a merge conflict still blocks
  the merge.
- **`bypass_actors`** names one person: the maintainer, Joe (`7349341`), in
  `always` mode. The maintainer is the only one who can merge, and can also
  force-push, push directly, or merge past a failing check when needed.

This replaces a classic branch protection rule that asked for one approving
review (always bypassed by the sole maintainer) and allowed force-pushes.

## Applying it

Apply it only after the `check` job exists on `main`, or no pull request can
satisfy the required check. First time, when no ruleset exists yet:

```sh
gh api --method POST /repos/joe-bell/skills/rulesets --input .github/rulesets/main.json
gh api --method DELETE /repos/joe-bell/skills/branches/main/protection
```

Delete the classic rule only after the ruleset exists. After that:

```sh
id=$(gh api /repos/joe-bell/skills/rulesets --jq '.[] | select(.name=="main protection") | .id')
gh api --method PUT "/repos/joe-bell/skills/rulesets/$id" --input .github/rulesets/main.json
```
