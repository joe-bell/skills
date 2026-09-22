# Maintaining anorak-print-width

## When to amend

- Prettier changes a default this skill quotes: `printWidth`, `proseWrap` or
  `embeddedLanguageFormatting`.
- Prettier adds or removes a recognised config filename or resolution rule.
- Prettier gains the ability to reflow something listed in section 5 as
  opaque, such as string literals or `@apply` parameters.

## How to amend

1. Confirm the behaviour against Prettier's own documentation and note the
   version it was checked against. Update [sources.md](sources.md).
2. Bump `metadata.version` and `metadata.reviewed`.
3. Run the repository's validation commands:

```sh
npx prettier@3 --check .
npx skill-check@1.2.0 check ./skills --no-security-scan --strict
```

4. Keep the change to one finding per pull request.

## What not to add

- A recommended `printWidth`. This skill decides who wraps, not how wide.
- Guidance for formatters other than Prettier. The principle transfers; the
  specifics do not, and stating them unchecked would be wrong.

## Companion skill

[anorak-css](../../anorak-css/SKILL.md) covers the case this skill carves
out: breaking class strings and `@apply` rules by hand, because Prettier
cannot reflow them.
