---
name: subway
description: Fast live NYC subway arrival lookups. Use this whenever the user asks when a specific train is coming, gives a train line and a stop such as "when's the next 1 train at 14th St", asks how long until their train arrives, wants directions/route suggestions between two stations, or names an NYC subway station/line and clearly wants real-time arrival info rather than general trivia. Also trigger on casual phrasing that skips the word "train" entirely — "how long till the next uptown 6", "what's running at Union Square right now", "how do I get from Astor Place to Bed-Stuy" — since these are all live-arrival or routing questions this skill answers directly. Do not use it for MTA service planning outside NYC transit, for historical/statistical questions about the subway system, or when the user is just asking general trivia with no interest in current arrivals.
---

# Subway

Live NYC transit data comes from the `mta-nyc-transit` MCP server
(configured in `.mcp.json`), not from scraping any website. Use its tools
directly:

- **`mta_search_stations`** — resolve a station name to a `station_id`.
  NYC has many stations that share a bare name but are physically
  unrelated (three separate "14 St" stops, two "72 St" stops, etc.), and
  a single complex often has one ID per line group (e.g. "14 St-Union Sq"
  has separate IDs for the 4/5/6, the L, and the N/Q/R/W). Always search
  first — never guess an ID — and if results are ambiguous, pick using
  whatever line/neighborhood the user mentioned, or ask.
- **`mta_get_arrivals`** — takes `station_id`, optional `line`, optional
  `direction` (`"N"` or `"S"` — not "uptown"/"downtown" as free text, so
  map the user's wording to one of those two).
- **`mta_plan_trip`** — takes `origin_station_id` and
  `destination_station_id` (search for both first). Use this whenever the
  user names a destination instead of hand-rolling route logic.
- **`mta_get_line_status`** / **`mta_list_alerts`** — check these when a
  line looks delayed or the user asks about service problems.
- **`transit_ask`** — a natural-language fallback across all NYC transit
  modes (subway, bus, ferry, rail, bike) if a user's question doesn't map
  cleanly onto the tools above (e.g. mixed-mode questions).

Relay results conversationally and briefly — this is a fast-lookup skill,
not a research task. State arrival times and service issues plainly; don't
smooth over delays or "No Service" alerts.
