# Sources & credits

Format: **Author — Title (date) — URL** — what this skill took from it.

## Property order

- **Sky UK — Sky CSS Style Guide (2016–, BSD 3-Clause) —
  https://github.com/sky-uk/css** — the eight-group declaration order in
  section 3 (composed styles, structure, typography, cosmetic, native
  interaction, pseudo-elements, nested elements, pseudo-classes, media
  queries), and the reasoning that composed styles come first for ease of
  modification and media queries come last. The guide's property-order section
  was written by this skill's author, Joe Bell, who is its principal
  contributor; copyright in the guide remains Sky UK Ltd. Sky's guide in turn
  credits **Dropbox — CSS Style Guide —
  https://github.com/dropbox/css-style-guide** for a similar rule ordering.
  The groups are paraphrased here and extended with a Tailwind utility mapping
  and the variant-ordering rules, which are this skill's own. Sky's worked
  example ordering `padding` before `position` is the evidence for treating
  within-group sequence as a guide rather than a rule. Checked 2026-09-22.

## Tooling

- **Prettier — Options — https://prettier.io/docs/options** — `printWidth`
  defaults to `80` and is a target rather than an enforced maximum.
- **Tailwind Labs — prettier-plugin-tailwindcss —
  https://github.com/tailwindlabs/prettier-plugin-tailwindcss** — the plugin
  sorts classes within `class`/`className` attributes, within `@apply`
  directives, and within functions and template literals named in
  `tailwindFunctions`; extra attributes are opted in via `tailwindAttributes`.

## Production experience

- **Joe Bell — utility-heavy component libraries (2022–)** — everything not
  attributed above: when a list is long enough to split, keeping a cohesive
  cluster whole across a category boundary, the `text-*` ambiguity, combined
  variants sorting by their outermost group, keeping conditional and override
  segments last, and not introducing a class helper merely to enable grouping.
