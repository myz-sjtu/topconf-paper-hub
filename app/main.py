from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.schemas import CrawlPreviewRequest
from app.services.conference_registry import registry
from app.services.crawl import create_crawl_job, run_crawl_job_sync
from app.services.ingestion_pipeline import seed_conferences, seed_taxonomy
from app.web import index_page

scheduler = BackgroundScheduler(timezone="UTC")


def scheduled_incremental_crawl() -> None:
    db = SessionLocal()
    try:
        request = CrawlPreviewRequest(years=registry.default_years())
        tasks = registry.build_crawl_preview(request)
        job = create_crawl_job(db, request, tasks)
        run_crawl_job_sync(job.id, request)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_conferences(db, registry.conferences)
        seed_taxonomy(db)
    finally:
        db.close()

    if settings.scheduler_enabled and not scheduler.running:
        scheduler.add_job(
            scheduled_incremental_crawl,
            "cron",
            hour=settings.scheduler_hour_utc,
            id="daily_incremental_crawl",
            replace_existing=True,
        )
        scheduler.start()
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/", include_in_schema=False)
def index():
    return index_page()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


app.include_router(api_router, prefix=settings.api_v1_prefix)
