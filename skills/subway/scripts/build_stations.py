#!/usr/bin/env python3
"""
Build assets/nyc_stations.json by scraping every /city/nyc/train/{line} page
on aptransit.co and recording which stations each line stops at.

This is a one-time (or occasional re-run) build step, not something the
skill runs on every lookup. Re-run it if aptransit.co adds/removes lines or
stations, or if lookup.py starts reporting stale IDs (a 404 on a stop page
is the tell).

Usage: python3 build_stations.py [output_path]
"""
import json
import re
import sys
import time
import urllib.request

BASE = "https://aptransit.co"
LINE_CODES = [
    "1", "2", "3", "4", "5", "5x", "6", "6x", "7", "7x",
    "a", "b", "c", "d", "e", "f", "fs", "fx", "g", "gs", "h",
    "j", "l", "m", "n", "q", "r", "s", "si", "ss", "w", "z",
]

STOP_LINK_RE = re.compile(
    r'<a href="(/city/nyc/stop/(\d+)/([a-z0-9\-]+))"[^>]*>.*?'
    r'<div class="mta-roadmap-desc[^>]*"><div class="flex[^>]*"><div>([^<]+)</div>',
    re.DOTALL,
)
def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def resolve_name_collisions(stations: dict):
    """
    Several NYC station *names* are shared by genuinely separate, unconnected
    stations: there are three different "14 St" stops on three different
    lines, two different "72 St" stops, six different "86 St" stops, and so
    on. A couple of names (like "Times Sq-42 St") really are one walkable
    complex split across several scraped IDs, one per line group.

    Telling the two cases apart turns out not to be reliable from this
    site's data: a stop page's live arrivals include nearby transfer
    suggestions even for physically separate stations a couple of blocks
    away (confirmed by hand for 14 St), so "does A's page mention B's line"
    is not a trustworthy same-complex signal. Rather than risk silently
    merging two unrelated stations — which would tell a user "catch the F
    here" at a platform the F never reaches — every name collision gets
    disambiguated by suffixing each entry with its own line list. A true
    hub like Times Sq ends up as a few adjacent, clearly-labeled entries
    instead of one; lookup.py's ambiguity handling asks which one is meant
    rather than guessing.
    """
    by_name = {}
    for s in stations.values():
        by_name.setdefault(s["name"], []).append(s)
    groups = {name: entries for name, entries in by_name.items() if len(entries) > 1}
    print(f"\n{sum(len(v) for v in groups.values())} candidates across "
          f"{len(groups)} station names collide; disambiguating by line list.")

    for name, entries in groups.items():
        for s in entries:
            suffix = ", ".join(s["lines"])
            stations[s["id"]]["name"] = f"{name} ({suffix})"


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "../assets/nyc_stations.json"
    stations = {}  # stop_id -> {id, slug, name, lines: set}

    for code in LINE_CODES:
        url = f"{BASE}/city/nyc/train/{code}"
        try:
            html = fetch(url)
        except Exception as e:
            print(f"  ! failed to fetch {code}: {e}", file=sys.stderr)
            continue

        found = STOP_LINK_RE.findall(html)
        display_code = code.upper()
        for _, stop_id, slug, name in found:
            entry = stations.setdefault(
                stop_id, {"id": stop_id, "slug": slug, "name": name.strip(), "lines": []}
            )
            if display_code not in entry["lines"]:
                entry["lines"].append(display_code)
        print(f"  {display_code}: {len(found)} stops")
        time.sleep(0.3)  # be polite

    resolve_name_collisions(stations)

    result = sorted(stations.values(), key=lambda s: int(s["id"]))
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nWrote {len(result)} stations to {out_path}")


if __name__ == "__main__":
    main()
