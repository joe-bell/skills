# Startup ("splash") images on iOS

## How iOS picks one

Startup images are an iOS/iPadOS feature. macOS Dock web apps have no launch
image concept — there is nothing to generate for them.

When a home-screen app launches, iOS looks through the `<link
rel="apple-touch-startup-image">` elements in the page it cached at install
time and uses the **first whose `media` query matches exactly**. There is no
scaling and no fallback: a device with no matching entry gets a blank screen in
the app's background colour (usually white).

Requirements:

- `apple-mobile-web-app-capable` must be `yes`. Without it, no startup image is
  shown at all — this is the single most common cause of "splash screens
  stopped working" after a framework upgrade.
- The links must be in the HTML of the page that was added to the home screen.
- The images must be fetchable **without cookies** (see below).

## Link template

```html
<link
  rel="apple-touch-startup-image"
  href="/splash/{width}/{height}/{dpr}?v1"
  media="(device-width: {width}px) and (device-height: {height}px) and (-webkit-device-pixel-ratio: {dpr}) and (orientation: {portrait|landscape})"
/>
```

`{width}`/`{height}` are **CSS points** in the media query. For landscape
entries, swap them: a 393×852 device gets a portrait entry with
`device-width: 393px, device-height: 852px` and a landscape entry with
`device-width: 852px, device-height: 393px`.

## Pixel maths

Image pixel dimensions = CSS points × device pixel ratio.

| Device (points) | DPR | Portrait image | Landscape image |
| :-------------- | :-- | :------------- | :-------------- |
| 393 × 852       | 3   | 1179 × 2556    | 2556 × 1179     |
| 402 × 874       | 3   | 1206 × 2622    | 2622 × 1206     |
| 820 × 1180      | 2   | 1640 × 2360    | 2360 × 1640     |

Get this wrong and iOS either rejects the image or stretches it.

## Design rules

- The background **must** equal the manifest `background_color` and the
  `<body>` background. Any difference shows as a flash at the splash → first
  paint handover, which is the exact thing a splash screen exists to hide.
- Centre the mark/wordmark and keep it well inside the safe area. The status
  bar, notch, and home indicator all overlay the splash and vary per device.
- Decorative framing generally only works in portrait — in landscape it either
  crops or looks stretched. It's fine to render decoration portrait-only.
- Don't put text you'll want to translate or update frequently in the splash;
  it's cached hard.

## What has to exist

Three artefacts, all derived from **one device table** so they can never drift
apart. Source: Joe Bell.

1. **The image set.** For every unique `width × height @ dpr` triple in the
   table, two PNGs — portrait and landscape — sized points × dpr. With the
   table in [ios-devices.md](ios-devices.md) that is 22 triples × 2 = 44
   images.
2. **The link list.** Two `<link rel="apple-touch-startup-image">` elements per
   triple, each carrying the exact four-clause media query above (device-width,
   device-height, `-webkit-device-pixel-ratio`, orientation) and a cache-bust
   query on the `href`.
3. **The device table itself**, as the single source of truth that both of the
   above are generated from. Adding a device should be a one-line edit that
   produces both a new pair of images and a new pair of links.

Each image is the background colour plus a centred mark. Decoration beyond that
generally only works in portrait — see the design rules above.

Two neutral ways to produce the set:

- **Static export at build time** — render the PNGs into your output directory
  and commit or generate them during the build. Simple and trivially
  cacheable; the cost is a pile of binaries.
- **An image endpoint** — serve `/splash/{width}/{height}/{dpr}`, rendering per
  size, prerendered or cached at the edge. Nothing binary enters the repo and
  new sizes need no rebuild of assets; the cost is a rendering path to keep
  working. Whichever you choose, validate the requested size against the device
  table so an unknown triple fails loudly instead of returning a blank image.

## Cache busting

iOS caches startup images extremely aggressively, per home-screen entry.

- Add a version query to every `href` (`?v2`) and bump it whenever the design
  changes. Source: Joe Bell. This forces a new URL for anything not yet installed.
- For an app already on the home screen, the only reliable refresh is to
  **remove and re-add** it. Say so in your release notes; do not spend a day
  chasing a "stale splash" bug.

## Verification

- View the deployed HTML and count the emitted `apple-touch-startup-image`
  links: the total must equal unique triples × 2.
- `curl -I` one image URL with **no cookies**: it must return `200` and
  `content-type: image/png`. A redirect to a sign-in page means the splash will
  silently never appear for signed-out installs.
- Add to home screen, kill the app, cold-launch, and watch the handover.

## Gotchas

- **Device aliases produce duplicate links.** Device tables are usually keyed
  by model name, and many names share one triple (iPhone 13, 13 Pro, 14, 15 and
  16 are all 390×844@3). Iterating over names emits one `<link>` per name —
  easily 100 links for ~44 unique sizes. Deduplicate by `width × height @ dpr`
  before emitting.
- Landscape entries double the count; that part is unavoidable.
- New devices need a new row _and_ a cache-bust bump, or existing installs keep
  the old set.
- Splash images are unrelated to the manifest — Android uses `background_color`
  - icon + `name` instead, and needs none of this.

Device sizes: [ios-devices.md](ios-devices.md). Credits: [sources.md](sources.md).
