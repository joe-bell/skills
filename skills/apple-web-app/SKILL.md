---
name: apple-web-app
description: UI guidance for web apps installed on Apple platforms — iOS and iPadOS home-screen apps first (viewport-fit and safe areas, status bar and theme colour after iOS 26, sticky/fixed bars and overlays, startup images, icons and manifest, touch CSS, install hints, iOS-version gotchas) plus macOS Safari "Add to Dock" web apps (what carries over, what does nothing there, cookies, scope, icons, menu bar). Use when adding or debugging add-to-home-screen or Add to Dock behaviour, notch/safe-area layout, apple-mobile-web-app-* meta tags, web app manifest, splash screens, or anything that only looks wrong as an installed web app on iPhone, iPad or Mac. Not for service workers, offline caching, or push.
metadata:
  source: hand-maintained by Joe Bell; derived from a production home-screen web app plus credited external sources
  reviewed: "2026-09-04 against iOS 26.x, macOS 26 / Safari 26"
  upstream: "https://github.com/joe-bell/skills/tree/main/skills/apple-web-app"
  version: "2026-09-04.2"
---

# Apple web app UI (iOS home screen and macOS Dock)

## 1. Scope

How an installed web app **looks and feels** on Apple platforms — chrome,
safe areas, splash, icons, touch, navigation. iOS and iPadOS come first: they ignore half
the manifest and need a parallel `apple-*` meta layer. macOS "Add to Dock" is section
12, mostly a list of what does _not_ apply there. Android honours the manifest and needs
none of this. Plain HTML, CSS and DOM; Tailwind v4 equivalents are an optional reference.

**Non-goals:** service workers, offline caching, background sync, push,
`beforeinstallprompt` flows on Android. If the task is offline or caching, this
is the wrong skill.

References (read the one that matches the problem):

- [ios-26-notes.md](references/ios-26-notes.md)
- [theme-color-and-status-bar.md](references/theme-color-and-status-bar.md)
- [overlays-and-keyboard.md](references/overlays-and-keyboard.md)
- [splash-screens.md](references/splash-screens.md)
- [ios-devices.md](references/ios-devices.md)
- [install-ux.md](references/install-ux.md)
- [tailwind-css-v4.md](references/tailwind-css-v4.md)
- [macos-add-to-dock.md](references/macos-add-to-dock.md)
- [sources.md](references/sources.md)
- [maintenance.md](references/maintenance.md)

## 2. Quick checklist

Derived from Joe Bell's production experience; external rules carry their own source.

- `<meta name="viewport" content="…, viewport-fit=cover">` — without it `env()`
  insets are all `0px`.
- Emit **both** `mobile-web-app-capable` and `apple-mobile-web-app-capable`.
- Set the home-screen label: manifest `short_name` is used from iOS 11.3
  onwards; keep `apple-mobile-web-app-title` as the fallback.
- Choose `apple-mobile-web-app-status-bar-style` deliberately — see section 5.
- Manifest: `display: standalone`, and `background_color` == `theme_color` ==
  the actual `<body>` background colour.
- One 180×180 **opaque** PNG apple-touch-icon; PNG manifest icons at 192 and
  512 (`purpose: any`; add 1024 and an SVG for macOS, a maskable for Android).
- Per-device `apple-touch-startup-image` links, all on that same background.
- Mirror `env(safe-area-inset-*)` into CSS variables once, then use them
  everywhere.
- Own your scroll container; set `overscroll-behavior-y: contain` in a
  stylesheet (not from JS after the fact).
- `-webkit-tap-highlight-color: transparent`, `user-select: none` on chrome,
  `-webkit-touch-callout: none` on media (iOS only — see section 12).
- Auth/middleware must never redirect the manifest, icons or splash images —
  iOS fetches them **without cookies**.

