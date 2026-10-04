#!/usr/bin/env python3
"""Elron (Estonian rail) train times, live running data and Ühiskaart farecard balances.

Talks to the public Ridango API that backs elron.ee, and to the feed behind
elron.ee's live train map. Standard library only, so
it runs anywhere Python 3.9+ does.

    elron.py stops [QUERY]
    elron.py trips [FROM] TO [--date YYYY-MM-DD] [--all] [--connections]   # FROM defaults to the saved home station
    elron.py live [QUERY] [--map [PATH]] [--tiles] [--watch [SECONDS]]  # trains running now
    elron.py passing STATION                               # running trains through a station, stopping or not
    elron.py balance [CARD_NUMBER]                         # default: every saved card
    elron.py config [--home STOP] [--add-card N] [--remove-card N] [--clear]

Saved settings live in a private JSON file on this machine ($ELRON_CONFIG, or
$XDG_CONFIG_HOME/elron/config.json, default ~/.config/elron/config.json).
"""

import argparse
import html
import http.client
import json
import math
import os
import re
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

BASE = "https://api.ridango.com/v2/64"  # 64 is Elron's agency id
LIVE_URL = "https://elron.ee/map_data.json"  # the feed behind elron.ee's live train map
TIMEOUT = 20
# Ridango answers 403 to urllib's default "Python-urllib" User-Agent, so always send our own.
USER_AGENT = "elron-skill (+https://github.com/joe-bell/skills)"
# Kept out of the current folder, which may be someone's repository.
DEFAULT_MAP = os.path.join(tempfile.gettempdir(), "elron-live-map.html")
# Names people use for stops Elron lists under another one, folded (see fold()).
ALIASES = {"riga": "Riia"}

try:
    from zoneinfo import ZoneInfo

    TALLINN = ZoneInfo("Europe/Tallinn")
except Exception:  # no tzdata on this machine: fall back to the local clock
    TALLINN = None


def config_path():
    if os.environ.get("ELRON_CONFIG"):
        return os.path.expanduser(os.environ["ELRON_CONFIG"])
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "elron", "config.json")


