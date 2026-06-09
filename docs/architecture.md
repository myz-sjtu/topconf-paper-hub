# Architecture

## Core Idea

TopConf Paper Hub uses a conference-registry-first architecture. The system does not blindly crawl the web. It starts from a curated list of top conferences, generates crawl tasks by conference/year/source, and stores metadata-first paper records.

```text
Conference Registry
        |
        v
Crawl Preview / Scheduler
        |
        v
Source Adapters -> RawPaperRecord
        |
        v
Ingestion Pipeline -> Normalize -> Deduplicate -> Tag
        |
        v
SQL Database
        |
        v
FastAPI
```

## Modules

- `configs/conferences/top_conferences.yaml`: top-conference registry and source preferences.
- `configs/taxonomy/tags.yaml`: keyword rules for first-version subtopic tagging.
- `app/adapters/`: source-specific metadata fetchers.
- `app/services/ingestion_pipeline.py`: normalization, merge, source tracing, and tagging.
- `app/services/crawl.py`: job creation and task execution.
- `app/api/routes/`: HTTP APIs for conferences, editions, papers, and crawl jobs.

## Storage

- SQLite is the default local database.
- PostgreSQL can be enabled by changing `DATABASE_URL`.
- Redis is included in `docker-compose.yml` as the deployment target for a future distributed queue.
- APScheduler supports daily incremental crawls when `SCHEDULER_ENABLED=true`.

## Compliance Boundary

The first version stores metadata and links. It does not download restricted PDFs, bypass access controls, or scrape behind login/paywall pages.