## 3. Head tags & manifest

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-title" content="Your App" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="theme-color" content="#f5f5f4" />
<link rel="apple-touch-icon" href="/apple-icon.png" />
<link rel="manifest" href="/manifest.webmanifest" />
```

Rules:

- **The `apple-` prefixed capable tag is still required.** The unprefixed
  `mobile-web-app-capable` does not enable startup images; Safari only shows
  them when `apple-mobile-web-app-capable` is present. Frameworks that emit
  only the standard tag will silently kill your splash screens — check the
  rendered HTML, not your source. Source: Firtman; see
  [sources.md](references/sources.md) for a documented case.
- **The home-screen label** comes from the manifest `short_name` (then `name`)
  since iOS 11.3. `apple-mobile-web-app-title` still wins on older versions and
  costs nothing, so set both. Source: Firtman.
- **iOS ignores much of the manifest**: `background_color`, `orientation`,
  `maskable` icons, and (as of 26.1) `theme_color` for home-screen apps. Set
  the equivalents in the `apple-*` layer and in CSS.
- **iOS only accepts PNG icons.** SVG and WebP manifest icons are skipped.
- The three `apple-mobile-web-app-*` metas are iOS-only: no documented effect
  on macOS, and harmless to leave in place. Source: WebKit blog.
- iOS 26 opens any site added to the Home Screen as a web app (there is now a
  per-site "Open as Web App" toggle), so sites that never opted in can suddenly
  find themselves in standalone mode. The manifest is still honoured for
  `display`, `start_url`, `name` and icons. Source: WebKit blog; Firtman.

## 4. Viewport & safe areas

```css
:root {
  --safe-area-inset-top: env(safe-area-inset-top);
  --safe-area-inset-right: env(safe-area-inset-right);
  --safe-area-inset-bottom: env(safe-area-inset-bottom);
  --safe-area-inset-left: env(safe-area-inset-left);

  --header-height: calc(3.5rem + var(--safe-area-inset-top));
}
```

Rules:

- `viewport-fit=cover` is mandatory; without it every inset is `0px` and your
  layout looks fine in the simulator and wrong on a notched phone.
- Mirror `env()` into variables **once**, in `:root`: one source of truth for
  every consumer, and the resolved value becomes readable from JS via
  `getComputedStyle`, which is the only way to detect that the insets have
  arrived. Express bar heights as `base + inset`, never as the inset alone.
  Source: Joe Bell.
- **Never assume the top inset is greater than zero.** It is `0px` on the SE,
  frequently `0px` in landscape, and was `0px` in standalone on iOS 26.1 due to
  a regression. Any code branching on "has a notch" must treat `0px` as a
  legitimate answer.
- `100vh` is the reliable height on a cold standalone launch; `100dvh` reports
  the wrong value until layout settles. A single fullscreen canvas should use
  `100vh` directly (source: fozzedout); the `html, body { height: 100% }` plus
  `min-height: 100vh` scroll-root pattern in section 6 is fine.
- Don't ship `user-scalable=no` / `maximum-scale=1` to suppress double-tap
  zoom — it breaks pinch-zoom for low-vision users. Use
  `touch-action: manipulation` on the tappable elements instead.
- `interactive-widget` is unimplemented in WebKit (bug 259770); keyboard handling is a
  `visualViewport` job — see [overlays-and-keyboard.md](references/overlays-and-keyboard.md).
- **iPadOS 26 windowed mode**: home-screen apps open as resizable windows with
  system controls over the top-left corner, and `env()` does not report them.
  Keep primary controls out of that corner, or pad it (a community workaround
  uses ~64px) when the window is smaller than the screen. Source: Reinhart
  Previano K.; Apple Support.

## 5. Status bar & theme colour (iOS 26+)

`apple-mobile-web-app-status-bar-style` values:

| Value               | Bar          | Content under bar | `env(safe-area-inset-top)` |
| :------------------ | :----------- | :---------------- | :------------------------- |
| `default`           | white/system | no                | `0px`                      |
| `black`             | black        | no                | `0px`                      |
| `black-translucent` | transparent  | **yes**           | real inset                 |

`black-translucent` is the only edge-to-edge mode; it also puts the clock over
your content, so safe areas stop being optional.

**Safari 26 ignores `<meta name="theme-color">`** and instead samples page
colour to tint the top and bottom system areas. Roughly, it looks for a
`position: fixed` or `position: sticky` element touching the viewport edge
(≥ 80% of the viewport width, ≥ 3px tall, within ~4px of the top edge / ~3px of
the bottom), takes its `background-color`/`backdrop-filter`, and otherwise
falls back to `<body>`'s background, then `<html>`'s, then white/black.

Consequences:

- Give `<body>` a real background colour. A transparent root tints white.
- If you want your header colour in the status bar, the header must have an
  actual background (or `backdrop-filter`), not just inherit the page.
- Hidden overlays with `opacity: 0` are **still sampled**. Hide them with
  `display: none`.
- `viewport-fit=cover` is required for the bottom tint to apply.
- Keep the `theme-color` meta for Chrome and older Safari.

iOS/iPadOS only — a macOS Dock app has a title bar (section 12). Light/dark
recipes and the blurred bar: [theme-color-and-status-bar.md](references/theme-color-and-status-bar.md);
the 26.1 regression that zeroed the inset: [ios-26-notes.md](references/ios-26-notes.md).

## 6. Standalone layout: scroll container & bars

```css
html,
body {
  height: 100%;
}
body {
  background: #f5f5f4; /* same colour as splash + manifest */
}

