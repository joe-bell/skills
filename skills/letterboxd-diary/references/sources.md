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

## Conventions

- **This skill (2026)** — the presentation defaults are its own, not taken from
  a published source: one bullet per film with only the title linked and the year
  in plain parentheses, the star string kept verbatim including `½`,
  filtering and sorting on `watchedDate` rather than `pubDate`, returning a
  single most recent film when the request carries no qualifier, and the
  trigger phrasing that catches "watchlist" used to mean watched films.
