#!/usr/bin/env python3
"""
Build assets/nyc_stations.json from the Transiter API (realtimerail.nyc),
which mirrors live MTA GTFS-realtime data. One-time (or occasional re-run)
build step — arrival times are always fetched live by lookup.py, this just
caches the station name -> stop ID -> lines-served mapping so a lookup
doesn't need a network search first.

Usage: python3 build_stations.py [output_path]
"""
import json
import sys
import time
import urllib.request

BASE = "https://realtimerail.nyc/transiter/v0.6"
SYSTEM = "us-ny-subway"


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def disambiguate_name_collisions(stations: list):
    """
    NYC has several unrelated stations that share a bare name: three separate
    "14 St" stops, three separate "72 St" stops, etc. Suffix each colliding
    entry with the lines it actually serves so a name lookup can't silently
    pick the wrong physical station.
    """
    by_name = {}
    for s in stations:
        by_name.setdefault(s["name"], []).append(s)
    for name, entries in by_name.items():
        if len(entries) <= 1:
            continue
        for s in entries:
            s["name"] = f"{name} ({', '.join(s['lines'])})"


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "../assets/nyc_stations.json"
    stations = []
    first_id = None

    while True:
        url = f"{BASE}/systems/{SYSTEM}/stops"
        if first_id:
            url += f"?firstId={first_id}"
        page = fetch(url)

        for stop in page.get("stops", []):
            if stop.get("type") != "STATION":
                continue
            routes = set()
            for smap in stop.get("serviceMaps", []):
                for route in smap.get("routes", []):
                    routes.add(route["id"])
            children = [c["id"] for c in stop.get("childStops", [])]
            stations.append({
                "id": stop["id"],
                "name": stop["name"],
                "lines": sorted(routes),
                "child_stop_ids": children,
            })

        next_id = page.get("nextId")
        print(f"  fetched page ending {next_id}, {len(stations)} stations so far")
        if not next_id:
            break
        first_id = next_id
        time.sleep(0.1)

    disambiguate_name_collisions(stations)

    with open(out_path, "w") as f:
        json.dump(stations, f, indent=2)
    print(f"\nWrote {len(stations)} stations to {out_path}")


if __name__ == "__main__":
    main()
