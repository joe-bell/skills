# Install UX on iOS and macOS

## The flow

There is no install prompt on iOS. The user must:

1. Open the site in **Safari** — this is the Safari flow; Chrome and Firefox on
   iOS have their own menus (see below), in-app browsers can't install at all.
2. Tap the Share button.
3. Scroll to **Add to Home Screen**.
4. Confirm.

On iOS 26 any site added this way opens as a web app by default, and there is a
per-site "Open as Web App" toggle in the Share sheet / site settings that the
user can turn off. So you get standalone mode more often than before — but the
user can also opt out of it, and your layout has to survive both.

`beforeinstallprompt` does not exist on iOS. Anything you show is a _hint_
pointing at the Share sheet, not a button that installs.

## Gating rules

A hint that appears on first paint for everyone is spam. Show it only when all
of these hold:

- The browser is Safari on iOS. Chrome and Firefox on iOS have been able to
  add to the Home Screen since iOS 16.4, but their menus differ from Safari's,
  so Safari-specific copy would be wrong there — which is why the snippet
  below targets Safari only. Broaden it only if you also write per-browser
  copy. In-app browsers (Facebook, Instagram, Google) can't install at all.
- The app is not already running standalone.
- The user has shown engagement — a second visit, or a meaningful interaction
  on this one.
- They haven't dismissed it before (persist that forever, not per-session).

```js
function shouldShowInstallHint() {
  const ua = navigator.userAgent;

  // iPadOS reports a desktop UA, so fall back to touch points.
  const isIOS =
    /iPad|iPhone|iPod/.test(ua) ||
    (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
  if (!isIOS) return false;

  const isStandalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;
  if (isStandalone) return false;

  // Safari only: in-app browsers can't install at all, and Chrome/Firefox
  // reach Add to Home Screen through a different menu than the copy describes.
  if (/CriOS|FxiOS|GSA|FBAN|FBAV|Instagram/.test(ua)) return false;

  if (localStorage.getItem("install-hint-dismissed") === "1") return false;

  const visits = Number(localStorage.getItem("visits") ?? "0") + 1;
  localStorage.setItem("visits", String(visits));
  return visits >= 2;
}

function dismissInstallHint() {
  localStorage.setItem("install-hint-dismissed", "1");
}
```

Gating on engagement + persisted dismissal is the one genuinely useful idea in
most PWA-install skills; credited in [sources.md](sources.md).

## Copy

Say what they get, then how, in that order. Illustrate the Share glyph rather
than describing it.

- "Add this to your Home Screen for a full-screen, app-like version. Tap Share,
  then Add to Home Screen."
- Avoid the word "install" — nothing is installed, and iOS users don't expect
  a website to install anything.
- Give it an obvious dismiss control, and honour it permanently.

## Storage & state

- **A standalone app has its own cookie and storage jar,** but Safari copies
  the site's cookies into it **once** at install (verified on iOS 26.6 by Joe
  Bell; also reported by fozzedout) — a user signed in in Safari launches the
  installed app signed _in_, and the jars diverge from there. Other storage
  (localStorage, IndexedDB) is not copied. Keep auth in cookies.
- iOS evicts standalone app state, and suspended apps get killed. Persist
  anything worth keeping (scroll position, draft input, filter state) to
  `localStorage` and restore it on launch rather than holding it in memory.

## macOS

The flow is **File → Add to Dock** (or the Share menu) in Safari 17+. Points
that differ from iOS:

- There is no `beforeinstallprompt` in Safari on macOS either, so the same
  "hint, not prompt" rule applies.
- You rarely need a hint at all: since Safari 18, visiting a site that has an
  installed matching web app shows Safari's own dismissible "Open in web app"
  banner.
- Safari copies the site's cookies into the app once at install, so users
  normally stay signed in — don't warn them about re-authenticating.
- Any hint copy must be macOS-specific; the Share → Add to Home Screen wording
  is wrong here.

Source: WebKit blog 17.0 and 18.0; Apple Support 104996.

- **External links never open the installed app on iOS** — there is no
  deep-link association, so a link from Mail or Messages opens Safari.
  `scope` only decides whether navigations _inside_ the app stay in the app
  or hand off to the in-app browser. Source: Firtman (behaviour since
  iOS 12.2).

Credits: [sources.md](sources.md).
