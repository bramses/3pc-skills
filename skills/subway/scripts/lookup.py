#!/usr/bin/env python3
"""
Look up live NYC subway arrivals from aptransit.co.

Resolves a fuzzy station name (and optional line / direction / destination)
against the bundled station database in assets/nyc_stations.json, fetches
the live stop page, and prints a short, ready-to-relay answer.

Usage:
  python3 lookup.py --station "14 st" [--line 1] [--direction uptown]
  python3 lookup.py --station "14 st" --destination "times sq"

Exit code 0 with a result, or 0 with a "no confident match" message and
candidate suggestions on stdout — never raises for an ambiguous/unmatched
station, so the caller can read stdout either way. Network/HTTP errors do
raise (non-zero exit), since there's nothing useful to say in that case.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = "https://aptransit.co"
STATIONS_PATH = Path(__file__).parent.parent / "assets" / "nyc_stations.json"

ROW_RE = re.compile(
    r'<div class="ap-city-route-badge-24"[^>]*>([A-Z0-9]+)</div>\s*'
    r'<div class="ap-city-my-auto">\s*([^<]+?)\s*<br>\s*'
    r'<label[^>]*>([^<]*)</label>\s*</div>\s*'
    r'<div class="ap-city-dep-time"><span[^>]*>([^<]+)</span></div>',
    re.DOTALL,
)
DIR_HEADER_RE = re.compile(r'<h3 class="ap-city-h3-dir">([^<]+)</h3>', re.DOTALL)


def load_stations():
    return json.loads(STATIONS_PATH.read_text())


# MTA station names use these abbreviations consistently; users type the full
# word. Expanding the query (not the station names, which are already
# canonical) means "union square" matches "Union Sq" instead of losing to
# some unrelated "Union St" on string-similarity alone.
ABBREVIATIONS = {
    "square": "sq", "street": "st", "avenue": "av", "ave": "av", "boulevard": "blvd",
    "parkway": "pkwy", "expressway": "expwy", "heights": "hts",
    "place": "pl", "court": "ct", "highway": "hwy", "center": "ctr", "centre": "ctr",
}
SUFFIX_RE = re.compile(r"\s*\([^)]*\)\s*$")


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", s)  # "14th" -> "14", so it matches "14 St"
    s = re.sub(r"[^a-z0-9 ]", "", s).strip()
    words = [ABBREVIATIONS.get(w, w) for w in s.split()]
    return " ".join(words)


def base_name(name: str) -> str:
    """Strip the disambiguating '(A, B, C)' line-suffix so matching isn't skewed by it."""
    return SUFFIX_RE.sub("", name)


def find_candidates(stations, query: str, line: str | None):
    """Return station entries matching query, preferring ones served by `line` if given."""
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


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_stop_page(html: str):
    """Returns {direction_header: [{line, destination, status, time}, ...]}"""
    parts = DIR_HEADER_RE.split(html)
    # parts = [preamble, header1, body1, header2, body2, ...]
    sections = {}
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        rows = []
        for line, dest, status, time in ROW_RE.findall(body):
            rows.append({
                "line": line.strip(),
                "destination": dest.strip(),
                "status": status.strip() or "Good Service",
                "time": time.strip(),
            })
        sections[header] = rows
    return sections


def drop_nearby_transfer_noise(sections, valid_lines):
    """
    AP Transit's stop pages mix in arrivals for nearby-but-different stations
    as a rider convenience (e.g. Astor Pl's page shows 4-train times even
    though the 4 never stops at Astor Pl — it's the 4 at nearby Union Sq).
    Useful for a human glancing at a map, actively misleading for a script
    that states "[4] 4 min" as if it's a train reachable from where you're
    standing. Keep only rows whose line is one this specific station's own
    /train/{line} page confirmed it serves.
    """
    valid = {ln.upper() for ln in valid_lines}
    return {
        header: [r for r in rows if r["line"] in valid]
        for header, rows in sections.items()
    }


def filter_direction(sections, direction: str | None):
    if not direction:
        return sections
    nd = normalize(direction)
    matched = {h: rows for h, rows in sections.items() if nd in normalize(h)}
    return matched or sections


def format_arrivals(station_name: str, sections: dict, line_filter=None):
    """line_filter: None (show everything), or an iterable of line codes to keep."""
    allowed = {ln.upper() for ln in line_filter} if line_filter else None
    lines_out = [f"**{station_name}**"]
    any_rows = False
    for header, rows in sections.items():
        if allowed is not None:
            rows = [r for r in rows if r["line"] in allowed]
        if not rows:
            wanted = (", ".join(sorted(allowed)) + " ") if allowed else ""
            lines_out.append(f"  {header}: no upcoming {wanted}trains listed right now")
            continue
        any_rows = True
        entries = ", ".join(f"[{r['line']}] {r['time']}" for r in rows[:6])
        lines_out.append(f"  {header}: {entries}")
    if not any_rows:
        lines_out.append("  (no live arrivals found — line may have no service right now)")
    return "\n".join(lines_out)


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

        # Same-named-but-unrelated stations are common in NYC (see build_stations.py) —
        # if the plain name match is ambiguous, use the origin's own line(s) as evidence
        # to narrow it down before giving up and asking.
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
                f"A transfer is likely needed — tell the user to check the AP Transit map for a full route."
            )
            sys.exit(0)
        print(f"Direct line(s) from {origin['name']} to {dest['name']}: {', '.join(shared)}")
        line_filter = [args.line] if args.line else shared

    url = f"{BASE}/city/nyc/stop/{origin['id']}/{origin['slug']}"
    try:
        html = fetch(url)
    except Exception as e:
        print(f"Failed to fetch live data from {url}: {e}", file=sys.stderr)
        sys.exit(1)

    sections = parse_stop_page(html)
    sections = drop_nearby_transfer_noise(sections, origin["lines"])
    sections = filter_direction(sections, args.direction)
    print(format_arrivals(origin["name"], sections, line_filter))


if __name__ == "__main__":
    main()
