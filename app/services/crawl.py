import asyncio
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters import get_adapter
from app.db.models import CrawlJob
from app.db.session import SessionLocal
from app.schemas import CrawlJobPreview, CrawlPreviewRequest
from app.services.conference_registry import registry
from app.services.ingestion_pipeline import ingest_records


def create_crawl_job(db: Session, request: CrawlPreviewRequest, tasks: list[CrawlJobPreview]) -> CrawlJob:
    job = CrawlJob(
        id=uuid.uuid4().hex,
        status="queued",
        total_tasks=len(tasks),
        completed_tasks=0,
        requested_payload=request.model_dump(mode="json"),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_crawl_job(db: Session, job_id: str) -> CrawlJob | None:
    return db.scalar(select(CrawlJob).where(CrawlJob.id == job_id))


async def run_crawl_job(job_id: str, request: CrawlPreviewRequest) -> None:
    db = SessionLocal()
    try:
        job = get_crawl_job(db, job_id)
        if job is None:
            return
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()

        tasks = registry.build_crawl_preview(request)
        inserted = 0
        updated = 0
        errors: list[str] = []

        for task in tasks:
            try:
                adapter = get_adapter(task.source_type)
                if adapter is None:
                    errors.append(f"{task.conference} {task.year} {task.source_type}: unsupported source")
                    continue

                conference = registry.get(task.conference)
                if conference is None:
                    errors.append(f"{task.conference}: unknown conference")
                    continue

                records = await adapter.fetch_papers(conference, task.year)
                result = ingest_records(
                    db,
                    conference_seed=conference,
                    year=task.year,
                    records=records,
                )
                inserted += result.inserted
                updated += result.updated
            except Exception as exc:  # pragma: no cover - defensive job isolation
                errors.append(f"{task.conference} {task.year} {task.source_type}: {exc}")
            finally:
                increment_job_progress(db, job_id, inserted=inserted, updated=updated)

        job = get_crawl_job(db, job_id)
        if job:
            job.status = "failed" if errors and inserted == 0 and updated == 0 else "succeeded"
            job.inserted_count = inserted
            job.updated_count = updated
            job.error = "\n".join(errors) if errors else None
            job.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def run_crawl_job_sync(job_id: str, request: CrawlPreviewRequest) -> None:
    asyncio.run(run_crawl_job(job_id, request))


def increment_job_progress(
    db: Session,
    job_id: str,
    *,
    inserted: int | None = None,
    updated: int | None = None,
) -> None:
    job = get_crawl_job(db, job_id)
    if job is None:
        return
    job.completed_tasks += 1
    if inserted is not None:
        job.inserted_count = inserted
    if updated is not None:
        job.updated_count = updated
    db.commit()
