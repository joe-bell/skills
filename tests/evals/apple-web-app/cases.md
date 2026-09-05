# Apple web app behavioral cases

Run each case in a fresh task with only the skill under test and the input
below. Keep outputs in a temporary directory. For a before/after comparison,
use the same model, effort and inputs and separate tasks. Do not give the
execution agent the rubric or another run's answer. These cases test decisions
and reporting; they do not establish Safari rendering or device compatibility.

## Inputs

1. **Mac icon:** "Our site is only installed through Safari Add to Dock on Mac.
   Its manifest has one 192px PNG icon. Give a focused implementation plan to
   improve the Dock icon. Don't change anything else."
2. **Splash:** "An iPhone home-screen splash stopped appearing after a framework
   upgrade. Rendered HTML includes mobile-web-app-capable=yes and a matching
   apple-touch-startup-image link, but no apple-mobile-web-app-capable. Give
   the smallest fix and explain how to verify it."
3. **Safe area:** "Fix only this iPhone header: height: env(safe-area-inset-top).
   Its design height is 56px plus safe area. The rest of the app works. Provide
   the CSS change and relevant verification."
4. **Audit without hardware:** "Audit an iPhone-only installed site; do not edit.
   Known evidence: viewport-fit=cover, pinch zoom allowed, an opaque 180px touch
   icon served as image/png with HTTP 200 without cookies, and an in-app Back
   button. No other files, browser, or physical device are available. Report
   what conforms and what remains unknown."
5. **Offline:** "Use this skill to add offline caching with a service worker.
   There is no installed UI issue. Explain whether this skill applies."

## Maintainer rubric

For each output, record pass/fail for relevant routing, scope preservation,
correct implementation advice, unnecessary blocking questions, and truthful
verification claims. Record the specific evidence for a failure. Do not grade
headings or exact wording. Do not call a plan a tested implementation.

Expected invariants: Mac work introduces no iOS assets; splash work identifies
the missing Apple tag; the header uses a 56px base plus inset; an audit makes
no edits or device-pass claims and distinguishes supplied evidence from unknowns;
offline work is routed outside this skill without expanding into installed UI.
Do not demand an unnecessary full-device matrix for a focused change.
