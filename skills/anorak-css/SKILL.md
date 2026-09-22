---
name: anorak-css
description: Order and group styling code so it reads in a predictable sequence — CSS and Sass declarations, Tailwind utility lists in class/className attributes and in cva, cx, clsx or cn helpers, and the classes inside an @apply rule. Use when writing or editing any of those, when a utility list has grown long enough to be hard to scan, or when deciding where a newly added class or declaration belongs. Works with Prettier and prettier-plugin-tailwindcss rather than around them. Not for redesigning styles, choosing utilities over CSS, or migrating Tailwind versions.
metadata:
  source: hand-maintained by Joe Bell; property order adapted from Sky's CSS Style Guide
  reviewed: "2026-09-22"
  upstream: "https://github.com/joe-bell/skills/tree/main/skills/anorak-css"
  version: "2026-09-22.1"
  category: "anorak"
---

# Ordering and grouping styling code

## 1. Scope

One ordering convention, applied to the three places styling is written:

- **CSS and Sass declarations** inside a rule.
- **Tailwind utility lists** in `class`/`className` attributes and in class
  helpers such as `cva`, `cx`, `clsx` and `cn`.
- **The classes inside an `@apply` rule.**

This is a source-formatting skill. It changes the order and the line and string
layout of styling code. It never changes which styles apply.

**Non-goals:** redesigning styles, choosing between utilities and hand-written
CSS, introducing or removing `@apply`, introducing or removing a class helper,
and Tailwind version migration. Organise the form the project already uses.

References:

- [tooling.md](references/tooling.md)
- [sources.md](references/sources.md)
- [maintenance.md](references/maintenance.md)

## 2. When to apply it

Apply this to styling code being written or substantively edited. Do not
reformat surrounding declarations or class lists that the task did not
otherwise touch — an ordering change in an untouched line is noise in the
diff and buries the real change.

Two exceptions, both requested explicitly:

- A tidying pass, where reordering untouched code is the whole point.
- A file already being rewritten for another reason.

## 3. The order

Adapted from Sky's CSS Style Guide, whose property-order section this skill's
author wrote. Source: Sky UK — Sky CSS Style Guide — see
[sources.md](references/sources.md).

Declarations and utilities run in this sequence:

0. **Composed styles** — `@include` and `@extend` in Sass; in a utility list,
   a shared base or imported class constant.
1. **Structure** — `display`, `position`, `margin`, `padding`, `width`,
   `height`, `box-sizing`, `overflow`, `gap`.
2. **Typography** — `font-*`, `line-height`, `text-align`, `text-transform`,
   `letter-spacing`.
3. **Cosmetic** — `color`, `background-*`, `border-*`, `border-radius`,
   `box-shadow`, `animation`, `transition`.
4. **Native interaction** — `appearance`, `cursor`, `user-select`,
   `pointer-events`.
5. **Pseudo-elements** — `::before`, `::after`.
6. **Nested elements** — child and descendant selectors.
7. **Pseudo-classes and states** — `:hover`, `:focus-visible`, `:active`,
   `:disabled`, `[aria-*]`, `[data-*]`.
8. **Media and container queries** — last.

In a utility list the same eight groups apply, with variants standing in for
selectors:

| Group                     | Utilities                                                                                                |
| ------------------------- | -------------------------------------------------------------------------------------------------------- |
| 0 Composed                | a shared base string, an imported class constant                                                         |
| 1 Structure               | `flex`, `grid`, `absolute`, `inset-0`, `p-4`, `w-full`, `gap-2`, `overflow-hidden`                       |
| 2 Typography              | `font-medium`, `text-sm`, `leading-tight`, `tracking-wide`, `text-center`                                |
| 3 Cosmetic                | `text-zinc-900`, `bg-white`, `border`, `border-zinc-200`, `rounded-md`, `shadow-sm`, `transition-colors` |
| 4 Native interaction      | `appearance-none`, `cursor-pointer`, `select-none`, `pointer-events-none`                                |
| 5 Pseudo-element variants | `before:*`, `after:*`                                                                                    |
| 6 Child variants          | `*:*`, `[&>svg]:*`                                                                                       |
| 7 State variants          | `hover:*`, `focus-visible:*`, `disabled:*`, `data-[state=open]:*`                                        |
| 8 Breakpoint variants     | `sm:*`, `md:*`, `lg:*`                                                                                   |

### Two wrinkles worth naming

**`text-*` spans two groups.** `text-sm`, `text-center` and `text-balance` are
typography (group 2). `text-zinc-900` is a colour, so it is cosmetic (group 3).
Sort by what the utility does, not by its prefix.

**Combined variants sort by their outermost group.** `md:hover:bg-zinc-50`
carries both a state and a breakpoint. Media queries come last in the order, so
it belongs with the other `md:` utilities, prefix intact. The same rule sends
`dark:hover:*` to wherever the list keeps `dark:`.

**The group boundary is the rule; the sequence inside a group is a guide.**
Whether `color` precedes `background`, or `flex` precedes `p-4`, matters far
less than keeping the cosmetic utilities together and after the structural
ones. Sky's own worked example puts `padding` before `position` while its list
has them the other way round. Do not reshuffle within a group to match the
list, and expect a formatter to make that call for you anyway.

