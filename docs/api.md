# API

Base path: `/api/v1`

## Health

- `GET /health`

## Conferences

- `GET /conferences?domain=&active=`
- `GET /conferences/{acronym}`

Aliases are normalized through the conference registry, so `NIPS` resolves to `NeurIPS` when the database has been seeded.

## Editions

- `GET /editions?conference=&year=`

Returns conference-year groupings used for date-based browsing.

## Papers

- `GET /papers?domain=&conference=&year=&tag=&q=&limit=&offset=`
- `GET /papers/{paper_id}`

Paper responses include conference, year, tags, and source records.

## Crawl

- `POST /crawl/preview`
- `POST /crawl/run`
- `GET /crawl/jobs/{job_id}`

Example preview request:

```json
{
  "conferences": ["SIGCOMM"],
  "years": [2025],
  "sources": ["dblp"]
}
```

Example run request:

```json
{
  "domain": "ai",
  "years": [2025],
  "sources": ["openreview", "dblp"],
  "async_run": true
}
```

