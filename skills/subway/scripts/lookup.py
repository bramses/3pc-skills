#!/usr/bin/env python3
"""
Look up live NYC subway arrivals from the Transiter API (realtimerail.nyc),
which serves live MTA GTFS-realtime data as plain JSON.

Resolves a fuzzy station name (and optional line / direction / destination)
against the bundled station database in assets/nyc_stations.json, fetches
live stop-time data for that station's platforms, and prints a short,
ready-to-relay answer.

Usage:
  python3 lookup.py --station "14 st" [--line 1] [--direction uptown]
  python3 lookup.py --station "14 st" --destination "times sq"

Exit code 0 with a result, or 0 with a "no confident match" message and
candidate suggestions on stdout. Network/HTTP errors raise (non-zero exit).
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = "https://realtimerail.nyc/transiter/v0.6"
SYSTEM = "us-ny-subway"
STATIONS_PATH = Path(__file__).parent.parent / "assets" / "nyc_stations.json"

ABBREVIATIONS = {
    "square": "sq", "street": "st", "avenue": "av", "ave": "av", "boulevard": "blvd",
    "parkway": "pkwy", "expressway": "expwy", "heights": "hts",
    "place": "pl", "court": "ct", "highway": "hwy", "center": "ctr", "centre": "ctr",
}
SUFFIX_RE = re.compile(r"\s*\([^)]*\)\s*$")

# GTFS N/S direction codes aren't literal compass directions on every line,
# but this covers the common way people phrase it for the NYC system.
NORTH_WORDS = {"uptown", "north", "northbound", "bronx"}
SOUTH_WORDS = {"downtown", "south", "southbound", "brooklyn"}


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", s)
    s = re.sub(r"[^a-z0-9 ]", "", s).strip()
    words = [ABBREVIATIONS.get(w, w) for w in s.split()]
    return " ".join(words)


def base_name(name: str) -> str:
    return SUFFIX_RE.sub("", name)


def load_stations():
    return json.loads(STATIONS_PATH.read_text())


def find_candidates(stations, query: str, line: str | None):
    nq = normalize(query)
    exact = [s for s in stations if normalize(base_name(s["name"])) == nq]
    if exact:
        pool = exact
    else:
        substr = [s for s in stations if nq in normalize(base_name(s["name"]))]
        if substr:
            pool = substr
        else:
            base_names = list({base_name(s["name"]) for s in stations})
            close = difflib.get_close_matches(nq, [normalize(n) for n in base_names], n=5, cutoff=0.5)
            pool = [s for s in stations if normalize(base_name(s["name"])) in close]

    if line:
        line_upper = line.upper()
        narrowed = [s for s in pool if line_upper in s["lines"]]
        if narrowed:
            return narrowed
    return pool


def dedupe_by_name(entries):
    seen = {}
    for e in entries:
        seen.setdefault(e["name"], e)
    return list(seen.values())


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def to_epoch_seconds(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_arrivals(child_stop_id: str, valid_lines: set) -> list[dict]:
    url = (f"{BASE}/systems/{SYSTEM}/stops/{child_stop_id}"
           f"?skip_service_maps=true&skip_alerts=true&skip_transfers=true")
    data = fetch_json(url)
    now = __import__("time").time()
    out = []
    for st in data.get("stopTimes", []):
        if st.get("future") is False:
            continue
        route_id = (st.get("trip") or {}).get("route", {}).get("id")
        if valid_lines and route_id not in valid_lines:
            continue
        t = to_epoch_seconds((st.get("arrival") or {}).get("time")
                              or (st.get("departure") or {}).get("time"))
        if t is None:
            continue
        minutes = round((t - now) / 60)
        if minutes < 0:
            continue
        out.append({"line": route_id, "minutes": minutes})
    out.sort(key=lambda r: r["minutes"])
    return out


def format_minutes(m: int) -> str:
    return "Now" if m == 0 else f"{m} min"


def format_arrivals(station_name: str, by_direction: dict, line_filter=None):
    allowed = {ln.upper() for ln in line_filter} if line_filter else None
    lines_out = [f"**{station_name}**"]
    any_rows = False
    for direction_label, rows in by_direction.items():
        if allowed is not None:
            rows = [r for r in rows if r["line"] in allowed]
        if not rows:
            wanted = (", ".join(sorted(allowed)) + " ") if allowed else ""
            lines_out.append(f"  {direction_label}: no upcoming {wanted}trains listed right now")
            continue
        any_rows = True
        entries = ", ".join(f"[{r['line']}] {format_minutes(r['minutes'])}" for r in rows[:6])
        lines_out.append(f"  {direction_label}: {entries}")
    if not any_rows:
        lines_out.append("  (no live arrivals found)")
    return "\n".join(lines_out)


def pick_direction_ids(child_stop_ids: list[str], direction: str | None):
    """Returns dict of {label: child_stop_id} to query, filtered by requested direction if given."""
    labels = {}
    for cid in child_stop_ids:
        if cid.endswith("N"):
            labels["Northbound"] = cid
        elif cid.endswith("S"):
            labels["Southbound"] = cid
    if not direction:
        return labels
    nd = normalize(direction)
    words = set(nd.split())
    if words & NORTH_WORDS and "Northbound" in labels:
        return {"Northbound": labels["Northbound"]}
    if words & SOUTH_WORDS and "Southbound" in labels:
        return {"Southbound": labels["Southbound"]}
    return labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", required=True)
    ap.add_argument("--line")
    ap.add_argument("--direction")
    ap.add_argument("--destination")
    args = ap.parse_args()

    stations = load_stations()
    candidates = find_candidates(stations, args.station, args.line)
    unique = dedupe_by_name(candidates)

    if not unique:
        print(f"No station matched '{args.station}'. Try a different spelling or the official station name.")
        sys.exit(0)

    if len(unique) > 1:
        print(f"Multiple stations could match '{args.station}':")
        for s in unique[:8]:
            print(f"  - {s['name']} (lines: {', '.join(s['lines'])})")
        print("Ask the user which one they mean, or pass --line to disambiguate.")
        sys.exit(0)

    origin = unique[0]
    line_filter = [args.line] if args.line else None

    if args.destination:
        dest_pool = dedupe_by_name(find_candidates(stations, args.destination, None))
        if not dest_pool:
            print(f"Couldn't find a destination station matching '{args.destination}'.")
            sys.exit(0)

        origin_lines = {args.line.upper()} if args.line else set(origin["lines"])
        narrowed = [d for d in dest_pool if set(d["lines"]) & origin_lines]
        dest_candidates = narrowed if len(narrowed) == 1 else dest_pool

        if len(dest_candidates) > 1:
            print(f"Multiple stations could match destination '{args.destination}':")
            for s in dest_candidates[:8]:
                print(f"  - {s['name']} (lines: {', '.join(s['lines'])})")
            print("Ask the user which one they mean, or narrow with a line the destination is on.")
            sys.exit(0)

        dest = dest_candidates[0]
        shared = sorted(set(origin["lines"]) & set(dest["lines"]))
        if not shared:
            print(
                f"No single line connects {origin['name']} directly to {dest['name']} "
                f"(origin lines: {', '.join(origin['lines'])}; destination lines: {', '.join(dest['lines'])}). "
                f"A transfer is likely needed."
            )
            sys.exit(0)
        print(f"Direct line(s) from {origin['name']} to {dest['name']}: {', '.join(shared)}")
        line_filter = [args.line] if args.line else shared

    direction_ids = pick_direction_ids(origin["child_stop_ids"], args.direction)
    valid_lines = set(origin["lines"])
    by_direction = {}
    try:
        for label, cid in direction_ids.items():
            by_direction[label] = get_arrivals(cid, valid_lines)
    except Exception as e:
        print(f"Failed to fetch live data: {e}", file=sys.stderr)
        sys.exit(1)

    print(format_arrivals(origin["name"], by_direction, line_filter))


if __name__ == "__main__":
    main()
