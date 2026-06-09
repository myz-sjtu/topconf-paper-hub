from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Conference, Paper, PaperSourceRecord, PaperTag, TaxonomyTag
from app.db.session import get_db
from app.schemas import PaperListResponse, PaperRead, PaperSourceRecordRead, PaperTagRead
from app.services.conference_registry import registry

router = APIRouter(tags=["papers"])


@router.get("/papers", response_model=PaperListResponse)
def list_papers(
    domain: str | None = None,
    conference: str | None = None,
    year: int | None = None,
    tag: str | None = None,
    q: str | None = None,
    limit: int = Query(default=50, ge=1, le=50000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaperListResponse:
    query = select(Paper).join(Conference)
    count_query = select(func.count(Paper.id)).join(Conference)

    filters = []
    if domain:
        filters.append(Paper.domain == domain)
    if conference:
        seed = registry.get(conference)
        acronym = seed.acronym if seed else conference
        filters.append(Conference.acronym == acronym)
    if year:
        filters.append(Paper.year == year)
    if q:
        like = f"%{q.lower()}%"
        filters.append(or_(func.lower(Paper.title).like(like), func.lower(Paper.abstract).like(like)))
    if tag:
        query = query.join(PaperTag).join(TaxonomyTag)
        count_query = count_query.join(PaperTag).join(TaxonomyTag)
        filters.append(TaxonomyTag.slug == tag)

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    total = db.scalar(count_query) or 0
    papers = db.scalars(
        query.options(
            selectinload(Paper.conference),
            selectinload(Paper.edition),
            selectinload(Paper.source_records),
            selectinload(Paper.tags).selectinload(PaperTag.tag),
        )
        .order_by(Paper.year.desc(), Conference.acronym, Paper.title)
        .limit(limit)
        .offset(offset)
    ).all()
    return PaperListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[serialize_paper(paper) for paper in papers],
    )


@router.get("/papers/{paper_id}", response_model=PaperRead)
def get_paper(paper_id: int, db: Session = Depends(get_db)) -> PaperRead:
    paper = db.scalar(
        select(Paper)
        .where(Paper.id == paper_id)
        .options(
            selectinload(Paper.conference),
            selectinload(Paper.edition),
            selectinload(Paper.source_records),
            selectinload(Paper.tags).selectinload(PaperTag.tag),
        )
    )
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return serialize_paper(paper)


def serialize_paper(paper: Paper) -> PaperRead:
    return PaperRead(
        id=paper.id,
        title=paper.title,
        authors=paper.authors or [],
        abstract=paper.abstract,
        doi=paper.doi,
        paper_url=paper.paper_url,
        pdf_url=paper.pdf_url,
        publication_date=paper.publication_date,
        conference=paper.conference.acronym,
        year=paper.year,
        domain=paper.domain,
        edition_start_date=paper.edition.start_date,
        edition_end_date=paper.edition.end_date,
        tags=[
            PaperTagRead(
                domain=item.tag.domain,
                slug=item.tag.slug,
                label=item.tag.label,
                score=item.score,
                method=item.method,
            )
            for item in paper.tags
        ],
        source_records=[
            PaperSourceRecordRead.model_validate(source_record)
            for source_record in sorted(
                paper.source_records,
                key=lambda item: (item.source_type, item.id),
            )
            if isinstance(source_record, PaperSourceRecord)
        ],
    )
