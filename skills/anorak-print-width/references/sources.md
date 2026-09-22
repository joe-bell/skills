# Sources & credits

Format: **Author — Title (date) — URL** — what this skill took from it.

## Prettier behaviour

- **Prettier — Options — https://prettier.io/docs/options** — `printWidth`
  defaults to `80` and is "roughly how long you'd like lines to be" rather
  than a hard maximum, so Prettier emits both shorter and longer lines;
  `proseWrap` defaults to `"preserve"`, with `"always"` wrapping prose to
  `printWidth` and `"never"` putting each prose block on a single line;
  `embeddedLanguageFormatting` defaults to `"auto"`, formatting recognised
  code inside template literals and Markdown code fences.
- **Prettier — Configuration File —
  https://prettier.io/docs/configuration** — the recognised config filenames
  (`.prettierrc` plus its `.json`, `.json5`, `.yaml`, `.yml`, `.toml`, `.js`,
  `.mjs`, `.cjs`, `.ts`, `.mts` and `.cts` variants, `prettier.config.*`, and
  a `prettier` key in `package.json` or `package.yaml`), and that the config
  is resolved from the location of the file being formatted, searching up the
  file tree until one is found. Checked 2026-09-22.

## Production experience

- **Joe Bell — Prettier-formatted repositories (2019–)** — the rule itself:
  hand-wrapping code a formatter will reflow produces churn that the next
  save undoes, the list of content Prettier treats as opaque, and the
  instruction to take Prettier's version whenever it rewrites a hand-wrapped
  line.