Group by purpose first. Use this sequence when a file has no established
convention of its own; where one exists, follow it and stay consistent within
the file.

## 4. Keeping a cohesive group together

The sequence serves readability, so it yields to it. A small cluster with one
clear job stays together even when it straddles two groups:

```jsx
// `overflow-hidden text-ellipsis whitespace-nowrap` straddles structure and
// typography, but the three do one job — truncation — and mean nothing apart.
<span className="block max-w-48 overflow-hidden text-ellipsis whitespace-nowrap" />
```

`transition-colors hover:bg-zinc-700` is the same case across cosmetic and
state: the transition exists for the hover. Splitting a cluster like that to
satisfy a category boundary makes the list harder to read, which defeats the
point.

## 5. Strings and lines

Short lists stay in one string. Splitting a four-class list across three
strings is worse than leaving it alone.

Once a list is long enough to be hard to scan, break it at a **group**
boundary. In a class helper that means another string; in `@apply` it means
another line. Never split an individual class token, and never let a break
change which classes apply.

Examples below are written in section 3's order. With
`prettier-plugin-tailwindcss` installed, expect it to reorder the classes
within each string — that is fine, and section 6 explains why.

```jsx
const button = cva(
  [
    "inline-flex items-center justify-center gap-2 px-4 py-2",
    "text-sm font-medium",
    "bg-zinc-900 text-white rounded-md transition-colors",
    "hover:bg-zinc-700 focus-visible:outline-2 focus-visible:outline-offset-2",
  ],
  {
    variants: {
      size: {
        sm: "px-2 py-1 text-xs",
        lg: "px-6 py-3 text-base",
      },
    },
  },
);
```

Variants stay compact. `"px-2 py-1 text-xs"` is already legible; giving it one
string per group would be ceremony.

```css
.card {
  @apply relative flex flex-col gap-3 p-6;
  @apply text-sm leading-relaxed;
  @apply bg-white text-zinc-900 rounded-lg border border-zinc-200;
}
```

**A group may span several lines.** A long structure group splits again at a
sensible seam rather than running past the edge of the screen. Grouping sets
where breaks _can_ go; length decides how many are needed.

### Where the width comes from

Prettier cannot reflow the inside of a string literal or the parameters of an
`@apply` rule — those are opaque to it. Nothing will wrap them for you, so
`printWidth` is the target to aim at by hand when choosing break points.

Read it from the project's Prettier config, and fall back to Prettier's
default of `80` when none is set. Source: Prettier — Options — see
[sources.md](references/sources.md).

This is the one case where hand-wrapping is correct, and it does not conflict
with [anorak-print-width](../anorak-print-width/SKILL.md): that skill forbids
hand-wrapping what Prettier would reflow itself. Class strings and `@apply`
parameters are exactly what it will not.

## 6. Working with the formatter

**The project's formatter wins.** Run it after editing and keep its output.
Never add an ignore comment, a formatter override or a config change to force
this skill's preferred order.

**If `prettier-plugin-tailwindcss` is installed, it decides the order within
each string** and within each `@apply` rule, and this skill decides which
classes share a string or a line. The plugin sorts each literal in place; it
does not move classes between them, so grouping survives sorting. Source:
Tailwind Labs — prettier-plugin-tailwindcss — see
[sources.md](references/sources.md).

Where the plugin's order and the sequence in section 3 disagree inside a
single string, the plugin wins. Do not fight it.

**Read the plugin's config; do not write it.** The plugin only sorts class
helpers listed in `tailwindFunctions`, and only sorts extra attributes listed
in `tailwindAttributes`. If a project's `cn` is unsorted, that is a project
decision. Adding it to the config is a change to the project's formatting
setup, not part of tidying a class list — raise it, don't do it.

See [tooling.md](references/tooling.md) for how to detect the setup.

## 7. Preserving behaviour

Ordering is not licence to change what renders.

- **In CSS, order can be meaningful.** Two declarations setting the same
  property, or shorthand followed by longhand (`background` then
  `background-size`), resolve by source order. Never reorder those past each
  other.
- **The same holds in a utility list** wherever two classes set the same
  property and the project relies on the later one winning.
- **Keep conditional and override positions.** A conditional class, a spread
  value, and a consumer's incoming `className` sit at the end so they still
  override. Grouping never moves them earlier.
- **Never introduce a helper to enable grouping.** If a list is a plain
  string, it stays a plain string; break it with the language's own
  concatenation or leave it long.

```jsx
// The trailing `className` still wins. It is not part of the grouping.
<div className={cn("flex items-center gap-2 p-4", isActive && "bg-zinc-100", className)} />
```

## 8. Verifying

Use the smallest check that proves nothing broke:

1. Run the project's formatter and keep its output.
2. Read the diff. Every line should be a move, a re-split or a re-wrap —
   never an added, removed or renamed class or declaration.

Run the project's own required checks as well. Go further than that only when
a class helper's behaviour is genuinely in doubt, such as a list with
conditional segments or duplicate properties.
