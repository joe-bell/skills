# Sources & credits

Format: **Author — Title (date) — URL** — what this skill took from it.

## Primary sources

- **Ridango — Elron intercity API (observed 2026-10-02) —
  `https://api.ridango.com/v2/64`** — stops from
  `GET /intercity/originstops`; direct journeys from
  `PUT /intercity/stopareas/trips/direct` and journeys with one change from
  `PUT /intercity/stopareas/trips/transfer`. Both take a JSON body with
  `channel` set to `web`, the `date`, and the origin and destination
  `stop_area_id`. `64` is Elron's agency id. Observed details:
  - Times are ISO 8601 with the Tallinn offset, for example
    `2026-10-03T05:02:00.000+03:00`.
  - `product.price` is euros (`12.9`); `price_vat` is not a VAT-inclusive
    price. The second leg of a transfer journey can carry no product.
  - `bikes_allowed` is the string `"1"` when bikes are allowed.
  - `trip_messages` and `disruption_messages` are objects with `id`,
    `message_en`, `message_et` and `message_ru`; the same notice repeats
    across legs and coupled trains.
  - `ext_trip_id` joins train numbers with `/` (`14/114/871`) for trains that
    change number along the way.
  - The API answers 403 to urllib's default `Python-urllib/x.y` User-Agent;
    curl, Node and any custom User-Agent are fine.
  - No endpoint listing a trip's stops was found. To tell whether a notice's
    station is on the user's stretch, the script asks for the same train
    (same departure, a shared train number) from the leg's start to that
    station, and checks it arrives before the leg ends.
  - Notices travel with the whole train: "transfer to another train at Tapa"
    also shows on a stretch of that train that never reaches Tapa.
  - Riga is listed as `Riia`.
- **Ridango — farecard balance (unverified with a real card) —
  `GET /tickets/web/cardtype/U/card/<number>/balance.json`** — `balance` read
  as cents, following an earlier client of the same endpoint; an unknown card
  number answers HTTP 409.
- **Elron — live map feed (observed 2026-10-02) —
  `https://elron.ee/map_data.json`** — one record per running train, with
  Estonian keys: `reis` (train number, matching one part of Ridango's
  `ext_trip_id`), `liin` (line), `reisi_algus_aeg` and `reisi_lopp_aeg`
  (scheduled start and end), `erinevus_plaanist` (minutes late, empty when on
  time), `reisi_staatus` (`plaaniline` when running to schedule),
  `viimane_peatus` (last stop), `kiirus` (km/h), `latitude`, `longitude`,
  `rongi_suund` (heading), `asukoha_uuendus` (Tallinn-time update stamp),
  `lisateade` and `pohjus_teade` (notes). The response sends no CORS headers,
  and `elron.ee` sends `X-Frame-Options: SAMEORIGIN`.
- **Peatus.ee — national public transport timetable, Digitransit GraphQL
  (read 2026-10-03) —
  `https://api.peatus.ee/routing/v1/routers/estonia/index/graphql`** — the
  order of stations along each Elron line and their coordinates, read once to
  build `TRACKS` in the script; the script never calls it. Ridango stops carry
  no coordinates. Some stops share coordinates (Aardla and Kirsi), and a few
  names differ from Ridango's (`Klooga aedlinn`, `Zemitāni`,
  `Riia raudteejaam`).

## Libraries

- **Natural Earth — 1:10m Admin 0 countries, version 4.1.0 (public domain) —
  https://www.naturalearthdata.com**, through **world-atlas 2.0.2 —
  https://github.com/topojson/world-atlas** (`countries-10m.json`, ISC) — the
  outline embedded in `scripts/elron.py`: Estonia, Latvia, Lithuania, Russia,
  Finland and Belarus, clipped to 20.8–29.6°E and 55.6–60.6°N, simplified to
  0.01° with Douglas–Peucker, and without rings under 0.003 square degrees.
  The layer has no lakes, so Lake Peipus draws as land.
- **MapLibre GL JS 5.24.0 — https://maplibre.org** — the `--tiles` map, loaded
  from cdnjs, with the few CSS rules it needs inlined.
- **OpenFreeMap — https://openfreemap.org (read 2026-10-02)** — the map's
  tiles, through its `liberty` style. No key or account and no stated usage
  limits; it asks for an OpenStreetMap and OpenMapTiles credit, which the
  page's credit line shows. OpenStreetMap's own tile servers, used before,
  refuse a page opened from a local file, which sends no Referer.

## Hosts

- **Claude — artifact preview (observed 2026-10-02)** — runs inline scripts,
  allows outside scripts only from cdnjs, cdn.jsdelivr.net, cdn.tailwindcss.com
  and code.jquery.com and outside stylesheets only from fonts.googleapis.com,
  and blocks every other request, tiles and style JSON included. A MapLibre
  page raised an uncaught script error there, which is why the default map is
  self-contained.
