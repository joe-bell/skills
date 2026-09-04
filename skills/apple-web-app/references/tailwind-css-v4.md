Optional. The skill itself is plain CSS; this is the Tailwind CSS v4 spelling of
the same rules for projects that use it. v4 only — `@utility`,
`@custom-variant`, `--value()` and the `(--var)` shorthand do not exist in v3.
Keep the `env(safe-area-inset-*)` mirrors in `@layer base :root`; `@theme` is
the wrong place for `env()`. Source: Joe Bell (a production Tailwind v4 app).

# Installed web app helpers (safe areas, standalone)

## §4 Viewport & safe areas

**Safe-area padding** — the `@utility pt-safe-area-*` family covers all four
sides using `--spacing(--value(integer))`; `pt-safe-area-0` and `pb-safe-area-2`
read like other padding classes:

```css
@utility pt-safe-area-* {
  padding-top: calc(env(safe-area-inset-top) + --spacing(--value(integer)));
}
/* repeat for pr-/pb-/pl- with the matching inset */
```

Use `h-(--header-height)` for `base + inset` bar heights (the `(--var)`
shorthand, not `[var(--x)]`).

## §6 Scroll container & bars

**Scroll root** — `isolate size-full min-h-screen overflow-x-hidden
overflow-y-scroll overscroll-y-contain
not-standalone:min-h-[-webkit-fill-available]`.
Use `min-h-screen`, not `min-h-dvh`, on a cold start.

**Bars** — use `sticky top-0 pt-safe-area-0 h-(--header-height)` for a sticky
header and `fixed inset-0 top-auto pb-safe-area-2 transform-gpu` for a bottom
bar. Make a standalone blur taller with
`standalone:[--layout-blur-h:calc(var(--header-height)*4)]`.

**Display-mode variants** — `standalone:` and `not-standalone:` follow
`display-mode`:

```css
@custom-variant standalone (@media (display-mode: standalone));
@custom-variant not-standalone (@media not all and (display-mode: standalone));
```

**Cold-launch reveal gate** — hide only in standalone until `data-ready` lands,
with no class juggling in JS:

```css
@custom-variant standalone-pending {
  @media (display-mode: standalone) {
    html:not([data-ready]) & {
      @slot;
    }
  }
}
```

Usage: `standalone-pending:invisible standalone-pending:opacity-0 transition-[visibility,opacity]`.

## §7 Overlays

Use `absolute inset-x-0 top-0 w-(--page-width) h-(--page-height) isolate` for
the backdrop and `sticky top-[calc(var(--visual-viewport-height)/2)]
-translate-y-1/2` for the dialog.

## §10 Touch & native-feel

Use `select-none touch-manipulation` on chrome,
`[-webkit-touch-callout:none]` on media, `[text-size-adjust:100%]` on `body`,
and `[content-visibility:auto]` on long grid items.
`scroll-pt-(--header-height)` and `motion-safe:scroll-smooth` cover anchors
and motion; `hover:` already compiles to `@media (hover: hover)`.
Keep `-webkit-tap-highlight-color: transparent` as a `:where(*)` rule in
`@layer base`, not a utility. Promote any repeated arbitrary property to an
`@utility`.

## §12 macOS

Every safe-area utility resolves to `0px` extra on macOS; the `standalone:`
variant still matches a Dock app.
