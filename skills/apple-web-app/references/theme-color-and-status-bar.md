# Status bar & theme colour

## `apple-mobile-web-app-status-bar-style`

Only applies in standalone (home-screen) mode, and only when
`apple-mobile-web-app-capable` is `yes`.

| Value                 | Bar appearance                    | Page draws under it | `env(safe-area-inset-top)` |
| :-------------------- | :-------------------------------- | :------------------ | :------------------------- |
| `default` (or absent) | Opaque, system/white              | No                  | `0px`                      |
| `black`               | Opaque black                      | No                  | `0px`                      |
| `black-translucent`   | Transparent; clock over your page | **Yes**             | Real inset                 |

`black-translucent` is the only "fullscreen" option — and the name is
misleading: it does not make the bar black, it removes it and hands you the
pixels. Choosing it means every top-anchored element needs
`padding-top: env(safe-area-inset-top)`.

## Safari 26 colour sampling

Safari 26 does not honour `<meta name="theme-color">` for the status bar above
the page or the address bar below it (Safari's default bottom tab layout). It
colours each bar from the page, and WebKit's source states the rule. For the top
and bottom edges separately:

1. Hit-test one point: the horizontal centre of the edge, 4px inside it. Only
   `position: fixed` and `position: sticky` elements and their contents are
   hit; other page content, including `absolute` elements outside them, never
   is. CSS `pointer-events` is ignored, except in the retry in item 9.
2. Walk up from the hit element to the first fixed or sticky ancestor (or the
   element itself) that qualifies. Nothing beneath the hit element is
   considered, so a narrow fixed element at the centre point hides a
   qualifying one below it. `opacity` below 0.1, `visibility: hidden`, and
   elements with no background, no `backdrop-filter` and no children are
   skipped; empty images, video, canvas and iframes are not.
3. A qualifying element spans at least 90% of the viewport width, measured
   after 4px is trimmed from each side (about 347px of a 393px viewport).
4. Its `background-color` is used when its border box is more than 10px in
   both dimensions. A smaller one is sampled from a 2px strip 4–6px inside the
   edge, so an edge bar needs to be about 6px deep to count. The element's own
   `opacity` is not applied to the colour; below 0.1 it is skipped instead.
5. A colour with alpha below 0.75 is blended over the page background colour —
   not over the pixels actually beneath it. So is a dimming layer: a fixed
   element covering at least 90% of the viewport both ways, with a translucent
   background and no children.
6. With nothing qualifying, the bar is the page background: `<body>`'s
   `background-color` (it won over `<html>`'s with both set); `<html>`'s, then
   white or black, when `<body>` is transparent.
7. A full-viewport overlay keeps the edge's existing colour when one is already
   set. A dialog opened over a page whose sticky header tints the top leaves
   the status bar at the header's colour above the dimmed page.
8. A `::backdrop` (native `<dialog>`, popover) counts as a dimming layer.
9. If the walk found only skipped `pointer-events: none` layers, Safari retries
   honouring `pointer-events`, which also skips a `pointer-events: none` dim.
10. The address bar only takes a tint when the page uses `viewport-fit=cover`.

Source: WebKit `LocalFrameView::fixedContainerEdges`; Joe Bell (iOS Simulator
26.5 23F77 and 27.0 24A434, 2026-09-22; verified iPhone 17 Pro, iOS 27.0,
2026-09-23); Larionov for item 10; the
`<html>` fallback chain from Fiquitiva and Nasedkin, in
[sources.md](sources.md). Earlier community measurements (Frain; Fiquitiva)
found the same shape; their ~80% width, ~3px height and "`opacity: 0` is still
sampled" figures do not match the source or these runs. On an iPhone 17 Pro
with iOS 27.0 these matched the Simulator: the fixed/absolute split, width
(92% used, 80% not), depth (6px used, 4px ignored), the centred pill, a fixed
dim over a sticky header (item 7), a native `<dialog>` on a plain page, and
the opacity and `pointer-events` cases. A native `<dialog>` over a sticky
header kept the header's colour in the Simulator, as items 7 and 8 predict,
but was not tried on the device. No iOS 26 device was checked.

### Pitfalls

- **Paint dims with `position: fixed`.** An absolutely positioned backdrop is
  never hit, however large, so both bars stay at the page background above a
  dimmed page.
- **Keep narrow fixed UI off the centre of an edge.** A floating toolbar, a
  toast or a framework dev toolbar fixed at `bottom: 0` takes that bar over
  and leaves it at the page background. Raise it at least 4px or keep it off
  the centre line.
- **An empty full-width `pointer-events: none` layer above a dim** (a portal
  root, a toast container) triggers the retry in item 9 and hides a
  `pointer-events: none` dim. Give the layer no size, or let the dim take
  pointer events.
- **Sticky headers keep the status bar colour when a dialog opens** (item 7).
  While the dialog is open, show a full-width fixed strip at the top edge, more
  than 10px deep (24px tested), with the dim's background: it is an ordinary
  candidate, so it replaces the stored colour. The status bar then shows the dim
  over the page background, not over the header; give the strip the header colour with the
  dim already applied, opaque, if the two must match.
- `display: none` remains the safe way to park an overlay. `opacity` below 0.1
  and `visibility: hidden` are skipped in the source, and `opacity: 0.05` was
  skipped on iOS 27.0, but Frain observed `opacity: 0` sampled earlier in 26.x.
- A header that "looks" coloured because the page behind it is coloured has no
  `background-color` of its own, so sampling falls through to `<body>`. That is
  fine if they match — and breaks the moment you add dark mode.
- Elements with `backdrop-filter` are reported to Safari as multiple colours,
  so the tint is not exactly your brand colour.
- `theme_color` in the manifest is **not** applied to home-screen apps as of
  26.1. The manifest value is still worth setting for Android.

## Recipes

### A. Solid coloured bar

```css
body {
  background: #f5f5f4;
}
header {
  position: sticky;
  top: 0;
  background: #f5f5f4;
  padding-top: env(safe-area-inset-top);
}
```

Both the sampled header and the body fallback are the same colour, so the tint
is correct whichever branch Safari takes.

### B. Blurred translucent bar

Give the status-bar strip its own blurred layer, so content scrolling under it
stays legible:

```css
body::before {
  content: "";
  position: fixed;
  inset: 0 0 auto 0;
  height: env(safe-area-inset-top);
  z-index: 1000;
  backdrop-filter: blur(12px);
  mask-image: linear-gradient(to bottom, #000 60%, transparent);
  pointer-events: none;
}
```

Source: Daniel Pietzsch. Note this element also becomes the sampling target —
which is usually what you want.

For a softer result, stack several `backdrop-filter` layers with increasing blur
radii and gradient masks (a "progressive blur") rather than one hard edge.

### C. Light and dark

Drive the real colours from `prefers-color-scheme` (that is what Safari 26
samples) and keep a `theme-color` media array for Chrome:

```css
body {
  background: #f5f5f4;
}
@media (prefers-color-scheme: dark) {
  body {
    background: #1c1917;
  }
}
```

```html
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#f5f5f4" />
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#1c1917" />
```

### D. A dim that reaches the status bar and address bar

The page viewport stops short of the screen in a Safari tab — 714pt of 874 on
an iPhone 17 Pro — and the status bar above it and the address bar below it are
Safari's. A dialog's dim only reaches them through edge sampling, so it has to
be the element sampling finds:

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
```

```css
.dim {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 0.2);
}
```

- `position: fixed`, never `absolute`: an absolute dim, however tall, dims the
  page and leaves both bars at the page background.
- `inset: 0` alone sizes it; `min-height: 100dvh` or a page-height variable
  adds nothing to the bars.
- Nothing narrower than 90% fixed on the centre of either edge above it, and no
  empty full-width `pointer-events: none` layer above a `pointer-events: none`
  dim.
- A page whose sticky header already tints the top keeps that tint: add the
  edge strip from Pitfalls while the dialog is open.
- Fades work, but the bars do not fade with them: sampling ignores `opacity`
  from 0.1 up, so each bar switches colour as the fade crosses 0.1.

Source: WebKit; Joe Bell (iOS Simulator 26.5 23F77 and 27.0 24A434,
2026-09-22; verified iPhone 17 Pro, iOS 27.0, 2026-09-23), in
[sources.md](sources.md).

## macOS

For Safari browser tinting versus an installed Dock app's title-bar snapshot,
read [macos-add-to-dock.md](macos-add-to-dock.md). It records the Mac-specific
thresholds, settings and tested versions; do not apply iOS sampling thresholds
to Mac. Source: Joe Bell; Mac tinting sources in [sources.md](sources.md).

## Make the layout robust when the top inset is `0px`

`env(safe-area-inset-top)` is legitimately `0` on non-notched devices, often in
landscape, and was `0` in standalone throughout iOS 26.1 (WebKit 301994). So:

- Express bar height as `base + env(safe-area-inset-top)`, never as
  `env(safe-area-inset-top)` alone.
- Don't branch on `inset > 0` to decide "is this a modern iPhone".
- Check the design at inset `0px` (Safari on desktop, responsive design mode) as
  well as with a notch.

Source: Joe Bell.

Version-specific behaviour: [ios-26-notes.md](ios-26-notes.md). Credits:
[sources.md](sources.md).