def load_config():
    try:
        with open(config_path(), encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        sys.exit(f"error: could not read {config_path()}: {e}")
    return data if isinstance(data, dict) else {}


def replace_file(path, text):
    """Write text to path through a private temp file and a rename: readers never see half a file,
    the result is readable by its owner only, and no predictable temp name can be hijacked."""
    fd, tmp = tempfile.mkstemp(prefix=".elron-", suffix=".tmp", dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def save_config(data):
    path = config_path()
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    # Farecard numbers are personal: replace_file leaves the file readable by its owner only.
    replace_file(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def clean_card(card):
    card = card.strip().replace(" ", "")
    if not re.fullmatch(r"[A-Za-z0-9]+", card):
        sys.exit("error: a farecard number is letters and digits only.")
    return card


def card_label(card):
    """A farecard by its last four characters, so output doesn't spread the whole number."""
    return f"…{card[-4:]}" if len(card) > 4 else card


def shown(path):
    """A request path fit for an error message: a farecard number in it cut to its last four."""
    return re.sub(r"(/card/)([^/]+)", lambda m: m[1] + card_label(m[2]), path)


def request(method, path, body=None, not_found=None, soft=False):
    """JSON from the Ridango API. soft: None on any failure, for lookups an answer can do without."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        if soft or (not_found and e.code in (404, 409)):
            return None
        sys.exit(f"error: Ridango API returned HTTP {e.code} for {method} {shown(path)}")
    except (OSError, http.client.HTTPException) as e:  # URLError, and failures while reading the reply
        if soft:
            return None
        sys.exit(
            f"error: could not reach api.ridango.com ({getattr(e, 'reason', e)}). "
            "In a sandbox, allow the api.ridango.com domain in its network settings."
        )
    except ValueError:  # not JSON
        if soft:
            return None
        sys.exit(f"error: Ridango API sent an unreadable reply for {method} {shown(path)}")


def fold(text):
    """Lower-case and strip accents, so "Põlva" matches "polva"."""
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def fold_query(query):
    """A stop query folded for matching, with aliases resolved: "Riga" becomes "riia"."""
    return fold(ALIASES.get(fold(query), query))


def get_stops():
    stops = request("GET", "/intercity/originstops")
    if not isinstance(stops, list):
        sys.exit("error: Ridango API sent an unexpected stop list.")
    return stops


def find_stop(stops, query):
    q = fold_query(query)
    exact = [s for s in stops if fold(s["stop_name"]) == q]
    if exact:
        return exact[0]
    partial = [s for s in stops if q in fold(s["stop_name"])]
    if len(partial) == 1:
        return partial[0]
    if not partial:
        sys.exit(f'error: no stop matches "{query}". Run `stops` to list them.')
    names = ", ".join(s["stop_name"] for s in partial[:10])
    sys.exit(f'error: "{query}" matches several stops: {names}. Use the full name.')


def now():
    return datetime.now(TALLINN) if TALLINN else datetime.now().astimezone()


def parse_time(value):
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    if t.tzinfo is None:  # treat naive times as Tallinn local time
        t = t.replace(tzinfo=TALLINN) if TALLINN else t.astimezone()
    return t.astimezone(TALLINN) if TALLINN else t


def cmd_stops(args):
    stops = get_stops()
    if args.query:
        q = fold_query(args.query)
        stops = [s for s in stops if q in fold(s["stop_name"])]
    for s in stops:
        print(s["stop_name"])


def get_live():
    """Trains running right now, from the feed behind elron.ee's live map. None if unreachable."""
    req = urllib.request.Request(LIVE_URL, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            data = json.load(res)
    except (OSError, http.client.HTTPException, ValueError):  # URLError and timeouts are OSErrors
        return None
    rows = data.get("data") if isinstance(data, dict) else None
    return rows if isinstance(rows, list) else None


def delay_of(train):
    """A live train's delay in minutes (negative if early), or None when the feed gives none."""
    delay = str(train.get("erinevus_plaanist") or "").strip()
    return int(delay) if re.fullmatch(r"-?\d+", delay) else None


def matches(train, q):
    """Whether a live train's line or last stop contains the folded query q (None matches all)."""
    return not q or q in fold(f"{train.get('liin', '')} {train.get('viimane_peatus', '')}")


def live_status(train):
    """One phrase for a live train: "3 min late, last stop Tamsalu" etc."""
    parts = []
    n = delay_of(train)
    if n:
        parts.append(f"{n} min late" if n > 0 else f"{-n} min early")
    elif (train.get("reisi_staatus") or "").strip() == "plaaniline":
        parts.append("running to schedule")
    elif train.get("reisi_staatus"):
        parts.append(f"status: {train['reisi_staatus']}")  # Estonian, from Elron
    if train.get("viimane_peatus"):
        parts.append(f"last stop {train['viimane_peatus']}")
    for note in (train.get("pohjus_teade"), train.get("lisateade")):
        if note and str(note).strip():
            parts.append(f"note: {str(note).strip()}")
    return ", ".join(parts)


def train_numbers(leg):
    """A leg's train numbers. ext_trip_id is "14/114/871" for a train that changes number."""
    return set(str(leg.get("ext_trip_id") or "").split("/")) - {""}


def match_live(leg, live):
    """The live record for a Ridango leg: the feed's reis is one of the leg's train numbers."""
    found = [t for t in live if str(t.get("reis")) in train_numbers(leg)]
    return found[0] if len(found) == 1 else None


def fetch_journeys(kind, origin, destination, day, soft=False):
    path = "/intercity/stopareas/trips/" + kind  # "direct", or "transfer" for one change of train
    body = {
        "channel": "web",
        "date": day,
        "origin_stop_area_id": origin["stop_area_id"],
        "destination_stop_area_id": destination["stop_area_id"],
    }
    return request("PUT", path, body, soft=soft)


def messages(items):
    """Readable text from Ridango notices: English where given, else Estonian; one per notice id."""
    seen, out = set(), []
    for item in items or []:
        if isinstance(item, dict):
            key = item.get("id")
            text = item.get("message_en") or item.get("message_et") or ""
        else:
            key, text = None, str(item)
        text = " ".join(str(text).split())
        if text and (key is None or key not in seen) and text not in out:
            seen.add(key)
            out.append(text)
    return out


def stop_patterns(stops):
    """(stop, pattern) pairs for named_stops, built once per run."""
    return [(s, re.compile(r"(?<!\w)" + re.escape(fold(s["stop_name"])) + r"(?!\w)")) for s in stops]


def named_stops(text, patterns):
    """The stops a notice names, as whole words: "transfer at Tapa station" names Tapa."""
    folded = fold(text)
    return [stop for stop, pattern in patterns if pattern.search(folded)]


def calls_at(leg, stop, day, cache):
    """Whether this leg's train stops at `stop` between the leg's own ends, inclusive.

    The API lists no stops along a trip, so ask for the same train from the leg's start to that stop:
    it is on the leg only if it gets there no later than the leg ends.
    """
    if stop["stop_name"] in (leg.get("origin_stop_name"), leg.get("destination_stop_name")):
        return True
    start, end = leg.get("origin_stop_area_id"), parse_time(leg.get("arrival_time"))
    if not start or end is None:
        return True  # can't tell, so keep the notice
    key = (start, stop["stop_area_id"])
    if key not in cache:
        cache[key] = fetch_journeys("direct", {"stop_area_id": start}, stop, day, soft=True)
    if cache[key] is None:
        return True
    for journey in cache[key].get("journeys") or []:
        for other in journey.get("trips") or []:
            arrives = parse_time(other.get("arrival_time"))
            if (
                other.get("departure_time") == leg.get("departure_time")
                and train_numbers(other) & train_numbers(leg)
                and arrives
                and arrives <= end
            ):
                return True
    return False


def under_way(leg, train, current):
    """Whether a live train has still to reach the end of this leg, allowing for its delay."""
    if not train:
        return False
    last, end = str(train.get("viimane_peatus") or ""), str(leg.get("destination_stop_name") or "")
    if last and end and fold(last) == fold(end):
        return False  # the end of the leg was its last stop
    arrives = parse_time(leg.get("arrival_time"))
    return arrives is None or arrives + timedelta(minutes=max(delay_of(train) or 0, 0)) > current


def describe(journey, current, is_today, live, applies):
    """(state, text, leaves) for one journey of one or more legs, or (None, None, None) for an empty
    one. leaves is when it is expected to leave the user's stop, allowing for a live delay.

    state is "upcoming" (it can still be caught), "on its way" (it has left the user's stop but not
    reached their destination) or "departed". applies(leg, text) says whether a notice concerns the
    user's part of that leg's route.
    """
    legs = [leg for leg in journey.get("trips") or [] if leg]
    if not legs:
        return None, None, None
    dep, arr = parse_time(legs[0].get("departure_time")), parse_time(legs[-1].get("arrival_time"))
    if dep is None:  # never drop a train silently: show it raw instead
        return "upcoming", f"  ?     {legs[0].get('departure_time')!r} (unparseable time)", None
    # Match live trains before judging what has happened: a late train can still be caught after its
    # timetabled departure, and is still on its way after its timetabled arrival.
    running = [match_live(leg, live) if live and is_today else None for leg in legs]
    state = "upcoming"
    leaves = dep + timedelta(minutes=max(delay_of(running[0]) or 0, 0)) if running[0] else dep
    if is_today:
        if leaves <= current:
            moving = any(under_way(leg, train, current) for leg, train in zip(legs, running))
            state = "on its way" if moving else "departed"
    line = f"  {dep:%H:%M} → {arr:%H:%M}" if arr else f"  {dep:%H:%M}"
    if arr:
        minutes = int((arr - dep).total_seconds() // 60)
        line += f"  ({minutes // 60}h{minutes % 60:02d})" if minutes >= 60 else f"  ({minutes} min)"
    tags = []
    if len(legs) > 1:
        for a, b in zip(legs, legs[1:]):
            at, leave = parse_time(a.get("arrival_time")), parse_time(b.get("departure_time"))
            when = f" {at:%H:%M}→{leave:%H:%M}" if at and leave else ""
            tags.append(f"change at {a.get('destination_stop_name')}{when}")
    if state == "departed":
        tags.append("departed")
    if any(leg.get("fast_train") for leg in legs):
        tags.append("express")
    prices = [(leg.get("product") or {}).get("price") for leg in legs]
    if prices and all(isinstance(p, (int, float)) for p in prices):
        # Euros, not cents (unlike the farecard balance): a Tallinn-Tartu ticket reads 12.9.
        tags.append(f"€{sum(prices):.2f}")
    if all(str(leg.get("bikes_allowed")) == "1" for leg in legs):
        tags.append("bikes ok")
    for leg, train in zip(legs, running):
        tags.extend(f"notice: {text}" for text in messages(leg.get("trip_messages")) if applies(leg, text))
        # Only until the train reaches the end of the leg: past the user's stop it runs on elsewhere.
        if under_way(leg, train, current):
            prefix = "live" if len(legs) == 1 else f"live ({leg.get('origin_stop_name')} leg)"
            tags.append(f"{prefix}: {live_status(train)}")
    if tags:
        line += "  [" + "; ".join(tags) + "]"
    return state, line, leaves


def cmd_trips(args):
    if len(args.stops) == 2:
        origin_name, destination_name = args.stops
    elif len(args.stops) == 1:
        origin_name, destination_name = load_config().get("home"), args.stops[0]
        if not origin_name:
            sys.exit(
                "error: no home station saved. Ask the user where they usually travel from, "
                "then save it with `config --home STOP` (or pass both FROM and TO)."
            )
    else:
        sys.exit("error: trips takes [FROM] TO.")
    stops = get_stops()
    origin = find_stop(stops, origin_name)
    destination = find_stop(stops, destination_name)
    current = now()
    day = args.date or current.date().isoformat()
    is_today = day == current.date().isoformat()
    live = get_live() if is_today else None

    print(f"{origin['stop_name']} → {destination['stop_name']}, {day} (Europe/Tallinn time)")
    if is_today and live is None:
        print("(live running data unavailable: elron.ee could not be reached)")

    # Notices travel with the whole train ("transfer at Tapa" on a Tartu-Tallinn train): show one only
    # if it names no stop, or names a stop on the user's part of the route.
    patterns, called = stop_patterns(stops), {}

    def applies(leg, text):
        named = named_stops(text, patterns)
        return not named or any(calls_at(leg, stop, day, called) for stop in named)

    on_its_way, disruptions = [], []

    def section(title, data):
        """Print one section of journeys; return how many can still be caught."""
        data = data if isinstance(data, dict) else {}
        rows, upcoming, departed, moving = [], 0, 0, 0
        for journey in data.get("journeys") or []:
            state, text, leaves = describe(journey, current, is_today, live, applies)
            if text is None:
                continue
            if state == "on its way":  # listed apart, so the first row is always one the user can catch
                on_its_way.append(text)
                moving += 1
            elif state == "departed" and not args.all:
                departed += 1
            else:
                rows.append((leaves, text))
                upcoming += state == "upcoming"
        disruptions.extend(data.get("disruption_messages") or [])
        print(f"{title}:")
        # In the order they will actually leave: a train running an hour late goes after the on-time
        # one timetabled half an hour behind it, so the first row is still the next to catch.
        rows = [text for _, text in sorted(rows, key=lambda r: (r[0] is not None, r[0]))]
        print("\n".join(rows) if rows else "  None" + (" left today." if departed or moving else "."))
        if departed:
            print(f"  ({departed} earlier train{'s' if departed != 1 else ''} already departed; pass --all to list them)")
        return upcoming

    upcoming_direct = section("Direct", fetch_journeys("direct", origin, destination, day))
    # One change of train: always on request, and automatically when no direct train can still be caught.
    if args.connections or not upcoming_direct:
        transfers = fetch_journeys("transfer", origin, destination, day, soft=True)
        if transfers is None:
            print("With one change:\n  (could not be loaded from api.ridango.com)")
        else:
            section("With one change", transfers)
    if on_its_way:
        print("Already on the way:")
        print("\n".join(on_its_way))
    if upcoming_direct and not args.connections:
        print("(pass --connections to also list journeys with a change of train)")
    for text in messages(disruptions):
        print(f"Disruption: {text}")


# Trains through a station, whether or not they stop: the live feed's position and speed, placed on
# the track network in TRACKS (at the end of this file). The feed names a train's line but not its
# route, so the route is the track between the first and last stops its line names.
STOP_ID_PREFIX = "64-11632-"  # every Elron stop_area_id; TRACKS keeps only the part after it
PASSING_AHEAD = 60  # minutes: how far ahead to look
PASSING_BEHIND = 15  # minutes: how far back "just went through" reaches
OFF_TRACK_KM = 3  # a train further than this from its route can't be placed on it


def tracks():
    """({stop_area_id: (lon, lat)}, {stop_area_id: {neighbouring stop_area_ids}}) from TRACKS."""
    where, links = {}, {}
    for run in TRACKS.strip().split("\n"):
        ids = []
        for point in run.split("|"):
            number, position = point.split()
            lon, lat = position.split(",")
            ids.append(STOP_ID_PREFIX + number)
            where[ids[-1]] = (float(lon), float(lat))
        for a, b in zip(ids, ids[1:]):
            links.setdefault(a, set()).add(b)
            links.setdefault(b, set()).add(a)
    return where, links


def track_path(links, start, end):
    """The stop ids from start to end along the track, or None if the track doesn't join them."""
    previous, queue = {start: None}, [start]
    for here in queue:
        for nxt in links.get(here, ()):
            if nxt not in previous:
                previous[nxt] = here
                queue.append(nxt)
    if end not in previous:
        return None
    path = [end]
    while path[-1] != start:
        path.append(previous[path[-1]])
    return path[::-1]


def locate(path, where, lon, lat):
    """(km along the path, km off it) for a position, through straight lines between stations."""
    best, along = None, 0.0
    k = math.cos(math.radians(lat)) * 111.2  # km per degree of longitude here; latitude is 111.2
    for a, b in zip(path, path[1:]):
        ax, ay = (where[a][0] - lon) * k, (where[a][1] - lat) * 111.2
        dx, dy = (where[b][0] - where[a][0]) * k, (where[b][1] - where[a][1]) * 111.2
        length = math.hypot(dx, dy)
        t = 0.0 if not length else min(1.0, max(0.0, -(ax * dx + ay * dy) / length**2))
        off = math.hypot(ax + t * dx, ay + t * dy)
        if best is None or off < best[1]:
            best = (along + t * length, off)
        along += length
    return best


def km_to(path, where, stop):
    """km along the path from its start to one of its stops."""
    total = 0.0
    for a, b in zip(path, path[1:]):
        if a == stop:
            break
        (x1, y1), (x2, y2) = where[a], where[b]
        total += math.hypot((x2 - x1) * math.cos(math.radians((y1 + y2) / 2)) * 111.2, (y2 - y1) * 111.2)
    return total


def stops_at(train, station, start, end, day, cache):
    """True or False for whether a live train calls at station, None if the timetable can't say.

    A train counts as not stopping only if the timetable knows it between its line's ends but not
    between the station and its last stop, so an unlisted train is never called non-stopping."""
    if station["stop_area_id"] in (start["stop_area_id"], end["stop_area_id"]):
        return True
    number = str(train.get("reis"))

    def runs(origin, destination):
        key = (origin["stop_area_id"], destination["stop_area_id"])
        if key not in cache:
            cache[key] = fetch_journeys("direct", origin, destination, day, soft=True)
        if not isinstance(cache[key], dict):
            return None  # the lookup failed: unknown
        return any(
            number in train_numbers(leg)
            for journey in cache[key].get("journeys") or []
            for leg in journey.get("trips") or []
        )

    onward = runs(station, end)
    if onward is not False:
        return onward
    return False if runs(start, end) else None


def parse_clock(value, current):
    """Today's datetime for an "HH:MM" from the feed, or None."""
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", str(value or "").strip())
    if not match or int(match[1]) > 23 or int(match[2]) > 59:
        return None
    return current.replace(hour=int(match[1]), minute=int(match[2]), second=0, microsecond=0)


def cmd_passing(args):
    stops = get_stops()
    station = find_stop(stops, args.station)
    where, links = tracks()
    if station["stop_area_id"] not in where:
        sys.exit(f"error: there is no track data for {station['stop_name']}, so trains through it can't be placed.")
    live = get_live()
    if live is None:
        sys.exit("error: could not reach elron.ee. In a sandbox, allow the elron.ee domain in its network settings.")
    current = now()
    day = current.date().isoformat()
    by_id = {s["stop_area_id"]: s for s in stops}
    patterns, cache, rows = stop_patterns(stops), {}, []
    for t in live:
        # Earliest-named stop first, the longest name winning where two start at the same place.
        found = sorted(
            ((m.start(), -len(m.group()), stop) for stop, pattern in patterns for m in pattern.finditer(fold(str(t.get("liin") or "")))),
            key=lambda f: f[:2],
        )
        if len(found) < 2:
            continue
        start, end = found[0][2], found[-1][2]
        path = track_path(links, start["stop_area_id"], end["stop_area_id"])
        if not path or station["stop_area_id"] not in path:
            continue
        try:
            lat, lon = float(t.get("latitude")), float(t.get("longitude"))
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(lat) and math.isfinite(lon)):
            continue
        along, off = locate(path, where, lon, lat)
        if off > OFF_TRACK_KM:
            continue
        ahead = km_to(path, where, station["stop_area_id"]) - along
        try:
            speed = float(t.get("kiirus"))
        except (TypeError, ValueError):
            speed = 0.0
        # A standing or crawling train says little about its pace: assume a typical 60 km/h.
        minutes = ahead / (speed if speed >= 30 else 60) * 60
        leaves = parse_clock(t.get("reisi_algus_aeg"), current)
        if along < 0.5 and leaves and leaves > current:  # still waiting at its first stop
            minutes += (leaves - current).total_seconds() / 60
        if not -PASSING_BEHIND <= minutes <= PASSING_AHEAD:
            continue
        rows.append((minutes, ahead, speed, t, stops_at(t, station, by_id.get(start["stop_area_id"], start), end, day, cache)))

    print(f"Trains through {station['stop_name']} (live positions; times are rough estimates):")
    here = [r for r in rows if abs(r[1]) < 0.3 and r[2] < 5]  # standing at the station
    coming = sorted((r for r in rows if r[1] > 0 and r not in here), key=lambda r: r[0])
    gone = sorted((r for r in rows if r[1] <= 0 and r not in here), key=lambda r: -r[0])
    for minutes, ahead, speed, t, stops in here + coming + gone:
        if (minutes, ahead, speed, t, stops) in here:
            when, calls, where_now = "at the station now", None, None
        elif ahead > 0:
            due = current + timedelta(minutes=minutes)
            when = f"in about {max(1, round(minutes))} min ({due:%H:%M})"
            calls = {True: "stops here", False: "doesn't stop here"}.get(stops)
            where_now = f"{ahead:.1f} km away"
        else:
            when = f"about {max(1, round(-minutes))} min ago"
            calls = {True: "stopped here", False: "went through without stopping"}.get(stops)
            where_now = f"{-ahead:.1f} km past"
        details = [x for x in (calls, where_now, f"{speed:.0f} km/h" if speed else None, live_status(t)) if x]
        print(f"  {when}: train {t.get('reis')} {t.get('liin')}; {'; '.join(details)}")
    if not rows:
        print(f"  None due in the next {PASSING_AHEAD} min or gone through in the last {PASSING_BEHIND}.")
    print("(Only trains already running are shown; `trips` lists the timetable's stopping trains.)")


# The default map is a self-contained SVG over an embedded outline: hosts that preview HTML in a
# sandbox (Claude's artifacts, for one) block every request a page makes, so it must make none, and
# its CSP enforces that.
# --tiles adds MapLibre over OpenFreeMap street tiles for a local browser, and falls back to the
# SVG wherever the library or its style can't load.
HOME_VIEW = (21.7, 57.45, 28.3, 59.75)  # west, south, east, north: Estonia, Valga to Narva
OUTLINE_BOX = (20.8, 55.6, 29.6, 60.6)  # the area OUTLINE covers, at the end of this file
PLACES = [
    ("Tallinn", 24.75, 59.44),
    ("Tapa", 25.96, 59.26),
    ("Tartu", 26.72, 58.38),
    ("Narva", 28.19, 59.38),
    ("Viljandi", 25.60, 58.36),
    ("Valga", 26.05, 57.78),
    ("Riga", 24.11, 56.95),
]
MAPLIBRE_JS = "https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/5.24.0/maplibre-gl.js"
NO_REQUESTS_CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'"
# The few rules from maplibre-gl.css this page needs, inlined: sandboxes block outside stylesheets.
MAPLIBRE_CSS = (
    ".maplibregl-map{overflow:hidden;position:relative;-webkit-tap-highlight-color:transparent}"
    ".maplibregl-canvas{left:0;position:absolute;top:0}"
    ".maplibregl-canvas-container.maplibregl-interactive{cursor:grab}"
    ".maplibregl-canvas-container.maplibregl-touch-zoom-rotate.maplibregl-touch-drag-pan,"
    ".maplibregl-canvas-container.maplibregl-touch-zoom-rotate.maplibregl-touch-drag-pan .maplibregl-canvas"
    "{touch-action:none}"
    ".maplibregl-boxzoom{background:#fff;border:2px dotted #202020;height:0;left:0;opacity:.5;position:absolute;"
    "top:0;width:0}"
)

MAP_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Elron trains</title>
__HEAD__<style>
  :root { color-scheme: light dark; --sea: #d7e6f1; --land: #ebe7de; --home: #fbfaf7; --edge: #a39c8a; --ink: #1d1d1f; --panel: #ffffffee; }
  @media (prefers-color-scheme: dark) {
    :root { --sea: #15212a; --land: #2b2b2d; --home: #3a3a3c; --edge: #5f5b55; --ink: #f2f2f2; --panel: #1f1f22ee; }
  }
  html, body { margin: 0; height: 100%; background: var(--sea); color: var(--ink); font: 14px/1.4 system-ui, sans-serif; }
  #svgmap, #tiles { position: absolute; inset: 0; width: 100%; height: 100%; }
  .sea { fill: var(--sea); }
  .land { fill: var(--land); stroke: var(--edge); stroke-width: 1; stroke-linejoin: round; }
  .home { fill: var(--home); }
  .place { fill: var(--ink); opacity: .6; font-size: 13px; }
  .train { stroke: #fff; stroke-width: 2; cursor: pointer; }
  .train:focus { outline: none; stroke: var(--ink); stroke-width: 3; }
  .ontime { fill: #2ca02c; } .late { fill: #ff7f0e; } .very-late { fill: #d62728; }
  @media (max-width: 600px) {
    .train { r: 14px; stroke-width: 3; }
    .place { font-size: 26px; }
  }
  .panel { position: absolute; z-index: 3; left: 12px; max-width: calc(100% - 48px); background: var(--panel); padding: 6px 10px; border-radius: 6px; box-shadow: 0 1px 4px #0003; }
  #note { top: 12px; }
  #info { bottom: 12px; }
  #info:empty, #credit[hidden] { display: none; }
  #credit { left: auto; right: 12px; bottom: 12px; font-size: 12px; }
  #credit a { color: inherit; }
__CSS__</style>
</head>
<body>
__SVG__
__TILES__<div class="panel" id="note"></div>
<div class="panel" id="info" role="status"></div>
<script>
const data = __DATA__;
const svg = document.getElementById("svgmap");
const info = document.getElementById("info");
document.getElementById("note").textContent = data.note;
// Feed text is untrusted: it only ever goes in as text, never as HTML.
function show(i) {
  info.replaceChildren(...data.trains[i].lines.map((line) => {
    const p = document.createElement("div");
    p.textContent = line;
    return p;
  }));
}
function picked(event) {
  const i = event.target.dataset ? event.target.dataset.i : undefined;
  return i === undefined ? null : Number(i);
}
svg.addEventListener("click", (event) => {
  const i = picked(event);
  if (i === null) info.replaceChildren();
  else show(i);
});
svg.addEventListener("keydown", (event) => {
  const i = picked(event);
  if (event.key === "Enter" && i !== null) show(i);
});
__TILESCRIPT__</script>
</body>
</html>
"""

TILES_DIV = """<div id="tiles"></div>
<div class="panel" id="credit" hidden>Map <a href="https://openfreemap.org">OpenFreeMap</a> © <a href="https://www.openmaptiles.org/">OpenMapTiles</a> Data from <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a></div>
"""

TILES_SCRIPT = """function useSvg() {
  const tiles = document.getElementById("tiles");
  if (tiles) tiles.remove();
  document.getElementById("credit").hidden = true;
  svg.style.display = "";
}
if (typeof maplibregl === "undefined") useSvg();
else {
  try {
    svg.style.display = "none";
    const [west, south, east, north] = data.bounds;
    const map = new maplibregl.Map({
      container: "tiles",
      style: "https://tiles.openfreemap.org/styles/liberty",
      bounds: [[west, south], [east, north]],
      attributionControl: false,
      // Under --watch the view lives in the URL, so each reload keeps the user's pan and zoom.
      hash: data.watch > 0,
    });
    let styled = false;
    map.on("error", () => {
      if (styled) return; // a missing tile later on is not worth losing the map over
      try { map.remove(); } catch (error) {}
      useSvg();
    });
    map.once("style.load", () => {
      styled = true;
      document.getElementById("credit").hidden = false;
      map.addSource("trains", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: data.trains.map((t, i) => ({
            type: "Feature",
            geometry: { type: "Point", coordinates: [t.lon, t.lat] },
            properties: { i, colour: t.colour },
          })),
        },
      });
      map.addLayer({
        id: "trains",
        type: "circle",
        source: "trains",
        paint: { "circle-radius": 7, "circle-color": ["get", "colour"], "circle-stroke-width": 2, "circle-stroke-color": "#fff" },
      });
      map.on("click", "trains", (event) => show(event.features[0].properties.i));
      map.on("mouseenter", "trains", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "trains", () => { map.getCanvas().style.cursor = ""; });
    });
  } catch (error) {
    useSvg();
  }
}
"""

COLOURS = {"ontime": "#2ca02c", "late": "#ff7f0e", "very-late": "#d62728"}


def outline():
    """The embedded country outlines: {"EST": [[(lon, lat), ...], ...], ...}."""
    shapes = {}
    for country in OUTLINE.split(";"):
        code, rings = country.split(":")
        shapes[code] = [
            [(int(x) / 100, int(y) / 100) for x, y in (point.split(",") for point in ring.split())]
            for ring in rings.split("|")
        ]
    return shapes


def map_points(trains):
    """Running trains with a usable position, ready for the page."""
    west, south, east, north = OUTLINE_BOX
    points = []
    for t in trains:
        try:
            lat, lon = float(t.get("latitude")), float(t.get("longitude"))
        except (TypeError, ValueError):
            continue
        # Drops NaN, infinities and the 0,0 a tracker can send, which would stretch the map.
        if not (west <= lon <= east and south <= lat <= north):
            continue
        delay = delay_of(t) or 0
        state = "very-late" if delay >= 5 else "late" if delay > 0 else "ontime"
        points.append(
            {
                "lat": lat,
                "lon": lon,
                "state": state,
                "colour": COLOURS[state],
                "label": f"{t.get('reis')} {t.get('liin')}",
                "lines": [
                    f"Train {t.get('reis')}: {t.get('liin')} ({t.get('reisi_algus_aeg')}–{t.get('reisi_lopp_aeg')})",
                    live_status(t),
                    f"{t.get('kiirus')} km/h, position as of {t.get('asukoha_uuendus')}",
                ],
            }
        )
    return points


def svg_map(points):
    """(svg, bounds): the trains as dots over the embedded outline, framing Estonia and every train."""
    west, south, east, north = HOME_VIEW
    for p in points:
        west, east = min(west, p["lon"] - 0.3), max(east, p["lon"] + 0.3)
        south, north = min(south, p["lat"] - 0.15), max(north, p["lat"] + 0.15)
    box_west, box_south, box_east, box_north = OUTLINE_BOX
    west, south = max(west, box_west), max(south, box_south)
    east, north = min(east, box_east), min(north, box_north)
    # Equirectangular, true to scale at the middle latitude: plenty at this size.
    k = math.cos(math.radians((south + north) / 2))
    scale = 1000 / ((east - west) * k)
    height = round((north - south) * scale)

    def x(lon):
        return f"{(lon - west) * k * scale:.1f}"

    def y(lat):
        return f"{(north - lat) * scale:.1f}"

    parts = [f'<rect class="sea" width="1000" height="{height}"/>']
    for code, rings in outline().items():
        d = "".join("M" + "L".join(f"{x(lon)},{y(lat)}" for lon, lat in ring) + "Z" for ring in rings)
        parts.append(f'<path class="land{" home" if code == "EST" else ""}" d="{d}"/>')
    for name, lon, lat in PLACES:
        if west < lon < east and south < lat < north:
            # Label to the left near the right edge, so Narva isn't cut off.
            side = 'text-anchor="end" dx="-9"' if lon > east - 0.8 else 'dx="9"'
            parts.append(f'<text class="place" x="{x(lon)}" y="{y(lat)}" {side} dy="4">{name}</text>')
    for i, p in enumerate(points):
        parts.append(
            f'<circle class="train {p["state"]}" cx="{x(p["lon"])}" cy="{y(p["lat"])}" r="7" tabindex="0" '
            f'data-i="{i}"><title>{html.escape(p["label"])}</title></circle>'
        )
    svg = (
        f'<svg id="svgmap" viewBox="0 0 1000 {height}" preserveAspectRatio="xMidYMid meet" role="group" '
        f'aria-label="Map of running Elron trains">{"".join(parts)}</svg>'
    )
    return svg, [round(v, 2) for v in (west, south, east, north)]


def write_map(trains, path, refresh=None, tiles=False):
    points = map_points(trains)
    svg, bounds = svg_map(points)
    updated = max((str(t.get("asukoha_uuendus") or "") for t in trains), default="") or now().strftime("%Y-%m-%d %H:%M")
    mode = f"updating every {refresh}s, last" if refresh else "snapshot as of"
    count, unplaced = len(points), len(trains) - len(points)
    note = f"{count} running Elron train{'s' if count != 1 else ''}"
    if unplaced:
        note += f" ({unplaced} more with no usable position)"
    note += f" · {mode} {updated} · green on time, orange late, red 5+ min late"
    data = {"trains": points, "note": note, "bounds": bounds, "watch": refresh or 0}
    head = f'<meta http-equiv="refresh" content="{int(refresh)}">\n' if refresh else ""
    if tiles:
        head += f'<script src="{MAPLIBRE_JS}"></script>\n'
    else:
        head = f'<meta http-equiv="Content-Security-Policy" content="{NO_REQUESTS_CSP}">\n' + head
    parts = {
        "HEAD": head,
        "CSS": f"  {MAPLIBRE_CSS}\n" if tiles else "",
        "SVG": svg,
        "TILES": TILES_DIV if tiles else "",
        # Escape "<" so feed text can never close the <script> block.
        "DATA": json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"),
        "TILESCRIPT": TILES_SCRIPT if tiles else "",
    }
    # One pass, so text from the feed is never itself searched for placeholders.
    page = re.sub(r"__(HEAD|CSS|SVG|TILES|DATA|TILESCRIPT)__", lambda m: parts[m.group(1)], MAP_TEMPLATE)
    try:
        replace_file(path, page)  # a page reloading mid-write never sees half a file
    except OSError as e:
        sys.exit(f"error: could not write the map to {path}: {e}")
    return count


def cmd_live(args):
    live = get_live()
    if live is None:
        sys.exit(
            "error: could not reach elron.ee. "
            "In a sandbox, allow the elron.ee domain in its network settings."
        )
    q = fold(args.query) if args.query else None
    trains = [t for t in live if matches(t, q)]
    if (args.watch or args.tiles) and not args.map:
        args.map = DEFAULT_MAP
    if not trains and not args.watch:  # under --watch, keep the map waiting for trains to start
        print("No running trains match." if q else "No trains are running right now.")
        return
    if args.map:
        count = write_map(trains, args.map, args.watch, args.tiles)
        # flush: run in the background, output goes to a log that would otherwise only fill on exit.
        print(f"Map of {count} running train{'s' if count != 1 else ''} written to {os.path.abspath(args.map)}", flush=True)
    if args.watch:
        print(f"Updating it every {args.watch}s until stopped (Ctrl+C); open it in a browser and it follows along.", flush=True)
        try:
            while True:
                time.sleep(args.watch)
                fresh = get_live()
                if fresh is not None:  # keep the last good map through a failed fetch
                    write_map([t for t in fresh if matches(t, q)], args.map, args.watch, args.tiles)
        except KeyboardInterrupt:
            return
        return
    for t in sorted(trains, key=lambda t: str(t.get("liin"))):
        speed = f", {t['kiirus']} km/h" if str(t.get("kiirus") or "").strip() else ""
        print(
            f"Train {t.get('reis')} {t.get('liin')} ({t.get('reisi_algus_aeg')}–{t.get('reisi_lopp_aeg')}): "
            f"{live_status(t)}{speed}; at {t.get('latitude')},{t.get('longitude')} as of {t.get('asukoha_uuendus')}"
        )


def cmd_balance(args):
    cards = [clean_card(args.card)] if args.card else load_config().get("cards") or []
    if not cards:
        sys.exit(
            "error: no farecards saved. Ask the user for their card number, "
            "then save it with `config --add-card N` (or pass it directly)."
        )
    for card in cards:
        data = request("GET", f"/tickets/web/cardtype/U/card/{card}/balance.json", not_found=True)
        if not isinstance(data, dict):
            print(f"Card {card_label(card)}: not recognised by Elron (check the number)")
            continue
        balance = data.get("balance")
        currency = data.get("currency") or "EUR"
        if not isinstance(balance, (int, float)):
            print(f"Card {card_label(card)}: the API returned no balance")
            continue
        # The balance is in cents (1250 is 12.50), unlike trip prices, which are euros.
        print(f"Card {card_label(card)}: {balance / 100:.2f} {currency}")


def cmd_config(args):
    data = {} if args.clear else load_config()
    changed = args.clear
    if args.home:
        data["home"] = find_stop(get_stops(), args.home)["stop_name"]  # store the canonical name
        changed = True
    cards = data.get("cards") or []
    for card in map(clean_card, args.add_card or []):
        if card not in cards:
            cards.append(card)
        changed = True
    for card in map(clean_card, args.remove_card or []):
        # The full number, or the last four characters `config` shows.
        found = [c for c in cards if c == card] or [c for c in cards if len(card) >= 4 and c.endswith(card)]
        if len(found) > 1:
            sys.exit(f"error: several saved cards end in {card}; give the full number.")
        if found:
            cards.remove(found[0])
        changed = True
    if cards:
        data["cards"] = cards
    else:
        data.pop("cards", None)
    if changed:
        save_config(data)
    print(f"Home station: {data.get('home') or '(not set)'}")
    print(f"Saved farecards: {', '.join(map(card_label, data.get('cards') or [])) or '(none)'}")
    print(f"Stored in {config_path()}")


def iso_date(text):
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a date like 2026-10-02") from None


def watch_seconds(text):
    try:
        seconds = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number of seconds") from None
    if seconds < 10:  # be kind to elron.ee, which every update asks again
        raise argparse.ArgumentTypeError("use 10 seconds or more")
    return seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("stops", help="list stops, optionally filtered by name")
    p.add_argument("query", nargs="?")
    p.set_defaults(func=cmd_stops)

    p = sub.add_parser("trips", help="trains between two stops, direct and with one change")
    p.add_argument("stops", nargs="+", metavar="STOP", help="[FROM] TO; FROM defaults to the saved home station")
    p.add_argument("--date", type=iso_date, help="YYYY-MM-DD, default today")
    p.add_argument("--all", action="store_true", help="include trains that have already departed")
    p.add_argument("--connections", action="store_true", help="also list journeys with one change of train")
    p.set_defaults(func=cmd_trips)

    p = sub.add_parser("live", help="trains running right now, with delays and positions")
    p.add_argument("query", nargs="?", help="filter by line or last stop, e.g. Tartu")
    p.add_argument(
        "--map",
        nargs="?",
        const=DEFAULT_MAP,
        metavar="PATH",
        help="also write an HTML map of the trains (default elron-live-map.html in the temp folder)",
    )
    p.add_argument(
        "--watch",
        nargs="?",
        type=watch_seconds,
        const=15,
        metavar="SECONDS",
        help="keep the map file updating (default every 15s, at least 10s) until stopped",
    )
    p.add_argument(
        "--tiles",
        action="store_true",
        help="draw the map over street tiles from the web, for a local browser (falls back to the plain map)",
    )
    p.set_defaults(func=cmd_live)

    p = sub.add_parser("passing", help="running trains due through a station, or just gone through, stopping or not")
    p.add_argument("station", metavar="STATION")
    p.set_defaults(func=cmd_passing)

    p = sub.add_parser("balance", help="Ühiskaart farecard balance")
    p.add_argument("card", nargs="?", help="default: every saved card")
    p.set_defaults(func=cmd_balance)

    p = sub.add_parser("config", help="show or change the saved home station and farecards")
    p.add_argument("--home", metavar="STOP", help="save the home station")
    p.add_argument("--add-card", metavar="N", action="append", help="save a farecard number")
    p.add_argument("--remove-card", metavar="N", action="append", help="forget a farecard, by number or last four")
    p.add_argument("--clear", action="store_true", help="forget everything saved")
    p.set_defaults(func=cmd_config)

    args = parser.parse_args()
    args.func(args)


# Natural Earth 1:10m country outlines (public domain), from the world-atlas 2.0.2 package,
# clipped to OUTLINE_BOX and simplified to 0.01°: points are "lon,lat" in hundredths of a degree,
# "|" separates rings and ";" countries. Embedded rather than fetched: see the map section.
OUTLINE = (
    "EST:2431,5787 2440,5802 2446,5807 2447,5816 2445,5820 2447,5825 2455,5829 2456,5831 2455,5833 "
    "2444,5839 2436,5840 2432,5838 2429,5832 2424,5828 2415,5828 2411,5824 2398,5832 2383,5835 "
    "2374,5834 2372,5840 2368,5844 2368,5852 2359,5855 2356,5858 2352,5856 2350,5856 2352,5860 "
    "2349,5867 2350,5870 2355,5871 2353,5875 2359,5874 2370,5875 2380,5873 2381,5875 2378,5877 "
    "2380,5878 2387,5877 2378,5880 2376,5878 2374,5880 2360,5880 2343,5876 2347,5880 2352,5882 "
    "2346,5886 2342,5891 2342,5893 2353,5896 2359,5895 2363,5898 2361,5903 2356,5905 2361,5901 "
    "2356,5899 2355,5897 2346,5899 2341,5902 2344,5902 2343,5906 2349,5909 2352,5907 2352,5912 "
    "2347,5921 2352,5923 2358,5923 2364,5926 2373,5923 2374,5925 2372,5926 2376,5928 2404,5929 "
    "2408,5927 2410,5929 2409,5931 2403,5936 2402,5938 2406,5940 2417,5935 2422,5936 2416,5940 "
    "2431,5942 2433,5947 2442,5948 2450,5944 2455,5946 2464,5944 2466,5944 2462,5947 2466,5947 "
    "2467,5949 2469,5950 2474,5945 2477,5945 2482,5949 2478,5952 2477,5956 2480,5957 2494,5951 "
    "2501,5952 2510,5950 2512,5950 2511,5953 2514,5954 2541,5949 2541,5953 2554,5953 2550,5957 "
    "2549,5967 2562,5958 2568,5957 2571,5957 2572,5959 2568,5963 2569,5965 2567,5966 2570,5967 "
    "2578,5964 2579,5959 2582,5958 2586,5959 2588,5963 2594,5960 2597,5960 2597,5962 2599,5963 "
    "2604,5962 2609,5959 2628,5959 2650,5954 2658,5956 2666,5955 2683,5948 2694,5945 2741,5945 "
    "2787,5941 2795,5943 2802,5948 2819,5937 2818,5936 2816,5936 2811,5935 2800,5933 2810,5932 "
    "2807,5931 2796,5931 2788,5928 2789,5926 2784,5916 2771,5899 2748,5888 2741,5875 2756,5839 "
    "2750,5832 2748,5827 2750,5822 2763,5809 2763,5800 2767,5799 2768,5797 2766,5792 2778,5789 "
    "2780,5786 2770,5782 2752,5781 2755,5780 2750,5777 2751,5771 2738,5767 2738,5760 2733,5758 "
    "2735,5753 2732,5752 2708,5755 2698,5761 2687,5763 2680,5757 2670,5757 2661,5754 2659,5752 "
    "2654,5753 2650,5752 2643,5756 2630,5760 2617,5770 2603,5777 2602,5784 2579,5786 2577,5787 "
    "2573,5792 2563,5791 2558,5792 2554,5796 2546,5798 2540,5802 2532,5804 2528,5807 2525,5807 "
    "2525,5805 2528,5801 2523,5798 2520,5799 2517,5806 2509,5807 2495,5801 2487,5800 2482,5798 "
    "2473,5799 2468,5795 2453,5795 2444,5791 2438,5786|2394,5811 2394,5814 2396,5815 2401,5815 "
    "2402,5813 2400,5811 2397,5810|2323,5850 2332,5847 2333,5846 2333,5844 2326,5847 2324,5846 "
    "2328,5844 2324,5844 2316,5848 2313,5844 2309,5843 2309,5839 2304,5837 2302,5836 2296,5838 "
    "2295,5837 2297,5836 2290,5831 2281,5827 2272,5827 2271,5826 2276,5824 2272,5823 2267,5822 "
    "2265,5824 2262,5825 2256,5823 2253,5825 2251,5822 2248,5824 2232,5821 2227,5817 2226,5809 "
    "2220,5803 2220,5799 2205,5792 2202,5791 2196,5798 2200,5798 2208,5808 2215,5808 2216,5812 "
    "2220,5815 2207,5818 2202,5823 2190,5825 2184,5829 2185,5831 2191,5830 2187,5834 2189,5835 "
    "2194,5832 2197,5835 2201,5835 2195,5843 2183,5851 2190,5850 2193,5852 2199,5851 2209,5842 "
    "2210,5849 2219,5854 2221,5855 2223,5851 2227,5850 2229,5857 2232,5858 2246,5859 2255,5863 "
    "2258,5863 2265,5859 2268,5860 2274,5859 2281,5862 2292,5862 2309,5857 2313,5853|2338,5858 "
    "2340,5856 2336,5853 2328,5855 2322,5854 2306,5860 2306,5862 2312,5863 2315,5868 2320,5868 "
    "2333,5865 2334,5864 2335,5861|2336,5903 2339,5901 2338,5898 2330,5897 2322,5898 2316,5897 "
    "2311,5902 2317,5905 2334,5904|2229,5889 2220,5889 2206,5893 2204,5894 2206,5895 2246,5897 "
    "2244,5898 2249,5898 2249,5902 2256,5904 2259,5909 2267,5909 2271,5907 2269,5904 2274,5900 "
    "2284,5901 2293,5898 2295,5896 2295,5894 2302,5889 2304,5884 2302,5883 2296,5885 2294,5883 "
    "2288,5883 2287,5882 2288,5882 2289,5879 2284,5878 2279,5878 2278,5879 2283,5882 2278,5882 "
    "2274,5881 2265,5870 2256,5869 2246,5872 2250,5874 2245,5879 2243,5885 2238,5888;LVA:2735,5753 "
    "2753,5753 2751,5743 2764,5739 2784,5729 2784,5721 2782,5716 2768,5710 2774,5707 2775,5704 "
    "2771,5696 2763,5684 2766,5684 2779,5687 2783,5687 2791,5682 2792,5681 2787,5674 2798,5669 "
    "2801,5659 2813,5655 2813,5654 2809,5650 2816,5644 2817,5637 2822,5627 2815,5614 2811,5616 "
    "2794,5611 2788,5606 2778,5602 2774,5596 2765,5592 2759,5579 2744,5580 2735,5583 2726,5579 "
    "2715,5583 2698,5583 2690,5578 2684,5572 2674,5568 2664,5569 2660,5567 2648,5568 2628,5574 "
    "2618,5585 2570,5609 2566,5614 2535,5616 2511,5618 2507,5620 2503,5626 2497,5630 2491,5642 "
    "2487,5644 2485,5640 2481,5641 2468,5638 2454,5629 2448,5627 2441,5627 2432,5630 2414,5626 "
    "2398,5631 2386,5633 2373,5633 2371,5636 2361,5635 2352,5633 2329,5637 2317,5636 2311,5631 "
    "2306,5630 2302,5632 2296,5640 2292,5641 2267,5635 2261,5638 2251,5640 2221,5639 2210,5642 "
    "2168,5631 2159,5631 2142,5624 2133,5623 2123,5616 2119,5608 2115,5608 2105,5607 2103,5615 "
    "2097,5623 2098,5631 2097,5637 2100,5643 2100,5651 2101,5652 2103,5651 2104,5646 2103,5645 "
    "2104,5644 2103,5641 2106,5639 2108,5640 2106,5650 2099,5655 2106,5669 2107,5677 2105,5683 "
    "2122,5691 2138,5701 2141,5707 2140,5715 2141,5718 2141,5727 2143,5731 2148,5733 2152,5739 "
    "2173,5757 2200,5760 2248,5774 2261,5775 2259,5765 2266,5759 2303,5740 2313,5737 2322,5721 "
    "2326,5710 2334,5706 2351,5703 2358,5698 2369,5697 2395,5701 2404,5707 2421,5712 2438,5723 "
    "2440,5726 2441,5734 2438,5751 2436,5755 2437,5761 2436,5769 2430,5774 2429,5784 2431,5787 "
    "2440,5787 2443,5790 2453,5795 2468,5795 2473,5799 2482,5798 2487,5800 2495,5801 2507,5806 "
    "2517,5806 2520,5799 2523,5798 2528,5801 2525,5805 2525,5807 2528,5807 2532,5804 2540,5802 "
    "2546,5798 2554,5796 2558,5792 2563,5791 2573,5792 2577,5787 2579,5786 2602,5784 2603,5777 "
    "2617,5770 2630,5760 2643,5756 2650,5752 2654,5753 2659,5752 2661,5754 2670,5757 2680,5757 "
    "2687,5763 2698,5761 2708,5755 2732,5752;LTU:2660,5567 2661,5560 2119,5560 2114,5569 2107,5575 "
    "2104,5592 2106,5595 2105,5607 2119,5608 2123,5616 2129,5621 2136,5623 2142,5624 2159,5631 "
    "2168,5631 2210,5642 2221,5639 2251,5640 2261,5638 2267,5635 2292,5641 2296,5640 2302,5632 "
    "2306,5630 2311,5631 2317,5636 2329,5637 2352,5633 2361,5635 2371,5636 2373,5633 2386,5633 "
    "2398,5631 2414,5626 2432,5630 2441,5627 2448,5627 2454,5629 2468,5638 2481,5641 2485,5640 "
    "2487,5644 2491,5642 2497,5630 2503,5626 2507,5620 2511,5618 2535,5616 2566,5614 2570,5609 "
    "2618,5585 2628,5574 2648,5568|2110,5560 2108,5572 2112,5570 2113,5566 2113,5560;RUS:2960,6060 "
    "2960,5574 2948,5568 2936,5575 2934,5579 2939,5588 2944,5591 2940,5595 2922,5598 2914,5601 "
    "2903,5602 2886,5598 2883,5596 2883,5594 2881,5593 2870,5596 2867,5604 2861,5609 2854,5610 "
    "2839,5609 2831,5604 2817,5613 2815,5614 2822,5627 2817,5637 2816,5644 2809,5650 2813,5654 "
    "2813,5655 2801,5659 2798,5669 2787,5674 2792,5681 2791,5682 2783,5687 2779,5687 2766,5684 "
    "2763,5684 2771,5696 2775,5704 2774,5707 2768,5710 2782,5716 2784,5721 2784,5729 2764,5739 "
    "2751,5743 2753,5753 2735,5753 2733,5758 2738,5760 2738,5766 2739,5768 2751,5771 2750,5777 "
    "2755,5780 2752,5781 2770,5782 2780,5786 2778,5789 2766,5792 2768,5797 2767,5799 2763,5800 "
    "2763,5809 2750,5822 2748,5827 2750,5832 2756,5839 2741,5875 2748,5888 2771,5899 2784,5916 "
    "2789,5926 2788,5928 2796,5931 2807,5931 2810,5932 2800,5933 2811,5935 2816,5936 2818,5936 "
    "2819,5937 2814,5940 2810,5944 2802,5948 2806,5953 2807,5958 2805,5962 2800,5968 2801,5976 "
    "2809,5980 2813,5979 2819,5976 2822,5969 2837,5967 2841,5968 2842,5971 2843,5981 2850,5986 "
    "2868,5981 2872,5979 2877,5980 2883,5979 2888,5982 2897,5983 2901,5986 2903,5990 2898,5993 "
    "2901,5993 2912,5999 2927,6000 2960,5996 2960,6020 2953,6020 2942,6017 2905,6018 2899,6022 "
    "2892,6028 2886,6029 2880,6037 2879,6034 2875,6034 2861,6039 2844,6056 2851,6056 2854,6051 "
    "2868,6046 2871,6048 2866,6053 2866,6060 2829,6060 2821,6055 2816,6055 2814,6053 2804,6053 "
    "2790,6053 2787,6054 2786,6057 2782,6053 2779,6053 2781,6055 2789,6060|2702,6004 2702,6002 "
    "2698,6002 2694,6009 2696,6010|2871,6029 2872,6029 2869,6026 2863,6027 2855,6030 2854,6035 "
    "2858,6035;FIN:2789,6060 2781,6055 2776,6058 2774,6057 2775,6056 2773,6054 2775,6052 2773,6051 "
    "2775,6051 2770,6049 2764,6049 2769,6052 2763,6052 2761,6050 2763,6047 2751,6051 2747,6051 "
    "2749,6049 2747,6048 2751,6046 2737,6050 2725,6051 2723,6053 2731,6053 2721,6056 2723,6058 "
    "2721,6059 2718,6057 2720,6052 2718,6051 2717,6053 2711,6055 2709,6053 2705,6055 2702,6054 "
    "2703,6052 2700,6049 2693,6049 2697,6046 2696,6045 2692,6048 2679,6046 2681,6049 2680,6049 "
    "2674,6047 2674,6044 2669,6042 2662,6045 2655,6043 2653,6044 2648,6049 2654,6052 2658,6059 "
    "2669,6060 2675,6057 2674,6060 2656,6060 2647,6051 2645,6048 2649,6044 2645,6042 2642,6041 "
    "2642,6040 2638,6042 2638,6040 2635,6039 2634,6038 2625,6045 2623,6044 2627,6040 2618,6041 "
    "2614,6040 2598,6048 2592,6049 2603,6043 2604,6041 2601,6040 2601,6039 2611,6034 2609,6031 "
    "2604,6030 2604,6032 2600,6036 2600,6037 2596,6036 2584,6040 2592,6036 2588,6031 2593,6025 "
    "2589,6025 2586,6028 2580,6029 2575,6032 2574,6031 2575,6030 2585,6027 2576,6024 2573,6025 "
    "2565,6030 2567,6033 2565,6034 2571,6034 2567,6036 2553,6033 2555,6031 2554,6028 2550,6025 "
    "2536,6025 2536,6026 2531,6027 2532,6025 2520,6025 2518,6022 2516,6023 2521,6021 2518,6020 "
    "2520,6019 2512,6018 2509,6018 2510,6019 2506,6018 2505,6017 2507,6016 2503,6015 2500,6016 "
    "2503,6020 2500,6021 2495,6014 2485,6014 2483,6016 2487,6016 2487,6018 2484,6019 2481,6019 "
    "2483,6016 2468,6013 2467,6010 2465,6010 2464,6013 2455,6016 2460,6013 2454,6009 2461,6010 "
    "2458,6007 2459,6006 2445,5999 2442,5999 2446,6005 2445,6005 2437,6000 2437,6002 2431,6000 "
    "2436,6004 2437,6007 2432,6008 2426,6004 2416,6004 2418,6003 2417,6002 2411,6003 2401,6001 "
    "2402,6004 2400,6004 2396,6000 2387,5999 2380,5996 2377,5997 2361,5996 2357,5998 2343,5996 "
    "2348,6001 2354,6003 2355,6007 2350,6006 2345,6003 2344,5999 2337,5995 2324,5990 2322,5987 "
    "2325,5984 2291,5981 2289,5981 2294,5985 2317,5989 2316,5992 2325,5992 2329,5996 2333,6003 "
    "2322,5993 2319,5995 2317,5994 2313,5994 2311,5992 2310,5994 2311,5997 2320,6000 2326,6004 "
    "2303,6004 2300,6006 2299,6008 2305,6012 2302,6014 2301,6011 2297,6009 2296,6012 2288,6015 "
    "2289,6017 2287,6018 2301,6028 2308,6036 2303,6034 2300,6031 2294,6032 2274,6024 2252,6021 "
    "2259,6023 2257,6024 2259,6026 2265,6028 2245,6025 2246,6027 2254,6032 2255,6033 2263,6038 "
    "2262,6040 2255,6037 2246,6038 2248,6040 2229,6038 2218,6043 2212,6044 2210,6046 2205,6044 "
    "2202,6046 2202,6047 2198,6048 2198,6049 2194,6049 2195,6052 2190,6053 2184,6052 2188,6048 "
    "2179,6048 2181,6057 2185,6059 2183,6060 2168,6058 2164,6050 2158,6049 2156,6049 2158,6051 "
    "2157,6053 2152,6057 2158,6057 2141,6058 2142,6060|2241,6005 2241,6009 2245,6007 2244,6000 "
    "2241,6001 2238,5999 2236,6002 2235,6008 2238,6008 2239,6005|2150,6014 2157,6017 2166,6016 "
    "2161,6013 2164,6012 2161,6010 2152,6010 2148,6012 2156,6012|2174,6019 2185,6020 2189,6018 "
    "2185,6017 2187,6016 2179,6016 2183,6015 2180,6014 2181,6014 2172,6011 2170,6012 2172,6015 "
    "2171,6017|2135,6021 2137,6020 2145,6018 2141,6018 2138,6016 2127,6019 2131,6021|2206,6021 "
    "2207,6020 2201,6017 2204,6016 2201,6014 2195,6015 2194,6018|2221,6021 2225,6024 2229,6025 "
    "2230,6022 2227,6020 2223,6018|2562,6024 2557,6026 2558,6030 2568,6025 2564,6023 2564,6021 "
    "2560,6022|2284,6024 2292,6030 2296,6029 2295,6027 2283,6019 2284,6017 2282,6016 2284,6016 "
    "2285,6011 2273,6005 2276,6003 2273,6000 2268,6000 2265,6003 2260,5998 2260,6001 2258,6000 "
    "2257,6002 2259,6005 2253,6001 2247,6000 2248,6008 2242,6012 2260,6014 2242,6015 2245,6022 "
    "2248,6023 2245,6019 2247,6018 2282,6023|2211,6031 2225,6031 2234,6029 2233,6027 2221,6025 "
    "2220,6025 2222,6027 2218,6028 2214,6028 2218,6028 2216,6026 2208,6027 2208,6030|2239,6032 "
    "2231,6032 2235,6035 2240,6036 2240,6034 2248,6032 2239,6029 2237,6029|2200,6033 2190,6033 "
    "2190,6034 2179,6037 2179,6040 2185,6041 2180,6044 2181,6047 2183,6047 2193,6042 2195,6040 "
    "2189,6040 2194,6037 2199,6037 2200,6036 2196,6035|2139,6056 2148,6053 2146,6053 2146,6049 "
    "2143,6049 2144,6047 2139,6049 2136,6053 2133,6053 2134,6056;BLR:2661,5560 2660,5567 2662,5569 "
    "2674,5568 2682,5571 2690,5578 2698,5583 2715,5583 2726,5579 2735,5583 2744,5580 2759,5579 "
    "2765,5592 2774,5596 2778,5602 2788,5606 2793,5611 2811,5616 2831,5604 2839,5609 2854,5610 "
    "2861,5609 2867,5604 2870,5596 2873,5595 2883,5594 2883,5596 2886,5598 2903,5602 2914,5601 "
    "2922,5598 2938,5595 2944,5591 2939,5588 2934,5579 2935,5577 2948,5568 2960,5574 2960,5560"
)

# Elron's track network for `passing`: runs of stations in track order, "ID lon,lat" separated by
# "|", one run per line, junctions at the ends of runs; ID is a stop_area_id after STOP_ID_PREFIX.
# Derived from the stop patterns of every Elron route in the national timetable (api.peatus.ee):
# see references/maintenance.md to redraw it.
TRACKS = (
    "114 25.5741,58.3579|89 25.5370,58.4878|60 25.5466,58.5453"
    "|115 25.5617,58.6296|59 25.5409,58.6659|38 25.5180,58.7252"
    "|92 25.4726,58.7712|100 25.4221,58.8051|40 25.1439,58.8341"
    "|47 25.0066,58.8679|18 24.8984,58.9430|78 24.8321,58.9944"
    "|5 24.8127,59.0657|50 24.7872,59.1154|33 24.7435,59.1712"
    "|113 24.7131,59.2014|82 24.6957,59.2215|24 24.6857,59.2390"
    "|17 24.6768,59.2736|85 24.6770,59.3014|53 24.7017,59.3389"
    "|104 24.7204,59.3756|48 24.7235,59.3880|94 24.7462,59.4131"
    "|93 24.7372,59.4402\n"
    "119 24.2407,59.0762|81 24.3122,59.1196|9 24.3175,59.1580"
    "|44 24.3149,59.1952|22 24.2934,59.2147|109 24.2994,59.2386"
    "|37 24.3544,59.2863|21 24.4172,59.3061\n"
    "120 27.4675,57.8400|35 27.5753,57.8369|61 27.4734,57.9198"
    "|8 27.4107,57.9679|111 27.3536,58.0061|84 27.2734,58.0424"
    "|7 27.1953,58.0548|71 27.0912,58.0700|91 27.0285,58.1013"
    "|23 26.9939,58.1289|106 26.9674,58.1481|110 26.9323,58.1736"
    "|79 26.8096,58.2384|108 26.7840,58.2550|80 26.7713,58.2716"
    "|101 26.7289,58.2891|118 26.7214,58.3100|26 26.7152,58.3574"
    "|97 26.7061,58.3738\n"
    "136 24.1201,56.9465|135 24.1561,56.9651|130 24.8555,57.1532"
    "|125 25.2833,57.3140|123 25.4412,57.5229|105 26.0533,57.7745"
    "|86 26.1892,57.8641|19 26.2394,57.9471|52 26.2313,58.0110"
    "|69 26.2400,58.0553|65 26.3258,58.1271|4 26.4230,58.2256"
    "|68 26.4487,58.2372|99 26.4819,58.2603|58 26.5373,58.2816"
    "|83 26.6292,58.3150|1 26.7149,58.3579|97 26.7061,58.3738\n"
    "21 24.4172,59.3061|107 24.4835,59.3114|87 24.5488,59.3251"
    "|63 24.5928,59.3379|102 24.6126,59.3436|41 24.6279,59.3550"
    "|72 24.6419,59.3696|28 24.6561,59.3768|6 24.6712,59.3832"
    "|57 24.6863,59.3860|75 24.7023,59.3885|13 24.7252,59.4012"
    "|98 24.7337,59.4111|49 24.7284,59.4246|93 24.7372,59.4402\n"
    "21 24.4172,59.3061|56 24.3203,59.3141|30 24.2590,59.3203\n"
    "30 24.2590,59.3203|31 24.2172,59.3246|70 24.1742,59.3291"
    "|45 24.1345,59.3332|64 24.0609,59.3441\n"
    "30 24.2590,59.3203|32 24.2459,59.3438\n"
    "54 28.1981,59.3688|103 27.7676,59.3729|62 27.5756,59.3746"
    "|11 27.4054,59.3556|34 27.1896,59.3618|73 27.0488,59.3585"
    "|29 26.9660,59.3531|88 26.8430,59.3495|15 26.6751,59.3449"
    "|77 26.3658,59.3578|16 26.1454,59.3380|96 25.9612,59.2655\n"
    "93 24.7372,59.4402|27 24.7387,59.4204|117 24.7958,59.4233"
    "|112 24.8192,59.4231|42 24.9317,59.3998|36 25.0042,59.3835"
    "|3 25.0805,59.3720|74 25.1738,59.3657|66 25.2673,59.3568"
    "|20 25.3352,59.3368|43 25.4109,59.3143|51 25.4651,59.2982"
    "|2 25.6131,59.2852|55 25.6525,59.2705|12 25.7071,59.2549"
    "|46 25.8231,59.2542|96 25.9612,59.2655\n"
    "96 25.9612,59.2655|95 26.1119,59.1598|25 26.1766,59.0878"
    "|76 26.2428,58.9903|116 26.2789,58.9087|67 26.3454,58.8269"
    "|10 26.3996,58.7479|14 26.5196,58.6626|90 26.5916,58.5517"
    "|39 26.6591,58.4579|97 26.7061,58.3738\n"
)


if __name__ == "__main__":
    main()
