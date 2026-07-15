---
name: subway
description: Fast live NYC subway arrival lookups via AP Transit (aptransit.co). Use this whenever the user asks when a specific train is coming, gives a train line and a stop such as "when's the next 1 train at 14th St", asks how long until their train arrives, wants to know which trains run from one station to another, or names an NYC subway station/line and clearly wants real-time arrival info rather than general trivia. Also trigger on casual phrasing that skips the word "train" entirely — "how long till the next uptown 6", "what's running at Union Square right now", "how do I get from Astor Place to Bed-Stuy" — since these are all live-arrival or routing questions this skill answers directly. Do not use it for MTA service planning outside NYC subway (buses, LIRR, Metro-North, PATH), for historical/statistical questions about the subway system, or when the user is just asking general trivia about a line with no interest in current arrivals.
---

# Subway

A fast lookup skill: user names a train, a stop, and optionally a direction
or destination — you fetch live arrival times from
[AP Transit](https://aptransit.co/city/nyc) and answer in a couple of lines.
Speed matters here more than most skills; the whole point is a quick answer,
not a research project.

## Why a script instead of fetching the page yourself

AP Transit's station pages are server-rendered HTML with consistently
classed markup, so [scripts/lookup.py](scripts/lookup.py) parses them
directly with regex rather than asking a model to eyeball fetched content.
For arrival times — where being off by one row means telling someone the
wrong train — deterministic parsing beats summarization. Always use the
script; don't fetch aptransit.co pages yourself and read them.

The script also resolves fuzzy station names against a bundled database
([assets/nyc_stations.json](assets/nyc_stations.json)) instead of hitting
the network to search, which is most of why this is fast — one HTTP
request per lookup, not several.

## Running a lookup

```bash
python3 scripts/lookup.py --station "<name>" [--line <code>] [--direction <word>] [--destination "<name>"]
```

- `--station` — required. Fuzzy-matched, so "14th st", "14 St", or "Union Sq"
  all work. Doesn't need to be the exact official name.
- `--line` — optional train/service code (`1`, `6`, `A`, `GS`, etc.), case-insensitive.
  Give it whenever the user names a specific train — it also disambiguates
  stations that share a name but are physically unrelated (see below).
- `--direction` — optional. AP Transit labels directions per-station (e.g.
  "Uptown & The Bronx" / "Downtown & Brooklyn", or "Manhattan-bound" for
  lines that don't run north-south). Pass whatever word the user used
  ("uptown", "downtown", "brooklyn", "queens") — the script does a loose
  substring match against the actual header text. If nothing matches, it
  falls back to showing all directions rather than silently guessing wrong.
- `--destination` — optional station name. When set, the script looks for
  train lines serving *both* the origin and destination and reports those
  as direct options before showing arrivals. Per the user's own scoping
  decision for this skill, it only looks for a **direct line** — it
  deliberately doesn't try to compute a multi-transfer route, since a wrong
  guessed transfer is worse than admitting "you'll need to check a map."

Read stdout and relay it conversationally — don't just paste the raw output
verbatim if the user asked a casual question, but don't editorialize the
times either. If a line shows "No Service" or the script reports no
upcoming trains, say that plainly rather than smoothing it over.

## Reading the output

The script always exits 0 and prints a plain-text explanation of what
happened, whether that's a clean result or something that needs a follow-up:

- **Clean match** — direction header(s) each with a short list of
  `[line] time` pairs, soonest first.
- **No match for the station** — say so and ask the user to confirm the
  station name. Before asking, it's worth one retry with a more standard
  phrasing yourself first (e.g. if the user said "penn station" and it
  didn't resolve, try "34 St-Penn Station" or "34th Street Penn Station" —
  you know NYC station names better than a fuzzy string matcher does).
- **Multiple stations could match** — the script lists candidates with the
  lines each serves. This isn't just fuzzy-match noise: NYC genuinely has
  several unrelated stations sharing a bare name (three separate "14 St"
  stations on different lines, two separate "72 St" stations, etc.). Ask
  the user which one they mean, or infer it from context (a mentioned line,
  neighborhood, or borough) and retry with `--line` set — that's usually
  enough to resolve it in one follow-up call instead of a back-and-forth.
  When a `--destination` is ambiguous, giving `--line` for the *origin*
  often resolves it automatically (the script prefers whichever destination
  candidate shares a line with the origin), so try that before asking the
  user anything.
- **No direct line to a destination** — the script says so explicitly
  rather than fabricating a transfer route. Tell the user a transfer looks
  necessary and, if they want the full route, point them to
  aptransit.co/city/nyc rather than guessing one yourself.

## Known gaps

- The four shuttle services (Franklin Ave, 42 St, Rockaway Park, and the
  Staten Island Railway's "H" designation) weren't populated in the bundled
  database — their line pages had zero active trains at build time, which
  is when station lists get scraped. If a lookup for one of these comes back
  empty, say so rather than guessing, and mention re-running
  `scripts/build_stations.py` might pick them up when they're running.
- Station names that collide are disambiguated by suffixing the full line
  list, e.g. `72 St (B, C)` vs `72 St (1, 2, 3)`. That's what you'll see in
  ambiguity messages and in the header of a result — it's not a formatting
  error, it's telling you which physical station you're looking at.

## Example

User: "when's the next downtown 6 train at Union Square?"

```bash
python3 scripts/lookup.py --station "union square" --line 6 --direction downtown
```

Relay the result directly, e.g.: "Next downtown 6 trains at Union Sq: 3 min
and 11 min out."

## Keeping the station database fresh

[assets/nyc_stations.json](assets/nyc_stations.json) is a snapshot of which
stations exist and which lines serve them, built by
[scripts/build_stations.py](scripts/build_stations.py). It doesn't need
rebuilding for a normal lookup — arrival *times* are always fetched live.
Only re-run the build script if `lookup.py` starts returning 404s or
obviously stale station lists (aptransit.co added/removed a line or
station), which should be rare.
