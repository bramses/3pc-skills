---
name: nyc-data-assistant
description: Find, visualize, and turn into next actions any live dataset from NYC Open Data (data.cityofnewyork.us) — restaurant inspections, 311 complaints, building permits, housing violations, crime stats, noise complaints, and hundreds of other civic datasets. Use this whenever the user asks an open-ended question about NYC city services, civic conditions, or city data and wants a chart, dashboard, or breakdown built from it, even if they don't name a specific dataset, say "open data," or say "Socrata" — e.g. "what's going on with noise complaints near me," "how are restaurant inspections in the Bronx," "pull permit data for this address," "show me a chart of 311 complaints by borough." Do not use this for real-time NYC transit questions (subway/bus/ferry/bike arrivals or service status) if a dedicated transit MCP is connected — this skill is for the general Socrata open-data catalog, not live transit feeds.
---

# NYC Data Assistant

Answer open-ended NYC questions by finding the closest matching dataset on
NYC Open Data, pulling real rows from it, visualizing them, and telling the
user what to actually do next — a phone number to call, an agency to
contact — but only when that information genuinely exists in the data.

## Why this works everywhere (Code, Desktop, claude.ai)

NYC Open Data runs on Socrata. Its catalog/discovery API and its per-dataset
data API (SODA) are both plain public HTTPS endpoints that return JSON with
no authentication required for reads. Because of that, **this skill fetches
those endpoints directly with your own built-in web-fetch tool — never a
bundled script**. A bundled Python/Bash script making its own network call
would be silently blocked in the Claude Desktop/claude.ai sandbox (this is
the exact reason an earlier skill in this repo, "subway," was built twice and
then pulled — see `git show 8670d02`). Built-in fetch was confirmed live
against `data.cityofnewyork.us` from an actual Desktop/claude.ai session, so
this approach is verified, not assumed.

## Workflow

### 1. Find the closest dataset

Fetch the catalog search endpoint with terms drawn from the user's question:

```
https://api.us.socrata.com/api/catalog/v1?domains=data.cityofnewyork.us&q=<search terms>&limit=5
```

This returns candidate datasets with names, descriptions, resource IDs, and
column info. Picking the "closest" dataset is a judgment call, not a
deterministic lookup — read the descriptions and column names, not just the
titles, before choosing. If two or three candidates are genuinely plausible
for an ambiguous question (e.g. "complaints" could mean 311, DOB, or DOHMH
data), say so and offer the user a quick pick rather than silently guessing
one and running with it.

See [references/socrata-api.md](references/socrata-api.md) for query syntax
details, response shape, and tips for narrowing ambiguous searches.

### 2. Pull real rows

Fetch the dataset's SODA endpoint using the resource ID from step 1:

```
https://data.cityofnewyork.us/resource/<resource-id>.json?$limit=<n>
```

Use Socrata's query parameters (`$where`, `$select`, `$group`, `$order`) to
filter or aggregate server-side instead of pulling everything and filtering
locally — this is faster and avoids the rate limit described below. See
[references/socrata-api.md](references/socrata-api.md) for the query syntax
and worked examples (filtering by borough, date range, grouping counts).

### 3. Visualize

Build a chart or dashboard from the pulled data as an Artifact. Follow the
`dataviz` skill's guidance for chart choice, color, and layout — don't
reinvent styling here.

### 4. Give next actions — grounded, not invented

Look at the actual fields in the rows you pulled for anything
actionable: phone numbers, emails, agency names, complaint/ticket IDs, links.
Some NYC datasets carry this (e.g. DOHMH restaurant inspection records
include a `phone` field); most don't. If the pulled data has no contact or
follow-up information, say that plainly — "this dataset doesn't include
contact details" — instead of inventing a plausible-looking phone number or
311-style suggestion that isn't actually backed by the data you fetched.

Label what kind of contact it actually is before presenting it. A `phone`
field on a restaurant inspection record is that restaurant's own business
line, not a DOHMH case worker or complaint line — confirmed by checking a
real record (no agency contact field exists in that dataset at all). Say
whose number it is ("the restaurant's listed number") rather than letting
the user assume it routes to the city.

## Constraints to keep in mind

- **WebFetch only, never a bundled script.** This is what makes the skill
  work on Desktop/claude.ai — don't add a Python/Bash script that calls
  these APIs itself, even for convenience.
- **Unauthenticated rate limits.** Socrata throttles anonymous requests.
  Fine for one user working through a question, but don't loop rapid-fire
  calls (e.g. fetching the same dataset repeatedly with slightly different
  filters) when a single well-formed `$where`/`$group` query would do — and
  don't assume this holds up under many simultaneous users (e.g. a full
  workshop room hitting it at once).
- **Never fabricate contact info.** Only surface phone/email/agency details
  that are literally present in the fetched rows.
