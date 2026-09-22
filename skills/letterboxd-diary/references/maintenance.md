# Maintaining this skill

## 0. Porting

- Copy the whole directory, including `references/`, and keep its relative
  links.
- Recreate the host tool's discovery link (for example Claude Code reads
  `.claude/skills/<name>`; a relative symlink to the copied folder works)
  rather than copying any symlink.
- `metadata.upstream` is the public copy, published manually.
- **Never commit a username into this skill.** It is per-install state, not
  skill content — section 1 of [SKILL.md](../SKILL.md) says where it goes
  instead. A copy of this skill carrying someone's username is a bug.

## 1. Conventions

- A durable finding is an observed change in the feed, a field this skill has
  wrong, or a host whose fetch tool mangles the namespaced XML. Exclude
  one-off account quirks and unverified forum claims.
- Letterboxd publishes no schema for this feed, so every parsing rule is
  observed. Give each one a `Source:` tail naming the feed and the date it was
  seen, and record it in [sources.md](sources.md).
- If the documented curl flags change, change the `allowed-tools` entry in the
  frontmatter to match — it is a literal command prefix, not a pattern.
- A host that blocks one retrieval route is a durable finding: record which
  rung of the ladder failed, how it failed, and what reached the feed instead.
  Attribute it to the session that saw it rather than to the host's
  documentation. Add rungs only when an existing one is genuinely unavailable —
  the ladder is a fail-fast sequence, and every extra rung costs a round trip
  on hosts that need it.
- **Never rely on whitespace inside inline code.** Prettier strips leading and
  trailing spaces inside backticks, so a rule written as "split on ` - `"
  silently becomes "split on `-`" on the next format pass — which breaks on
  hyphenated titles. Spell such separators out in words.
- Keep `SKILL.md` at ≤ 500 lines / 5,000 words, wrapped around 80 columns; the
  upstream repo runs Prettier (code fences excluded).
- Bump `metadata.version` for every content change, and `metadata.reviewed`
  whenever the feed is re-checked.

## 2. Re-checking the feed

Against any public profile:

```sh
curl -sSf https://letterboxd.com/<username>/rss/ | head -20
curl -sSf https://letterboxd.com/<username>/rss/ | grep -c '<item>'
```

Confirm each field in section 3 of [SKILL.md](../SKILL.md) still appears, that
the diary-entry count is still capped at 50, and that a reviewed entry still
carries a `letterboxd-review-` guid. Note anything that moved, with the date.

Check against more than one account. Several rules only show up by comparison:
the unrated case needs a member who leaves films unrated, the list-vs-diary
split needs a member with lists, and the publish-date coverage boundary needs a
member who backdates. A single feed will happily agree with a wrong rule.

## 3. Validation

From the repository root:

```sh
npx prettier@3 --check .
npx skill-check@1.2.0 check ./skills --no-security-scan --strict
```
