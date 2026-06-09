# MVP Roadmap

## Done

- Restore valid Python project metadata and application modules.
- Add curated top-conference registry for networking, architecture/systems, and AI.
- Add SQLAlchemy models for conferences, editions, papers, source records, tags, and crawl jobs.
- Implement DBLP, OpenAlex, OpenReview, CVF, and USENIX metadata adapters.
- Implement normalization, deduplication, source tracing, and keyword tagging.
- Add FastAPI endpoints for health, conferences, editions, papers, crawl preview, crawl run, and job status.
- Add CLI commands for initialization, preview, and synchronous crawl.
- Add unit/API/ingestion tests.

## Next

- Add precise per-year edition dates and proceedings URLs to the registry.
- Add official adapters for PMLR and ACL Anthology.
- Replace in-process job execution with Redis/RQ or Celery for multi-worker deployment.
- Add OpenSearch for richer paper search.
- Add a web UI for browsing by domain, conference, year, and tag.