#root {
  height: 100%;
  min-height: 100vh;
  overflow-y: scroll;
  overscroll-behavior-y: contain;
  isolation: isolate;
}
@media not all and (display-mode: standalone) {
  #root {
    min-height: -webkit-fill-available;
  }
}

header {
  position: sticky;
  top: 0;
  height: calc(3.5rem + env(safe-area-inset-top));
  padding-top: env(safe-area-inset-top);
}

nav.bottom {
  position: fixed;
  inset: auto 0 0 0;
  padding-bottom: calc(env(safe-area-inset-bottom) + 0.5rem);
  transform: translateZ(0);
}
```

Rules:

- **Own the scroll container.** One scrolling element gives you a readable
  scroll position and stops the document bouncing behind fixed bars; the
  `-webkit-fill-available` fallback matters only outside standalone.
  Source: Joe Bell.
- `overscroll-behavior` must be in a stylesheet that is parsed **before** the
  first `touchstart`; setting it from JS during a gesture is too late.
  Source: React Spectrum PR #8888.
- `isolation: isolate` on the scroll root keeps `z-index` sane once you add
  sticky bars, blurs and overlays.
- The home indicator auto-hides on iOS 26, but `env(safe-area-inset-bottom)`
  still reports its space — keep padding bottom bars.
- A translucent bar needs a translucent surface _and_ a blur behind it,
  otherwise content shows through crisply as it scrolls under. A progressive
  blur (stacked `backdrop-filter` layers with mask gradients) reads far more
  "native" than one flat blur; in standalone make it noticeably taller, because
  it also has to cover the status bar area. Source: Joe Bell.

**The cold-launch jump.** iOS lays out once before safe-area values arrive, so
an `env()`-padded header visibly jumps on cold launch. Prefer a CSS-only layout
correct at inset `0px` (`100vh` + `env()`, no JS). If you must gate rendering:
test the mirrored property for **non-emptiness**, not `> 0` (`0px` is valid on
no-notch devices and in landscape; getting this wrong hides the app forever on
an SE), always ship a timeout fallback, and only gate in standalone. Source: Joe Bell.

```js
// CSS keys on this: [data-ready] fades the app in; :not([data-ready]) hides it,
// but only inside @media (display-mode: standalone).
const root = document.documentElement;
const ready = () => root.setAttribute("data-ready", "");

const standalone =
  window.matchMedia("(display-mode: standalone)").matches ||
  window.navigator.standalone === true;

