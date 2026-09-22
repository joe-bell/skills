# Maintaining anorak-css

## When to amend

- Tailwind adds or renames a variant family that does not fit the eight
  groups, or changes how combined variants are written.
- `prettier-plugin-tailwindcss` changes which helpers or attributes it sorts
  by default, or gains an option that affects grouping.
- Prettier changes the `printWidth` default or how it treats string literals.
- A rule here turns out to conflict with a formatter in practice.

## How to amend

1. Confirm the behaviour against the upstream source, not from memory. Add or
   update the entry in [sources.md](sources.md) and give the rule a `Source:`
   tail in the skill body.
2. Keep the skill body within 500 lines and 5,000 words.
3. Bump `metadata.version` and `metadata.reviewed`.
4. Run the repository's validation commands:

```sh
npx prettier@3 --check .
npx skill-check@1.2.0 check ./skills --no-security-scan --strict
```

5. Keep the change to one finding per pull request.

## What not to add

- Advice on which utilities or properties to use. This skill orders styling
  code; it does not design it.
- Rules that require a formatter override or an ignore comment to hold.
- Guidance that only makes sense in one repository. Keep it portable.

## Companion skill

[anorak-print-width](../../anorak-print-width/SKILL.md) covers where line
breaks come from. The two must stay consistent: Prettier reflows what it
parses, and this skill governs the class strings and `@apply` parameters that
it does not.
