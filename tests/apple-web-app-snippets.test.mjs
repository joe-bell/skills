import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

function javascriptFences(path) {
  return [...readFileSync(path, "utf8").matchAll(/```js\n([\s\S]*?)```/g)].map(
    (match) => match[1],
  );
}

function storage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
}

test("install eligibility is pure and visits are recorded once per document", () => {
  const [source] = javascriptFences(
    "skills/apple-web-app/references/install-ux.md",
  );
  const localStorage = storage();
  const context = {
    localStorage,
    navigator: {
      userAgent: "Mozilla/5.0 (iPhone) Version/26.0 Safari/605.1",
      maxTouchPoints: 1,
    },
    window: { matchMedia: () => ({ matches: false }), navigator: {} },
  };
  vm.runInNewContext(
    `${source}; this.api = { recordInstallHintVisit, shouldShowInstallHint };`,
    context,
  );

  context.api.recordInstallHintVisit();
  context.api.recordInstallHintVisit();
  assert.equal(localStorage.getItem("install-hint-visits"), "1");
  assert.equal(context.api.shouldShowInstallHint(), false);
  assert.equal(context.api.shouldShowInstallHint(), false);
  assert.equal(localStorage.getItem("install-hint-visits"), "1");
  assert.equal(
    context.api.shouldShowInstallHint({ meaningfulInteraction: true }),
    true,
  );
  localStorage.setItem("install-hint-dismissed", "1");
  assert.equal(
    context.api.shouldShowInstallHint({ meaningfulInteraction: true }),
    false,
  );
  localStorage.setItem("install-hint-dismissed", "0");
  context.window.matchMedia = () => ({ matches: true });
  assert.equal(
    context.api.shouldShowInstallHint({ meaningfulInteraction: true }),
    false,
  );
  context.window.matchMedia = () => ({ matches: false });

  const nextDocument = { ...context };
  vm.runInNewContext(
    `${source}; this.api = { recordInstallHintVisit, shouldShowInstallHint };`,
    nextDocument,
  );
  nextDocument.api.recordInstallHintVisit();
  assert.equal(localStorage.getItem("install-hint-visits"), "2");
  assert.equal(nextDocument.api.shouldShowInstallHint(), true);
});

test("overlay viewport synchronization initializes and cleans up", () => {
  const [pageSizeSource, viewportSource] = javascriptFences(
    "skills/apple-web-app/references/overlays-and-keyboard.md",
  );
  const listeners = [];
  const removed = [];
  const properties = new Map();
  const target = (name) => ({
    addEventListener: (type, listener, options) =>
      listeners.push([name, type, listener, options]),
    removeEventListener: (type, listener, options) =>
      removed.push([name, type, listener, options]),
  });
  const visualViewport = { ...target("visualViewport"), height: 600, scale: 1 };
  const windowTarget = target("window");
  const documentElement = {
    clientHeight: 700,
    style: { setProperty: (name, value) => properties.set(name, value) },
  };
  class HTMLInputElement {}
  const cancelledFrames = [];
  let nextFrame = 0;
  const context = {
    HTMLInputElement,
    HTMLTextAreaElement: class {},
    HTMLElement: class {},
    cancelAnimationFrame: (frame) => cancelledFrames.push(frame),
    document: {
      activeElement: null,
      documentElement,
      scrollingElement: { scrollWidth: 900, scrollHeight: 1200 },
    },
    requestAnimationFrame: () => ++nextFrame,
    window: { ...windowTarget, visualViewport },
  };
  vm.runInNewContext(
    `${pageSizeSource}\n${viewportSource}; this.start = startOverlayViewportSync;`,
    context,
  );

  const cleanup = context.start();
  assert.equal(properties.get("--page-width"), "900px");
  assert.equal(properties.get("--page-height"), "1200px");
  assert.equal(properties.get("--visual-viewport-height"), "600px");
  assert.deepEqual(
    listeners.map(([targetName, type]) => [targetName, type]),
    [
      ["visualViewport", "resize"],
      ["visualViewport", "scroll"],
      ["window", "resize"],
      ["window", "blur"],
    ],
  );

  const blurListener = listeners.find(
    ([targetName, type]) => targetName === "window" && type === "blur",
  )[2];
  const input = new HTMLInputElement();
  input.type = "text";
  blurListener({ target: input });
  blurListener({ target: input });
  assert.deepEqual(cancelledFrames, [1]);

  cleanup();
  assert.deepEqual(cancelledFrames, [1, 2]);
  assert.equal(removed.length, 4);
  for (let index = 0; index < listeners.length; index += 1) {
    assert.equal(removed[index][2], listeners[index][2]);
  }
});

test("overlay fallback height follows window resizes without visualViewport", () => {
  const [pageSizeSource, viewportSource] = javascriptFences(
    "skills/apple-web-app/references/overlays-and-keyboard.md",
  );
  const listeners = new Map();
  const properties = new Map();
  const documentElement = {
    clientHeight: 700,
    style: { setProperty: (name, value) => properties.set(name, value) },
  };
  const context = {
    HTMLInputElement: class {},
    HTMLTextAreaElement: class {},
    HTMLElement: class {},
    cancelAnimationFrame: () => {},
    document: {
      activeElement: null,
      documentElement,
      scrollingElement: { scrollWidth: 900, scrollHeight: 1200 },
    },
    requestAnimationFrame: () => 1,
    window: {
      visualViewport: undefined,
      addEventListener: (type, listener) => listeners.set(type, listener),
      removeEventListener: () => {},
    },
  };
  vm.runInNewContext(
    `${pageSizeSource}\n${viewportSource}; this.start = startOverlayViewportSync;`,
    context,
  );

  context.start();
  assert.equal(properties.get("--visual-viewport-height"), "700px");
  documentElement.clientHeight = 640;
  listeners.get("resize")();
  assert.equal(properties.get("--visual-viewport-height"), "640px");
});