if (!standalone) {
  ready();
} else {
  const timeout = setTimeout(ready, 500); // never leave the app hidden
  (function poll() {
    const inset = getComputedStyle(root)
      .getPropertyValue("--safe-area-inset-top")
      .trim();
    if (inset !== "") {
      clearTimeout(timeout);
      ready();
    } else {
      requestAnimationFrame(poll);
    }
  })();
}
```

## 7. Overlays, modals, keyboard

iOS 26 clips `position: fixed` to the _inner_ viewport, so full-screen
backdrops no longer cover the page. The working pattern (from React Spectrum):

- Backdrop: `position: absolute`, sized to
  `document.scrollingElement.scrollWidth/scrollHeight` via CSS variables.
- Dialog: `position: sticky; top: calc(var(--visual-viewport-height) / 2)`
  and translate up by half its height.
- Maintain `--visual-viewport-height` from
  `visualViewport.height * visualViewport.scale`, updated on `resize` and — to
  beat the keyboard animation — on `blur`.
- Inject `overscroll-behavior: contain` from a `<style>` element, before any
  touch handling.
- Focus with `element.focus({ preventScroll: true })`, then scroll it into view
  yourself once the keyboard height is known.
- Allow two-finger gestures and drags inside text/range inputs through your
  `touchmove` prevention.

Lightbox-style takeovers: pad the toolbar with the top inset and captions with
the bottom one, and set `-webkit-touch-callout: none` on the image. Full
recipes: [overlays-and-keyboard.md](references/overlays-and-keyboard.md).

## 8. Icons

- `apple-touch-icon`: one **180×180 opaque square PNG**. iOS applies its own
  mask and shadow — don't pre-round it, and don't ship transparency (it
  composites on black).
- Manifest icons: PNG, at minimum 192 and 512, `purpose: "any"`. Add a separate
  `purpose: "maskable"` icon with safe-zone padding for Android; iOS ignores it.
- Render every size from **one vector mark at build time** onto an opaque
  background, rather than hand-exporting each. One artwork source means the
  sizes can never drift apart.
- Use the same background colour for icon, splash and `<body>`. Any mismatch
  shows as a flash between splash and first paint. Source: Joe Bell.
- Icons are fetched **without cookies**. If they 302 to a sign-in page, iOS
  falls back to a screenshot of the page. Source: Joe Bell.
- iOS caches icons per home-screen entry: after changing one you must remove
  and re-add the app to see the new artwork.
- macOS reads the **manifest** icons (not `apple-touch-icon`), accepts PNG,
  WebP and SVG; ship opaque PNGs at 512 and 1024 (an SVG listed first was not
  chosen on Safari 26.6.2). Source: Apple Developer Forums 738535; Joe Bell
  (verified 26.6.2).

## 9. Splash / startup images

```html
<link
  rel="apple-touch-startup-image"
  href="/splash/393/852/3?v2"
  media="(device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)"
/>
```

- iOS picks a startup image only on an **exact** media match. No match means no
  splash — you get a blank white screen instead.
- Image pixel size = CSS points × device pixel ratio (393×852 @3 → 1179×2556).
- Landscape entries swap width and height; the media query's `device-width` /
  `device-height` swap with them.
- Background must equal the manifest `background_color` and the `<body>`
  background, so splash → first paint is seamless. Keep artwork centred and
  well inside the safe area; the frame differs per device.
- **What you have to produce:** for each unique `width × height @ dpr` in the
  device table, two images (portrait and landscape) sized points × dpr, and two
  `<link>` elements carrying the exact media query above. Deduplicate by that
  triple, **not** by device name — a dozen iPhone models share three triples, so
  one link per name doubles your `<head>` for no benefit. Drive both the image
  set and the link list from the same device table. Source: Joe Bell.
- Add a version query (`?v2`) and bump it when the design changes; also remove
  and re-add the app, because iOS caches aggressively. Source: Joe Bell.

Startup images are iOS/iPadOS only — nothing to generate for macOS. See
[splash-screens.md](references/splash-screens.md) and the device table in
[ios-devices.md](references/ios-devices.md).

## 10. Touch & native-feel CSS

```css
:where(*) {
  -webkit-tap-highlight-color: transparent;
}
body {
  text-size-adjust: 100%;
}
header,
nav,
button,
[role="tab"] {
  user-select: none;
  touch-action: manipulation;
}
img,
video {
  -webkit-touch-callout: none;
}
.long-list > * {
  content-visibility: auto;
}
:root {
  scroll-padding-top: var(--header-height);
}
@media (prefers-reduced-motion: no-preference) {
  html {
    scroll-behavior: smooth;
  }
}
```

Rules: kill the grey tap flash globally; `user-select: none` on chrome only,
never on body text; `-webkit-touch-callout: none` on media stops the long-press
save sheet, which matters when a long press is your own gesture, as in a photo
grid that opens a lightbox (source: Firtman; Joe Bell for the photo-grid case);
`content-visibility: auto` keeps long grids smooth (source: Joe Bell);
`scroll-padding-top` stops anchors landing under a sticky header; wrap hover
styling in `@media (hover: hover)` so it never sticks on touch.

## 11. Detection & install UX

```js
const isStandalone =
  window.matchMedia("(display-mode: standalone)").matches ||
  window.navigator.standalone === true;
