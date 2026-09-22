---
name: letterboxd-diary
description: Fetch recently watched films from a Letterboxd member's diary RSS feed and render them as a compact markdown list, with first-run setup for the username. Use when asked what someone last watched, their recent films, their Letterboxd diary or activity, films watched since a date or in a period, their last N movies, or their ratings of recent films — even if Letterboxd isn't named, or if they say "watchlist" when they mean watched films.
metadata:
  source: hand-maintained by Joe Bell; derived from the public Letterboxd RSS feed
  reviewed: "2026-09-22 against four live letterboxd.com RSS feeds"
  upstream: "https://github.com/joe-bell/skills/tree/main/skills/letterboxd-diary"
  version: "2026-09-22.9"
allowed-tools: Bash(curl -sSf https://letterboxd.com/:*) WebFetch(domain:letterboxd.com)
---

# Letterboxd diary

Pull watched films from a member's public Letterboxd RSS feed and render them as
a markdown list.

## 1. Username

The skill ships with no username. Resolve one in this order, and stop at the
first that answers:

1. **A username in the request.** "What has `<username>` been watching?" wins
   over anything saved. Use it for that request only.
2. **A saved username**, in whichever of these the host has:
   - the `LETTERBOXD_USERNAME` environment variable;
   - a `Letterboxd username: <username>` line in the host's persistent
     instructions or memory — `CLAUDE.md`, `AGENTS.md`, a memory file, a user
     preferences file.
3. **Ask.** One question and nothing else: "What's your Letterboxd
   username?" Explain that it is the last path segment of the profile URL —
   `letterboxd.com/<username>/` — only if asked what that means.

After asking, offer once to save it, and write it only where the user agrees:

- export `LETTERBOXD_USERNAME=<username>` in their shell profile, or
- add `Letterboxd username: <username>` to the host's instructions or memory
  file.

**Never edit this file to store the username.** Installs are copied folders — a
username written into `SKILL.md` is lost the next time the skill updates, and
leaks if the install is shared. Do not create config files inside the skill
directory either, for the same reason.

An unknown username returns HTTP 404, and `curl -f` then exits non-zero with a
message naming the 404. **Read the message, not the exit code** — the same 404
exits 22 over HTTP/1.1 and 56 over HTTP/2. Source: curl 8.7.1, observed
2026-09-22. Treat it as a wrong username: say which one was tried and ask for
the right one, and do not guess variations. Any other non-zero exit is not a
bad username; rung 1 of section 2 says how to tell a blocked host from a fault
somewhere else.

## 2. Source

- Feed: `https://letterboxd.com/<username>/rss/`
- Fetch it fresh every time; the diary changes often.

### Retrieval ladder

Hosts differ in what may reach the network, and a host that blocks one route
usually still has another. Try these in order, allow each rung **one** attempt,
and move down on failure. Never retry a rung that has already failed, and never
go back up.

1. **A shell, with curl.** The fast path.

   ```
   curl -sSf https://letterboxd.com/<username>/rss/
   ```

   Read the error, not the exit code, and sort it into three:
   - **A 404** is a wrong username — section 1.
   - **A policy denial** — a 403, a proxy refusal, a deny-reason header naming
     a host allowlist, a blocked DNS lookup — means the host will not let the
     shell reach letterboxd.com. Drop to rung 2 and say so once at the end.
     Source: HTTP 403 with a deny-reason header naming a host allowlist,
     claude.ai web chat, 2026-09-22.
   - **Any other failure** — a 5xx from Letterboxd, a TLS error, no curl on the
     machine — also drops to rung 2, but it is not an allowlist problem. Report
     what actually failed instead.

2. **The host's fetch tool**, if it has one. Two failures, leading different
   ways:
   - **It refuses the URL over where the URL came from.** Some hosts only open
     URLs that appeared in a user message or an earlier result, and a skill
     file does not count. Go to rung 3. Source: refused as a permissions error
     on claude.ai web chat, and in a Claude Desktop local-agent session,
     2026-09-22.
   - **Anything else** — no fetch tool at all, or one that converts the page to
     markdown and drops the namespaced `letterboxd:*` elements section 3
     parses. Rung 3 cannot help with either, so go to rung 4.

3. **Ask for the URL back.** Only after that first refusal. Such a host will
   open the very same URL once it has appeared in a user message, so the
   permission is one paste away. Fetching the pasted URL is a fresh call the
   host now allows, not a retry of rung 2.

   Put the feed URL in a fenced code block and ask for it back:

   ```
   To finish setup, send this link back as its own message:
   https://letterboxd.com/<username>/rss/
   ```

   A fenced block — not inline code, not a link. Copying out of a fence gives
   plain text, and a client that auto-links a bare domain can send the domain
   and the path as separate pieces, so the full URL never arrives as one string
   and the fetch is refused again. Say nothing else unless asked why.

   When the reply arrives, fetch the URL exactly as sent, then check the
   response as rung 2 would: it has to be the raw feed with the namespaced
   `letterboxd:*` elements intact. Only then continue with section 3.

   A paste settles where the URL came from and nothing else, so this rung ends
   at rung 4 whenever that isn't the whole problem: the fetch fails for any
   reason other than provenance, or it returns markdown with the namespaced
   elements stripped. A reply that still isn't one contiguous URL gets one
   further ask for it as plain text, then rung 4 as well.

   The permission belongs to the conversation, so this repeats in each new one
   on such a host. With the username already saved, skip the question in
   section 1 and go straight to the URL block. Source: fetch refused from the
   skill file, then returning `application/rss+xml` with all 50 entries and
   every namespaced element intact once pasted, claude.ai web chat,
   2026-09-22.

4. **A browser tool**, if the host has one — an in-app browser pane or a
   browser extension. Navigate to the feed URL and read the page text. Browsers
   serve the feed as plain XML source with every namespaced element intact, so
   section 3 parses it unchanged. A full 50-entry feed runs to about 43 KB, so
   raise any character limit the read offers rather than parsing a truncated
   feed. Source: `letterboxd.com` RSS feed read through the Claude desktop
   app's Chromium browser pane (Chrome 152), macOS 26.0 / Darwin 27.0.0,
   2026-09-22.

**Never web-search for the feed.** Search engines do not index RSS feeds, so a
web search spends a round trip and returns nothing usable. The lower rungs are
the answer to a blocked rung 1 — and looking up the host's own browser tool,
where tools are listed or loaded on demand, is part of taking rung 4, not a
search.

### When network policy blocks the shell

Only when rung 1 ran and failed with a policy denial — a 403, a proxy refusal,
a deny-reason header naming a host allowlist, a blocked DNS lookup — add one
line after the films: the host would not let the shell reach
`letterboxd.com`, and allowing that domain in its network settings makes every
later request a single fetch, with no paste step and no browser. Once per
conversation, not once per request.

Say none of that otherwise. A 5xx, a TLS error or a missing curl is
Letterboxd's fault or the machine's, and no allowlist will touch it — name the
actual failure if it is worth naming at all. A host with no shell has nothing
to allowlist either.

If asked where that setting is, answer for the host in hand rather than
guessing a menu:

- **claude.ai** — Settings, then Capabilities, then code execution and file
  creation, which is where the allowed-domains list sits. On an
  organisation-managed plan an admin may have to add the domain instead.
  Source: reported from a claude.ai session, 2026-09-22.
- **Anywhere else** — it is the host's sandbox or code-execution network
  allowlist. Name `letterboxd.com` and let the user find it; do not invent a
  path.

The feed is newest-first by publish date and carries a fixed window. Section 4
says what that window actually covers — it is not simply "the last 50 things".

It does not include the watchlist (films saved to watch later). If asked for the
actual watchlist, say there's no official feed for it and link
`https://letterboxd.com/<username>/watchlist/`.

A member who has logged nothing has a feed with no `<item>` elements. Say the
diary is empty rather than reporting an error.

### Pre-approved calls

`allowed-tools` pre-approves exactly two things and nothing wider: curl against
`https://letterboxd.com/`, and fetching that one domain.

- Use the flags as written. The entry is a literal command prefix, so a
  different flag order is a different command and won't match.
- `-f` makes curl exit non-zero on a 404 rather than handing back an error page
  to parse.
- Some hosts split `allowed-tools` on spaces, which would break the curl entry.
  If it isn't honoured, that's why — the skill still works, it just asks for
  permission first.
- Rung 4 of the ladder is deliberately not listed. Browser tools are named
  differently on every host, so pre-approving one would be a guess; expect a
  permission prompt there.

## 3. Parsing

Each film is an `<item>` with these fields. Source: `letterboxd.com` RSS feed,
observed 2026-09-22.

- `letterboxd:filmTitle` — film title (use this, not `<title>`, which also
  contains year and stars)
- `letterboxd:filmYear` — year
- `<title>` — `Title, Year - ★★★★` when rated, or plain `Title, Year` when not.
  **Do not parse the rating out of it.** A film title can itself contain
  space-hyphen-space, so `Example - Part Two, 2020` has a suffix that looks like
  a rating and is really part of the title. Use `letterboxd:filmTitle` for the
  title and the field below for the rating.
- `<link>` — diary entry URL
- `letterboxd:watchedDate` — date watched (YYYY-MM-DD)
- `letterboxd:memberRating` — numeric rating, e.g. `3.5`. **Absent entirely
  when the film is unrated**, so its presence — not the title text — is the
  test for whether a rating exists. Source: observed across four public feeds,
  2026-09-22
- `letterboxd:rewatch` — `Yes` / `No`
- `letterboxd:memberLike` — `Yes` / `No`
- `tmdb:movieId`, `<pubDate>`, `<guid>`, `<dc:creator>`
- `<description>` — poster image plus review text or "Watched on …"

Skip items without `letterboxd:filmTitle` (these are lists, not diary entries).

## 4. Selecting items

Filter and sort on `watchedDate`, not `pubDate` — entries are sometimes logged
days later.

- Default (no qualifier): the single most recent film. Like the output format,
  this is a default — if the user would rather a bare "what have I been
  watching?" return several, follow that.
- "last N" / "past N films": the N most recent.
- "since DATE": every film with watchedDate on or after DATE.
- Ranges ("in August", "this year", "between X and Y"): watchedDate within the
  range, inclusive.
- Filters on rating, rewatch, or liked films are fine to apply on top.

Sort newest watchedDate first; keep feed order for ties. Rewatches are separate
entries — keep them all.

### Coverage and truncation

The window is the 50 most recent **diary entries** by publish date. The member's
lists sit on top of that and are skipped, so total `<item>` count runs higher —
50 to 100 across the feeds checked. Source: observed across four public feeds,
2026-09-22.

Judge completeness by the diary-entry count, not by dates:

- **Fewer than 50 diary entries** — that is the member's whole diary. Results
  are complete; say nothing.
- **Exactly 50** — the window is full and older activity has been pushed out.
  For a "since" or range request reaching at or before the oldest `pubDate` in
  the feed, return what's there and add one line saying the feed only reaches
  back to that publish date, linking
  `https://letterboxd.com/<username>/films/diary/`.

**Never treat the oldest `watchedDate` as the boundary.** Entries are published
when logged, not when watched, so a single backdated entry drags that minimum
years earlier than the real coverage — one feed checked reaches back only to
December 2025 by publish date yet contains a January 2024 viewing. Reading that
as "history goes back to January 2024" would report an empty 2024 as a complete
answer.

## 5. Output format

This is a default, not a rule. It's the compact shape most requests want — if
the user asks for something else, give them that instead and keep it for the
rest of the conversation.

### One film

A single result is a sentence, not a list. Give the film on its own line with
no bullet:

```
[Title](link) (Year) ★★★★
```

A one-item bulleted list reads as the start of a list that never arrives. The
default in section 4 is a single film, so this is the common case.

If that entry has a review, put it on the next line, still unbulleted:

```
[Title](link) (Year) ★★★★
Review text.
```

### Several films

One bullet per film:

```
- [Title](link) (Year) ★★★★
```

- Only the title is linked; the year sits in plain parentheses after it.
- Rating is rendered from `letterboxd:memberRating`: one ★ per whole point plus
  `½` for a half, so `3.5` → ★★★½ and `5.0` → ★★★★★. Omit it entirely when
  the field is absent.
- If an entry has a review, render it as a sub-bullet under the film (see
  Reviews below).

### Say nothing else

The films are the whole answer. Unless the request asked for more, add no
preamble, no closing line, no headers, and no sub-bullets beyond a review — and
no commentary around the output either. Watched date, rewatch, rating, likes and
counts are details: silence about them is correct, not incomplete.

Three things override this, because they change what the answer means rather
than decorate it: the truncation line in section 4, saying the diary is empty
when it is, and the blocked-shell line in section 2.

### Adding fields

Every field in section 3 is available on request — watched date, rewatch,
liked, the numeric rating, TMDB ID, published date — as is the poster URL,
which comes from the `<img>` tag inside `<description>`. Add them as sub-bullets
under each film, or inline if that reads better for what was asked.

Don't volunteer them: "when did I watch these?" asks for the date, "what did I
watch last week?" does not. Asking for "details" or "everything" means all of
them.

### Changing the shape

Equally fine when asked: a table, grouping by month or by rating, sorting
oldest first, numbering the list, plain text without links, counts and
averages, or dropping the year or stars. Follow the request rather than this
section.

## 6. Reviews

`<description>` is HTML: a poster `<img>` paragraph, then either the review text
or a plain "Watched on <date>." line.

- It's a review when `<guid>` starts with `letterboxd-review-`, or when the
  remaining text isn't just the "Watched on …" line. Plain diary entries use
  `letterboxd-watch-`. Source: `letterboxd.com` RSS feed, observed 2026-09-22.
- Strip the `<img>` paragraph and any spoiler notice ("This review may contain
  spoilers."), convert remaining paragraphs to plain text, and keep emoji and
  line breaks.
- Multi-paragraph reviews: one sub-bullet, paragraphs joined with a line break.
- No review → no sub-bullet. Never render the "Watched on …" line.

## 7. Examples

Request: "films since 5 Sept"

```
- [Tony](https://letterboxd.com/<username>/film/tony-2026/) (2026) ★★★½
- [Casablanca](https://letterboxd.com/<username>/film/casablanca/) (1942) ★★★★★
- [Point Break](https://letterboxd.com/<username>/film/point-break/) (1991) ★★½
```

Request: "what did I watch on 2 Aug" — one film, so no bullet

```
[Spider-Man](https://letterboxd.com/<username>/film/spider-man/) (2002) ★★★½
Finally caught this in 35mm.
```

Request: "what was the last thing I watched"

```
[Casablanca](https://letterboxd.com/<username>/film/casablanca/) (1942) ★★★★★
```

Request: "last 3 films, with the dates"

```
- [Tony](https://letterboxd.com/<username>/film/tony-2026/) (2026) ★★★½
  - Watched 2026-09-19
- [Casablanca](https://letterboxd.com/<username>/film/casablanca/) (1942) ★★★★★
  - Watched 2026-09-12
- [Point Break](https://letterboxd.com/<username>/film/point-break/) (1991) ★★½
  - Watched 2026-09-06
```

## 8. Maintenance

See [maintenance.md](references/maintenance.md) for how to amend this skill, and
[sources.md](references/sources.md) for what it is built from.
