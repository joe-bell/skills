# Sources & credits

Format: **Author — Title (date) — URL** — what this skill took from it.

## Primary source

- **Letterboxd — member diary RSS feeds (observed 2026-09-22, four public
  accounts) — `https://letterboxd.com/<username>/rss/`** — the whole parsing contract: the
  namespaced item fields (`letterboxd:filmTitle`, `letterboxd:filmYear`,
  `letterboxd:watchedDate`, `letterboxd:memberRating`, `letterboxd:rewatch`,
  `letterboxd:memberLike`, `tmdb:movieId`), the `<title>` shape
  `Title, Year - ★★★★`, the `letterboxd-watch-` / `letterboxd-review-` guid
  prefixes that distinguish a plain diary entry from a review, the
  `<description>` layout (poster `<img>` paragraph, then review text or a
  "Watched on …" line), and the shape of the window: 50 diary entries by
  publish date, with the member's lists carried on top (total items ran 50–100
  across the four feeds). Two facts came from comparing accounts rather than
  from one feed: `letterboxd:memberRating` is omitted entirely for an unrated
  entry, whose `<title>` then carries no star suffix; and the oldest
  `watchedDate` is not the coverage boundary, since one feed reached back only
  to December 2025 by publish date while containing a January 2024 viewing.
  Letterboxd publishes no schema for this feed, so every field here is observed
  rather than documented.

## Host behaviour

- **curl 8.7.1 (observed 2026-09-22)** — `curl -sSf` against a non-existent
  member exits 22 over HTTP/1.1 and 56 over HTTP/2 for the same 404, so the
  ladder in section 2 of [SKILL.md](../SKILL.md) keys on the error message
  rather than the exit code.
- **The Claude desktop app's Chromium browser pane, Chrome 152, on macOS 26.0 /
  Darwin 27.0.0 (observed 2026-09-22)** — rendered the feed as plain XML source
  with every `letterboxd:*` and `tmdb:*` element intact, so the parsing rules
  hold unchanged on that route. The feed measured about 43 KB for a full
  50-entry window, which is close enough to a typical read cap to be worth
  raising.
- **claude.ai web chat (observed 2026-09-22)** — rung 1 exits 22 with HTTP 403
  and an `x-deny-reason` header naming a host allowlist, so the sandbox proxy
  blocks the domain; because the error names a 403 and not a 404, the section 1
  rule already reads it as a network failure rather than a wrong username. Rung
  2 is refused with a permissions error when the URL comes from the skill file,
  and refused again when the client auto-links only part of a pasted URL, so
  the domain and the path never arrive as one string. Sending the full URL as
  its own plain message succeeds: the response is `application/rss+xml`, raw,
  with all 50 entries and every `letterboxd:*` and `tmdb:*` element intact, so
  the section 3 parsing rules hold on that route too. Allowing
  `letterboxd.com` in that host's code-execution network settings restores rung
  1 and skips all of it.
- **A Claude Desktop local-agent session (observed 2026-09-22)** — its fetch
  tool refused the feed URL on the grounds that the URL had appeared only in a
  skill file rather than in the conversation, and its sandbox had no network
  route to `letterboxd.com`; a browser tool reached it. This is one session's
  observed behaviour, not documented host policy, and it is why the ladder
  exists.

## Conventions

- **This skill (2026)** — the presentation defaults are its own, not taken from
  a published source: one bullet per film with only the title linked and the year
  in plain parentheses, the star string kept verbatim including `½`,
  filtering and sorting on `watchedDate` rather than `pubDate`, returning a
  single most recent film when the request carries no qualifier, and the
  trigger phrasing that catches "watchlist" used to mean watched films.
