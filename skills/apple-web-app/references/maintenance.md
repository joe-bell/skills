# Maintaining this skill

## 0. Porting

- Copy the whole directory, including `references/`, and keep its relative links.
- Recreate the host tool's discovery link (for example Claude Code reads
  `.claude/skills/<name>`; a relative symlink to the copied folder works) rather
  than copying any symlink.
- `metadata.upstream` is the public copy, published manually.

## 1. Conventions

- A durable finding is verified device behaviour, an answered open question, a
  source shown wrong, or a new device size. Exclude project-specific workarounds
  and unverified forum claims.
- Add a `Source:` tail to the affected rule. For device work, use
  `Source: Joe Bell (verified <OS build>, <date>)`; for published work, give
  the author and URL.
- In `sources.md`, use `Author — Title (date) — URL — what was taken`.
- The Open questions list in [macos-add-to-dock.md](macos-add-to-dock.md) and
  the Later releases list in [ios-26-notes.md](ios-26-notes.md) are the work
  queue.
- Keep `SKILL.md` at ≤ 500 lines / 5,000 words, wrapped around 80 columns;
  the upstream repo runs Prettier (code fences excluded).
- Keep instructions plain HTML, CSS and DOM only. Tailwind belongs in
  [tailwind-css-v4.md](tailwind-css-v4.md).

## 2. Writing up a device test

- State the OS build, Safari version and default browser once, then use one-line
  answer records such as:
  `A: title bar = #f5f5f4; body change → never; header change → no`
- Add the build/date `Source:` tail to the affected finding, then paste the
  record into `sources.md` under the tester's entry.
- Promote only durable conclusions into the matching skill section or reference;
  retain unknowns in the work queue.

## 3. Amend in place

1. Read the affected section, its reference, the relevant work queue and
   `sources.md`; then amend them in place.
2. Run the validation commands from the repository's AGENTS.md
   (`npx prettier@3 --check .` and `npx skill-check@1.2.0 check ./skills --no-security-scan --strict`,
   or the host repo's equivalents) and `wc -l -w` on `SKILL.md`.
3. Commit with a message naming the finding and the tested OS/Safari build.

## 4. Upstreaming

This local folder's public home is `metadata.upstream`; Joe Bell publishes it
manually.

1. Check drift before preparing a handoff. Fetch the upstream `SKILL.md`
   frontmatter with
   `gh api repos/joe-bell/skills/contents/skills/apple-web-app/SKILL.md` or an
   equivalent raw URL, then compare `metadata.version`.
2. If upstream is newer, merge its changes into this local copy first. If the
   repository or path does not exist, say so and stop.
3. Prepare a diff limited to this skill folder with `git diff`, or copy the
   folder, and hand it to the user with a suggested PR title/body naming the
   finding, device/OS and sources added. One finding per PR.
4. Never push to or create the upstream repository; Joe Bell publishes
   manually.

## 5. Re-check cadence

After every Apple September major release and every `.1` / `.2` point release,
re-read [ios-26-notes.md](ios-26-notes.md) and the macOS timeline. The iOS
status-bar bug (WebKit 301994) has regressed twice, so a "fixed" result remains
provisional.

## 6. Don't

- Add unsourced claims, version-sniffing advice, project paths or framework
  code.
- Reopen an answered question without a new OS/Safari build.
