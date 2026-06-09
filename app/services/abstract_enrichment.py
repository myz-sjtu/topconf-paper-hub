import asyncio
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.openalex import OpenAlexAdapter
from app.db.models import Paper, PaperSourceRecord
from app.services.dedup import normalize_doi
from app.services.ingestion_pipeline import ensure_paper_tags


@dataclass
class AbstractEnrichmentResult:
    scanned: int = 0
    enriched: int = 0
    source_records_added: int = 0
    errors: list[str] = field(default_factory=list)


async def enrich_missing_abstracts_from_openalex(
    db: Session,
    *,
    limit: int | None = None,
    batch_size: int = 50,
    delay_seconds: float = 0.2,
) -> AbstractEnrichmentResult:
    batch_size = max(1, min(batch_size, 50))
    query = (
        select(Paper)
        .where(Paper.doi.is_not(None), Paper.abstract.is_(None))
        .order_by(Paper.year.desc(), Paper.id)
    )
    if limit:
        query = query.limit(limit)

    papers = list(db.scalars(query).all())
    result = AbstractEnrichmentResult(scanned=len(papers))
    adapter = OpenAlexAdapter()

    for start in range(0, len(papers), batch_size):
        batch = papers[start : start + batch_size]
        doi_to_paper = {normalize_doi(paper.doi): paper for paper in batch if paper.doi}
        try:
            records = await adapter.fetch_by_dois([paper.doi for paper in batch if paper.doi])
        except Exception as exc:  # pragma: no cover - network defensive path
            result.errors.append(f"batch {start // batch_size + 1}: {exc}")
            continue

        for record in records:
            paper = doi_to_paper.get(normalize_doi(record.doi))
            if paper is None:
                continue
            if record.abstract and not paper.abstract:
                paper.abstract = record.abstract.strip()
                ensure_paper_tags(db, paper, paper.domain)
                result.enriched += 1
            if ensure_openalex_source_record(db, paper, record):
                result.source_records_added += 1

        db.commit()
        if delay_seconds:
            await asyncio.sleep(delay_seconds)

    return result


def ensure_openalex_source_record(db: Session, paper: Paper, record) -> bool:
    existing = db.scalar(
        select(PaperSourceRecord).where(
            PaperSourceRecord.paper_id == paper.id,
            PaperSourceRecord.source_type == record.source_type,
            PaperSourceRecord.source_paper_id == record.source_paper_id,
        )
    )
    if existing:
        existing.raw_payload = record.raw_payload
        existing.source_url = record.source_url
        return False

    db.add(
        PaperSourceRecord(
            paper_id=paper.id,
            source_type=record.source_type,
            source_url=record.source_url,
            source_paper_id=record.source_paper_id,
            raw_payload=record.raw_payload,
        )
    )
    return True

