# Socrata API mechanics

Two separate APIs are involved. Both are plain HTTPS GET, both return JSON,
neither requires authentication for read access at moderate volume.

## 1. Catalog / discovery API — find the right dataset

```
https://api.us.socrata.com/api/catalog/v1?domains=data.cityofnewyork.us&q=<query>&limit=5
```

- `domains=data.cityofnewyork.us` scopes results to NYC's portal specifically
  (the same catalog API indexes every Socrata city/state portal — without
  this param you'll get datasets from other cities too).
- `q=` accepts free-text search terms. Use a few plain keywords from the
  user's question (e.g. `q=restaurant inspection`, `q=noise complaint`,
  `q=building permits`) rather than the full sentence — Socrata's search
  matches better on short keyword sets than full questions.
- `limit=` caps the number of candidate datasets returned; 5 is usually
  enough to see if there's a clear winner or genuine ambiguity.

Each result includes:
- `resource.id` — the resource ID you need for step 2 (e.g. `43nn-pn8j`).
- `resource.name` / `resource.description` — read both; names can be
  generic ("Complaints") while descriptions clarify scope (DOB vs DOHMH vs
  311).
- `resource.columns_field_name` / `columns_name` — column names, useful for
  checking up front whether a dataset actually has the fields you'll need
  (e.g. does it have `phone`, `latitude`/`longitude`, a date field to filter
  on) before committing to it.
- `link` — a human-readable URL to the dataset's page on the portal, worth
  including if you want to point the user at the source.

If the query returns nothing useful, broaden or rephrase the search terms —
don't assume the dataset doesn't exist after a single failed query with
narrow phrasing.

## 2. SODA API — pull actual rows

```
https://data.cityofnewyork.us/resource/<resource-id>.json
```

Add Socrata Query Language (SoQL) parameters to filter/shape server-side:

| Param | Purpose | Example |
|---|---|---|
| `$limit` | Row cap | `$limit=50` |
| `$where` | Filter condition | `$where=boro='BRONX'` |
| `$select` | Choose/aggregate columns | `$select=boro,count(*) as total` |
| `$group` | Group for aggregation (pairs with `$select`) | `$group=boro` |
| `$order` | Sort | `$order=inspection_date DESC` |
| `$q` | Full-text search across the whole row | `$q=pizza` |

Worked examples:

**Count restaurant inspections by borough:**
```
https://data.cityofnewyork.us/resource/43nn-pn8j.json?$select=boro,count(*) as total&$group=boro
```

**Recent 311 noise complaints in Brooklyn:**
```
https://data.cityofnewyork.us/resource/erm2-nwe9.json?$where=borough='BROOKLYN' AND complaint_type like '%25Noise%25'&$order=created_date DESC&$limit=25
```
(Note: `%25` is a URL-encoded `%`, needed for SoQL's `LIKE` wildcard inside a
URL.)

**Filter by date range:**
```
$where=created_date between '2026-01-01T00:00:00' and '2026-07-01T00:00:00'
```

String values in `$where` need single quotes (`boro='BRONX'`); column names
are case-sensitive and typically `snake_case` — check the catalog result's
column list from step 1 rather than guessing the field name.

## Rate limits

Anonymous (unauthenticated) requests are throttled by Socrata — exact limits
aren't published but are generous enough for a single user working through a
handful of queries in a conversation. Avoid firing many rapid, near-duplicate
requests (e.g. re-fetching the same dataset with only a `$limit` change) —
consolidate into one well-formed query with `$where`/`$group` instead. If a
request starts returning errors or empty results unexpectedly after several
rapid calls, that's a plausible rate-limit signal — space out requests rather
than retrying immediately in a loop.
