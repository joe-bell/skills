---
name: anorak-print-width
description: Leave line wrapping to Prettier when a project configures it, instead of hand-wrapping code or Markdown at a fixed character count. Use when writing or editing any file in a project with a Prettier config, when tempted to break a long line to hit 80 columns, when deciding how to wrap Markdown prose, and when choosing whether to hand-wrap something Prettier cannot reflow itself. Covers printWidth, proseWrap and where manual wrapping is still correct.
metadata:
  source: hand-maintained by Joe Bell; Prettier behaviour from Prettier's own documentation
  reviewed: "2026-09-22"
  upstream: "https://github.com/joe-bell/skills/tree/main/skills/anorak-print-width"
  version: "2026-09-22.1"
  category: "anorak"
---

# Let Prettier do the wrapping

## 1. Scope

Where line breaks come from in a project that runs Prettier. This is about who
decides the wrapping, not about what the width should be.

**Non-goals:** choosing a `printWidth`, adding Prettier to a project that does
not use it, and formatting for tools other than Prettier. If a project uses a
different formatter, defer to that one on the same principle.

References:

- [sources.md](references/sources.md)
- [maintenance.md](references/maintenance.md)

## 2. The rule

**If the project configures Prettier, Prettier owns the wrapping.** Write the
code, run the formatter, keep the result.

Do not hand-wrap a long line to reach some character count. Do not reflow a
line Prettier has already laid out. Do not add `// prettier-ignore` to protect
a manual wrap. Hand-wrapping code that Prettier then reflows produces a diff
full of churn, and the next person's editor undoes it on save.

`printWidth` is Prettier's target, not a ceiling it enforces — it aims for the
width and will still emit shorter and longer lines. Source: Prettier —
Options — see [sources.md](references/sources.md). So a line slightly over the
configured width, produced by Prettier, is correct output and should be left
alone.

## 3. Detecting the config

Prettier is configured if any of these is present:

- `.prettierrc`
- `.prettierrc.json`, `.prettierrc.json5`, `.prettierrc.yaml`,
  `.prettierrc.yml`, `.prettierrc.toml`
- `.prettierrc.js`, `.prettierrc.mjs`, `.prettierrc.cjs`, `.prettierrc.ts`,
  `.prettierrc.mts`, `.prettierrc.cts`
- `prettier.config.js`, `prettier.config.mjs`, `prettier.config.cjs`,
  `prettier.config.ts`, `prettier.config.mts`, `prettier.config.cts`
- a `prettier` key in `package.json` or `package.yaml`

Source: Prettier — Configuration File — see [sources.md](references/sources.md).

A config file that sets no options still counts — it opts the project into
Prettier's defaults, which include `printWidth: 80`.

Check for a nearer config before assuming the root one applies. Prettier
resolves config from the location of the file being formatted, searching up
the file tree until it finds one, so a monorepo package may set its own width.
Source: Prettier — Configuration File — see [sources.md](references/sources.md).

**If there is no Prettier config, this skill does not apply.** Follow whatever
the file and its neighbours already do.

## 4. Markdown is the exception worth knowing

Prettier does not rewrap Markdown prose by default. `proseWrap` defaults to
`"preserve"`, which keeps the existing line breaks exactly as written. Source:
Prettier — Options — see [sources.md](references/sources.md).

So for Markdown, read `proseWrap` before deciding:

| `proseWrap`            | What Prettier does          | What to do                               |
| ---------------------- | --------------------------- | ---------------------------------------- |
| `"preserve"` (default) | Keeps your line breaks      | Match the wrapping the file already uses |
| `"always"`             | Wraps prose to `printWidth` | Write freely and let it wrap             |
| `"never"`              | Puts each block on one line | Do not insert breaks                     |

Under `"preserve"` a hand-wrapped Markdown file stays hand-wrapped, and a
one-line-per-paragraph file stays that way. Matching the file keeps the diff
to the sentences that actually changed. Do not convert a file from one style
to the other as a side effect of an unrelated edit.

## 5. Where hand-wrapping is still correct

Prettier reflows the code it parses. It does not reach inside opaque content,
and there nothing will wrap for you:

- **String literals**, including Tailwind class strings in `class`/`className`
  and in helpers such as `cva`, `cx`, `clsx` and `cn`.
- **The parameters of a CSS `@apply` rule.**
- **Template literal contents**, unless embedded formatting applies.
- **Comments.**

In those, break by hand, at a boundary that means something — a group of
related classes, a clause — using the project's `printWidth` as the target and
`80` when none is set. That is not a violation of this skill; it is the case
it carves out.

For class strings and `@apply` specifically, the grouping convention is
[anorak-css](../anorak-css/SKILL.md). The two agree: Prettier reflows what it
can parse, and you break what it cannot.

## 6. Embedded code

`embeddedLanguageFormatting` defaults to `"auto"`, so Prettier formats code it
recognises inside template literals and Markdown code fences. Source: Prettier
— Options — see [sources.md](references/sources.md).

Where a project sets it to `"off"`, those fences and literals are left exactly
as written — so match the surrounding style rather than expecting the
formatter to tidy up afterwards.

## 7. Verifying

Run the project's formatter and confirm it reports no changes. If it rewrites
a line you wrote by hand, the hand-wrap was wrong: take Prettier's version.
