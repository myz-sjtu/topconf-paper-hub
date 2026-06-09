from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import CrawlJobRead, CrawlPreviewRequest, CrawlPreviewResponse, CrawlRunRequest
from app.services.conference_registry import registry
from app.services.crawl import create_crawl_job, get_crawl_job, run_crawl_job, run_crawl_job_sync

router = APIRouter(tags=["crawl"])


@router.post("/crawl/preview", response_model=CrawlPreviewResponse)
def preview_crawl(request: CrawlPreviewRequest) -> CrawlPreviewResponse:
    try:
        items = registry.build_crawl_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CrawlPreviewResponse(total=len(items), items=items)


@router.post("/crawl/run", response_model=CrawlJobRead)
async def run_crawl(
    request: CrawlRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> CrawlJobRead:
    try:
        tasks = registry.build_crawl_preview(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job = create_crawl_job(db, request, tasks)
    preview_request = CrawlPreviewRequest(**request.model_dump(exclude={"async_run"}))
    if request.async_run:
        background_tasks.add_task(run_crawl_job_sync, job.id, preview_request)
    else:
        await run_crawl_job(job.id, preview_request)
        db.refresh(job)
    return CrawlJobRead.model_validate(job)


@router.get("/crawl/jobs/{job_id}", response_model=CrawlJobRead)
def get_job(job_id: str, db: Session = Depends(get_db)) -> CrawlJobRead:
    job = get_crawl_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return CrawlJobRead.model_validate(job)