```

`navigator.standalone` is the iOS-only legacy flag (undefined on macOS); in CSS
use `@media (display-mode: standalone)`. Source: community skills, see sources.md.

- iOS has **no** `beforeinstallprompt`. Installing means Share → _Add to Home
  Screen_, so any "install" affordance is a hint, not a prompt.
- Only show that hint when not already standalone, after some engagement
  (second visit or a real interaction), and never again once dismissed. Target
  Safari specifically: in-app browsers can't install at all, and Chrome/Firefox
  on iOS can (since 16.4) but through a different menu than your copy will
  describe.
- A standalone app has **its own cookie/storage jar**, but Safari copies its
  cookies **once** at install, so a user signed in in Safari launches signed
  in; nothing else (localStorage, IndexedDB) copies, and jars diverge after.
  Keep auth in cookies. Source: Joe Bell (verified iOS 26.6); WWDC23 for the
  macOS half.
- iOS kills suspended standalone apps freely, so hold nothing important only in
  memory: persist drafts and positions to `localStorage` and restore on launch.
  Storage itself is best-effort on iOS — keep anything irreplaceable on the
  server. Source: Firtman; WebKit storage policy.
- **Standalone has no browser chrome, so there is no Back button.** Every
  screen needs its own way back or out. The iOS edge-swipe back gesture only
  works once the app has built in-app history (source: fozzedout), and
  out-of-scope links open an in-app browser with a Done button rather than
  leaving the app (source: Firtman, since iOS 12.2). On macOS
  `display: standalone` hides Back/Forward too — use `minimal-ui` if the site
  relies on browser navigation (source: Steiner).

Snippet and copy suggestions: [install-ux.md](references/install-ux.md).

## 12. macOS: Add to Dock

Safari 17 added File → Add to Dock; manifests are optional. Source: WebKit.

**Does nothing on macOS** — the bulk of this skill:

- `viewport-fit=cover` and every `env(safe-area-inset-*)` — all `0px`.
- `apple-mobile-web-app-capable`, `-title` and `-status-bar-style`.
- `apple-touch-startup-image` and the device table. Generate nothing.
- The cold-launch reveal gate — there is no safe-area timing problem.
- `navigator.standalone`, which is undefined. Use the media query.
- Touch CSS: `-webkit-touch-callout`, tap highlight, `touch-action`.
- Share → Add to Home Screen copy and the install-hint gating.

**Carries over:** manifest `name`, `display`, `start_url`,
`scope`, `id` and PNG icons; `@media (display-mode: standalone)`; the
one-time cookie copy at install (same as iOS, verified); and the section 5
recipe of a real `<body>` background plus a real background on any sticky
header.

**Differs:**

- Out-of-scope links open the default browser (verified macOS 26.6.2, even a
  third-party default); `window.open` opens a new app window. Safari 18+
  captures external in-scope links into the app. Source: WWDC23; Joe Bell
  (verified 26.6.2).
- `display: standalone` (or `fullscreen`) hides the toolbar; anything else
  shows Back, Forward and Share. Notifications are **silent by default** (the
  reverse of iOS); badging needs notification permission, and `shortcuts`
  become File-menu commands. Source: Steiner; WWDC23.
- Icons use the manifest, not `apple-touch-icon` (verified); ship opaque PNGs
  at 512 and 1024. SVG is optional and was not chosen on 26.6.2. Source: Apple
  Developer Forums 738535; Joe Bell (verified 26.6.2).
- Title bar colour is a snapshot at Add to Dock of `<body>`'s background (not
  manifest `background_color`), ignoring later CSS until re-add (verified macOS 26.6.2).

Full detail, the version timeline and remaining questions:
[macos-add-to-dock.md](references/macos-add-to-dock.md).

## 13. Testing checklist

- Test on a **real device** — the simulator does not reproduce safe-area timing,
  status-bar sampling or splash selection — add it to home screen, kill it and
  cold-launch it; most bugs appear after a swipe-up kill. Source: Joe Bell.
- Check portrait/landscape, notched/unnotched devices and windowed/full-screen
  iPad; focus a modal text field in light/dark mode; check the status-bar tint.
- View source: confirm **both** capable metas and startup-image links = unique
  triples × 2; `curl -I` manifest, icon and splash URLs without cookies — each
  must return 200, not a redirect. Source: Joe Bell.
- After changing icons or splash images, remove and re-add the app (source: Joe
  Bell); debug with Safari's Web Inspector (Develop → device → app).
- macOS: add to Dock; check title bar, toolbar presence, and where an out-of-scope link opens.

## 14. Gotchas by iOS version

| Version   | Behaviour                                                                                                                                                           | Mitigation                                                      |
| :-------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :-------------------------------------------------------------- |
| ≤ 11.2    | No manifest support; `apple-*` metas only (`user-scalable=no` ignored in Safari since 10, still honoured in standalone)                                             | Keep the apple layer                                            |
| 11.3      | Manifest + `env(safe-area-inset-*)` land                                                                                                                            | Baseline for `viewport-fit=cover`                               |
| 15        | `theme-color` respected in Safari UI                                                                                                                                | Still emit it for other browsers                                |
| 26.0      | `fixed` clipped to inner viewport; opaque fixed overlays don't fill; `100dvh` gap; theme-color sampling replaces the meta; any site can open as a web app           | Absolute backdrops, `opacity: .99`, `100vh`                     |
| 26.1      | Status bar opaque in standalone and `env(safe-area-inset-top)` → `0px` (WebKit 301994); `100dvh` gap fixed                                                          | Layout must be correct at inset `0px`                           |
| 26.2      | Status bar regression fixed — then **re-regressed on 26.5.2 and the iOS 27 beta** (301994 reopened); WebKit 259770 still open; 26.6 verified transparent (Joe Bell) | Never hardcode a version workaround; feature-detect             |
| iPadOS 26 | Home-screen apps open as resizable windows; system controls overlay the top-left and `env()` stays silent; no Window Controls Overlay                               | Keep chrome out of that corner; test windowed _and_ full screen |

Full matrix with sources: [ios-26-notes.md](references/ios-26-notes.md). The
macOS timeline is in [macos-add-to-dock.md](references/macos-add-to-dock.md).

## 15. Sources

Sources for every section are in [sources.md](references/sources.md); rules
without an inline tail are covered by the section's entries there.

## 16. Keeping this skill current

- Durable = device-verified behaviour, answered questions, corrected sources
  or new device sizes — not project workarounds or unverified forum claims.
- Amend the section and reference; add `Source: Joe Bell (verified <OS build>,
<date>)` or author + URL; update `sources.md`, Open questions and
  `metadata.version`; stay ≤ 500 lines / 5,000 words; run `skill-check --strict`.
- Prepare the diff for `metadata.upstream` and hand it to the user; never push
  there. See [maintenance.md](references/maintenance.md).
