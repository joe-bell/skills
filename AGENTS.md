# AGENTS.md

Conventions for agents editing this skills repository.

## Layout

- Put one skill in each `skills/<name>/` directory, with a `SKILL.md` and
  optional `references/` directory.
- Skills follow the [Agent Skills specification](https://agentskills.io/specification.md).
- Frontmatter begins with `name`, then `description`, whose text must include
  "Use when". `metadata` values must be strings only.

## Validation

Before every commit, run:

```sh
npx prettier@3 --check .
npx skill-check@1.2.0 check ./skills --no-security-scan --strict
```

Fix formatting with `npx prettier@3 --write .`. Code fences are left as
written (`embeddedLanguageFormatting: off` in `.prettierrc`).

- A skill body must stay within 500 lines and 5,000 words.
- Every local reference link must resolve. Do not use `#anchor` targets.

## Style

- Wrap prose at roughly 80 columns; Prettier normalises the rest.
- Keep skill bodies to plain HTML, CSS and DOM unless a skill explicitly
  concerns a particular tool.
- Give every external rule a `Source:` tail and an entry in
  `references/sources.md`.
- Record an OS build and date with device-verified findings.

## Keeping skills current

- When present, a skill's `references/maintenance.md` is its procedure for
  amending the skill.
- Bump `metadata.version` for every content change.
- Pull requests from copies in other repositories are welcome. Keep each PR
  to one finding.

## Adding a skill

1. Copy its complete folder into `skills/`.
2. Add a Reference bullet to the README: `[**name**](./skills/name/SKILL.md) — <Gerund> …`,
   one clause, no full stop.
3. Run the validation commands above and commit the change.

`CLAUDE.md` contains `@AGENTS.md`; keep this file as the one source of truth.
