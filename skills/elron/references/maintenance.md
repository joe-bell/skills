# Maintaining this skill

## 0. Porting

- Copy the whole directory, including `scripts/` and `references/`, and keep
  its relative links.
- Recreate the host tool's discovery link (for example Claude Code reads
  `.claude/skills/<name>`; a relative symlink to the copied folder works)
  rather than copying any symlink.
- `metadata.upstream` is the public copy, published manually.
- **Never commit a station or a farecard number into this skill.** They are
  per-install state kept in `~/.config/elron/config.json`; section 1 of
  [SKILL.md](../SKILL.md) says how they get there. A copy of this skill
  carrying someone's station or card is a bug.

## 1. Conventions

- Neither source publishes a schema, so every rule in the script is observed.
  Record each one, with the date it was seen, in [sources.md](sources.md).
- Keep `scripts/elron.py` to the Python standard library, so it runs in any
  host's sandbox without an install step.
- Always send the script's own `User-Agent`. Ridango answers 403 to urllib's
  default one, and mocked tests won't show it: run every change against the
  live sources before calling it done.
- Feed text is untrusted. The map takes it only as escaped JSON and sets it
  with `textContent`, or HTML-escaped in an SVG `title`; never as markup, and
  never inside a JavaScript template literal. Keep it that way.
- The default map makes no network requests, because Claude's artifact preview
  blocks them, and its Content-Security-Policy meta tag enforces that. Anything
  that needs the network belongs behind `--tiles`, with the plain map as its
  fallback.
- Judge a train against the live feed before its timetable: a late train can
  still be caught after its timetabled departure, and is still on its way after
  its timetabled arrival. Trains already on their way stay out of the main
  rows, so the first row is always the next one to catch.
- To redraw the outline, take `countries-10m.json` from world-atlas, keep ids
  233, 428, 440, 643, 246 and 112, clip each outer ring to `OUTLINE_BOX`,
  simplify to 0.01°, drop rings under 0.003 square degrees, and encode them as
  the comment above `OUTLINE` describes.
- `TRACKS`, at the end of the script, is the track network `passing` uses. To
  redraw it, query `api.peatus.ee`'s GraphQL endpoint for
  `routes(transportModes: RAIL)` with each pattern's stops (`name`, `lat`,
  `lon`); keep Elron's routes; join consecutive stops of every pattern; keep
  the minimum spanning tree by distance, so express hops drop out; map each
  name to its Ridango `stop_area_id` (`Riia raudteejaam` is `Riia`); and write
  each run between junctions as the comment above `TRACKS` describes. Keep
  ids, not names.
- Keep `SKILL.md` at ≤ 500 lines / 5,000 words, wrapped around 80 columns.
- Bump `metadata.version` for every content change, and `metadata.reviewed`
  whenever the sources are re-checked.

## 2. Re-checking the sources

```sh
python3 scripts/elron.py trips tallinn tartu --all
python3 scripts/elron.py trips kloogaranna rapla
python3 scripts/elron.py trips tartu riga
python3 scripts/elron.py live --map
python3 scripts/elron.py live --map --tiles
python3 scripts/elron.py passing tapa
```

Confirm that rows still carry fares, bike flags and readable notices; that a
notice naming a station off the trip is left out; that a route with no direct
train still finds journeys with one change; that a train still running after
leaving the first stop is listed under `Already on the way`; that running
trains still have a delay, last stop and position; and that `passing` places
trains on both sides of the station and marks an express as not stopping.
Open both maps in a browser: the plain one should show the outline and
trains, the `--tiles` one street tiles as well. Note anything that moved, with
the date, in [sources.md](sources.md).

## 3. Validation

From the repository root:

```sh
npx prettier@3 --check .
npx skill-check@1.2.0 check ./skills --no-security-scan --strict
python3 -m py_compile skills/elron/scripts/elron.py
```
