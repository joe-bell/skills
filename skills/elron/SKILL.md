---
name: elron
description: Look up Elron train times, fares and connections between Estonian (and cross-border Latvian) stations, see live delays and positions of running trains on a map, and check Ühiskaart farecard balances, remembering the user's home station and cards. Use when someone asks about trains in Estonia, Elron departures, the next or last train to or from a station, whether a train is late or where it is, which trains will pass through a station, ticket prices, or the balance on their Elron or Ühiskaart card.
metadata:
  source: hand-maintained by Joe Bell; derived from the public Ridango API behind elron.ee and elron.ee's live map feed
  reviewed: "2026-10-03 against api.ridango.com and elron.ee/map_data.json"
  upstream: "https://github.com/joe-bell/skills/tree/main/skills/elron"
  version: "2026-10-02.5"
---

# Elron

Elron runs Estonia's passenger trains. Timetables, fares and farecard balances
come from the public Ridango API at `api.ridango.com`; live running data comes
from the feed behind the live map on `elron.ee`. Neither needs a login.

Use the bundled script rather than calling either source by hand. It resolves
stop names, sends requests in the shape the API expects, remembers the user's
settings and prints compact results. It needs Python 3.9+ and nothing else.

```sh
python3 scripts/elron.py stops [QUERY]
python3 scripts/elron.py trips [FROM] TO [--date YYYY-MM-DD] [--all] [--connections]
python3 scripts/elron.py live [QUERY] [--map [PATH]] [--tiles] [--watch [SECONDS]]
python3 scripts/elron.py passing STATION
python3 scripts/elron.py balance [CARD_NUMBER]
python3 scripts/elron.py config [--home STOP] [--add-card N] [--remove-card N] [--clear]
```

Run it from this skill's directory, or pass the script's full path.

## 1. Home station and farecards

The skill ships with no station and no card. Learn them from the user, once.

- **Home station.** When the user asks about a train without saying where from
  ("when's the next train to Tartu?"), run `trips TO`. If it reports that no
  home station is saved, ask which station they usually travel from, save it
  with `config --home STOP`, then answer. From then on `trips TO` starts there.
  If they name a different origin, pass both stops and leave the saved one
  alone unless they ask.
- **Farecards.** When the user asks for their balance without giving a number,
  run `balance`. If no card is saved, ask for the number, save it with
  `config --add-card N`, then answer. `balance` with no argument checks every
  saved card. Use `--remove-card` when they ask you to forget one; it takes
  the full number or the last four characters, which is all the output shows.
- `config` with no flags shows what's saved and where. Settings live in
  `~/.config/elron/config.json` (or `$ELRON_CONFIG`), readable only by the
  user. Where the filesystem doesn't persist between conversations, as in a
  hosted chat's sandbox, keep the home station in the host's own memory as
  well and pass it explicitly.

**Never write the user's station or card numbers into this skill's files.**
Installs are copied folders: anything stored here is lost on the next update
and leaks if the install is shared. Don't repeat a card number back beyond
what the answer needs.

## 2. Answering questions

Answer in a sentence or two, leading with what was asked. For "when's the next
train to Tartu?":

> The next one leaves at 16:21 and gets in at 18:20. After that: 17:37 and
> 19:02.

- Add a train's live status when it's already on its way ("it's 3 minutes
  late"). Add the fare, bikes or express only when the user asks about them.
- Relay a notice when the script shows one. It already leaves out notices that
  name only stations off the user's stretch, such as a change of train further
  down the line.
- After saving a station or card, say so in a few words. Give the file's path
  only if asked, and don't describe the script, its sources or its output.
- **Stop names** match case- and accent-insensitively ("polva" finds "Põlva"),
  and a unique partial name works too; "Riga" finds Riia. An ambiguous or
  unknown name lists the candidates; pick one or ask. `stops QUERY` helps when
  unsure what a station is called.
- **Today vs another day.** With no `--date`, the script uses today in
  Europe/Tallinn and hides trains that have already left, saying how many it
  hid. `--all` shows the whole day; `--date` picks another (convert
  "tomorrow" or "Saturday" to a date first, in Estonian time).
- **"Next train" or "last train":** run `trips` and read the first or last row.
  Rows are trains the user can still catch, allowing for a late train's delay.
- **What a row shows:** departure, arrival and journey time, then tags: the
  single-ticket fare in euros, `bikes ok` when bikes are allowed, `express`,
  Elron's notices, and `live:` for a train that is on its way right now.
- **Changes of train.** `trips` lists direct trains first. When none are left
  it adds journeys with one change automatically; `--connections` adds them
  anyway. Each says where and when to change.
- **Is my train late? Where is it?** For today, `trips` lists trains that have
  left but not yet reached the user's stop under `Already on the way`, with
  their live status, allowing for delays. `live` lists every running train
  with its delay, last stop, speed and coordinates; filter it with a line or
  stop name (`live Tartu`).
- **What goes through a station?** Only when the user asks what will pass
  through or just went through, stopping or not ("what's the next train
  through Kehra?", "what was that train that didn't stop?"), run
  `passing STATION`. "Next train" questions stay with `trips`, which lists
  trains that stop. `passing` places each running train on its line from its
  live position and speed, and says whether it stops there.

All times are Estonian local time; say so only if the user may be elsewhere. If
no journey turns up even with one change, say there's no Elron train for that
trip, not that there's no way to get there.

## 3. Live map

`live --map` also writes a self-contained HTML map of the running trains: dots
over an embedded outline of Estonia and its neighbours, coloured green (on
time), orange (late) and red (5+ minutes late). It prints the file's path; the
file goes to the system temp folder unless you pass one. The page makes no
network requests, and its own security policy forbids them, so it works
offline and in sandboxed previews such as Claude's artifacts, which block every
outside request. If the host can show HTML to the user, show that file;
otherwise give the path or open it in their browser.

`--tiles` draws the trains over OpenFreeMap street tiles instead. Use it only
for a page the user opens in their own browser: a sandboxed preview can't load
the tiles, so there it falls back to the plain map. HTML shown inside Claude
must make no outside requests.

Elron's own map can't be embedded: elron.ee forbids framing. A page can't poll
the feed either, because it sends no CORS headers. For a map that follows the
trains, run `live --map --watch` in the background on the user's own machine.
It prints the map's path straight away, rewrites the file every 15 seconds and
the page reloads itself (with `--tiles`, keeping the user's pan and zoom); stop
it when they're done. In a hosted chat, run `live --map` again when they ask
for an update.

## 4. Limits

Live data covers only trains running right now, so `passing` can't see a
train that hasn't set off yet. Its times are rough estimates from distance
and current speed; give them as "about". A train whose stopping pattern
can't be confirmed shows neither "stops" nor "doesn't stop". A train that
hasn't set off has no delay forecast, so call it scheduled rather than
promising it's on time; "running to schedule" is Elron's own status. If
`elron.ee` can't be reached, the script says so and still lists the timetable.
Fares are the full single-ticket price: discounts, period tickets and first
class aren't covered.

## 5. If a request fails

"could not reach api.ridango.com", or "live running data unavailable", in a
sandboxed host (claude.ai, ChatGPT, a cloud agent) almost always means the
sandbox blocks the domain. Tell the user to allow `api.ridango.com` and
`elron.ee` in that environment's network settings, and don't retry in a loop.
A farecard Elron doesn't recognise is reported per card; ask the user to check
the number.

For changing this skill, see [maintenance](references/maintenance.md).
