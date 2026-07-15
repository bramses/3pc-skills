---
name: subway
description: Fast live NYC subway arrival lookups. Use this whenever the user asks when a specific train is coming, gives a train line and a stop such as "when's the next 1 train at 14th St", asks how long until their train arrives, wants directions/route suggestions between two stations, or names an NYC subway station/line and clearly wants real-time arrival info rather than general trivia. Also trigger on casual phrasing that skips the word "train" entirely — "how long till the next uptown 6", "what's running at Union Square right now", "how do I get from Astor Place to Bed-Stuy" — since these are all live-arrival or routing questions this skill answers directly. Do not use it for MTA service planning outside NYC subway (buses, LIRR, Metro-North, PATH), for historical/statistical questions about the subway system, or when the user is just asking general trivia about a line with no interest in current arrivals.
---

# Subway

Live arrival data comes from the [Transiter](https://github.com/jamespfennell/transiter)
API at realtimerail.nyc, which mirrors live MTA GTFS-realtime data as plain
JSON — no scraping, no MCP dependency, just an HTTP call. Always use
[scripts/lookup.py](scripts/lookup.py); don't call the API yourself, since
the script handles station-name matching and NYC's many same-named-but-unrelated
stations for you.

## Running a lookup

```bash
python3 scripts/lookup.py --station "<name>" [--line <code>] [--direction <word>] [--destination "<name>"]
```

- `--station` — required, fuzzy-matched ("14th st", "union square", etc.)
- `--line` — a train code (`1`, `6`, `A`, `GS`, ...). Give it whenever the
  user names a specific train — it also disambiguates stations that share
  a name but are physically unrelated (three separate "14 St" stops, three
  separate "72 St" stops — this is normal for NYC, not a bug).
- `--direction` — pass whatever word the user used ("uptown", "downtown",
  "north", "brooklyn", ...); the script maps it to the GTFS N/S convention.
  If it can't confidently map the word, it shows both directions rather
  than guessing.
- `--destination` — when set, the script reports which line(s) directly
  connect the two stations before showing arrivals. It only looks for a
  **direct line** — if none exists it says a transfer is needed rather
  than guessing a multi-leg route.

## Reading the output

The script always exits 0 and prints plain text — relay it conversationally,
not verbatim. Three shapes to expect:

- **Clean result** — direction labels (Northbound/Southbound) each with a
  few `[line] time` pairs, soonest first.
- **No match** / **Multiple stations could match** — for "no match," try
  one more standard phrasing yourself before asking the user (you know NYC
  station names better than a fuzzy matcher). For "multiple," the listed
  candidates are genuinely different physical stations, not just fuzzy
  noise — ask which one, or infer it from context and retry with `--line`.
- **No direct line to a destination** — say a transfer looks necessary;
  don't invent a specific transfer route.

## Keeping the station database fresh

[assets/nyc_stations.json](assets/nyc_stations.json) caches station names,
IDs, and which lines serve them, built by
[scripts/build_stations.py](scripts/build_stations.py). Arrival *times*
are always fetched live — this cache only avoids a network search on every
lookup. Re-run the build script if `lookup.py` starts reporting stations
that don't resolve.
