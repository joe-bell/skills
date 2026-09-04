# Overlays, modals & the keyboard on iOS

## Why this is hard

iOS 26 clips `position: fixed` to the **inner** viewport rather than the layout
viewport. A backdrop that used to cover everything now covers only the visible
window, and reveals page content as soon as the user scrolls or the keyboard
resizes the viewport. Adobe's React Spectrum worked out a portable fix
(PR #8888, follow-up #8922); MUI hit the same problem (#46953). What follows is
that approach, generalised.

## 1. Page dimensions as custom properties

```js
function syncPageSize() {
  const el = document.scrollingElement ?? document.documentElement;
  document.documentElement.style.setProperty("--page-width", `${el.scrollWidth}px`);
  document.documentElement.style.setProperty("--page-height", `${el.scrollHeight}px`);
}
```

Call on open, on `resize`, and after content changes that alter page height.

## 2. Visual viewport height

```js
function syncViewport() {
  const vv = window.visualViewport;
  if (!vv) return;
  // Multiplying by scale converts visual pixels back to layout pixels.
  const height = vv.height * vv.scale;
  document.documentElement.style.setProperty("--visual-viewport-height", `${height}px`);
}

window.visualViewport?.addEventListener("resize", syncViewport);
window.visualViewport?.addEventListener("scroll", syncViewport);
// `blur` fires before the keyboard-dismiss animation finishes, so updating here
// avoids a frame where the dialog is centred against the shrunken viewport.
window.addEventListener("blur", syncViewport, true);
```

Ignore updates while `vv.scale > 1` — the user is pinch-zooming and you don't
want the dialog to chase them.

## 3. Backdrop: absolute, page-sized

```css
.backdrop {
  position: absolute;
  top: 0;
  left: 0;
  width: var(--page-width, 100%);
  height: var(--page-height, 100%);
  isolation: isolate;
}
```

## 4. Dialog: sticky, centred on the visual viewport

```css
.dialog {
  position: sticky;
  top: calc(var(--visual-viewport-height, 100vh) / 2);
  transform: translateY(-50%);
  max-height: calc(var(--visual-viewport-height, 100vh) - 2rem);
}
```

Sticky positioning inside the absolutely-sized backdrop tracks scrolling without
relying on `fixed`.

## 5. Scroll locking

Inject the rule from a `<style>` element so it is in the cascade before any
`touchstart`:

```js
const style = document.createElement("style");
style.textContent = "@layer { * { overscroll-behavior: contain } }";
document.head.append(style);
```

`@layer` keeps it at the lowest precedence so page styles still win where they
matter. Remove the element when the last overlay closes.

## 6. `touchmove` prevention

If you also prevent `touchmove` to stop background scroll, let these through:

- `event.touches.length > 1` — two-finger pinch-zoom must keep working.
- Drags that start inside a text input, `contenteditable`, or a `range` input
  (text selection and slider dragging both arrive as `touchmove`).
- Anything inside a scrollable region of the dialog itself.

## 7. Focus without scroll jumps

```js
element.focus({ preventScroll: true });
```

Then scroll it into view yourself once `--visual-viewport-height` reflects the
keyboard. Letting the browser do it produces a scrolled-and-clipped layout,
because the browser scrolls the _layout_ viewport.

## 8. Fullscreen takeovers

For a sheet or lightbox that should cover everything, add
`padding-bottom: 100vh` to the scroll container. It guarantees the surface
extends past the inner viewport no matter how the browser clips.

## 9. Container queries for dialog breakpoints

Size dialog internals with `@container`, not media queries: the dialog's own
width, not the viewport's, is what determines its layout, and the visual
viewport changes under it when the keyboard appears.

## 10. `isolation: isolate`

Put it on the backdrop and on your scroll root. Stacking contexts around
sticky bars, `backdrop-filter` and portals are otherwise unpredictable.

## iOS 26.0-only bugs

- A fully opaque fixed overlay may not fill the viewport; `opacity: 0.99` fixes
  it (Lunardi).
- `100dvh` leaves a bottom gap (Apple forums 800798/803987); fixed in Safari
  26.1 (radar 158055568).

## Lightbox notes

For a photo lightbox or any full-bleed media takeover:

- Pad the toolbar/close button with `env(safe-area-inset-top)` so it clears the
  notch, and captions with `env(safe-area-inset-bottom)` so they clear the home
  indicator. Most lightbox libraries hardcode a flat padding — override it.
  Source: Joe Bell.
- Set `-webkit-touch-callout: none` on the image, otherwise a long press opens
  the system save/share sheet instead of your own gesture.
- Drop drop-shadow filters on toolbar buttons if they sit over a blurred
  surface; on iOS they cost a lot of compositing for little effect.
- Check the library's own full-screen container against the 26.0 opaque-fixed
  bug above.

Credits: [sources.md](sources.md).
