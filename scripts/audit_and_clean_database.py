from __future__ import annotations

import argparse
from dataclasses import dataclass

from app.db.models import Paper, PaperSourceRecord, PaperTag
from app.db.session import SessionLocal
from app.services.conference_registry import registry
from app.services.venue_validation import (
    is_crossref_item_for_conference,
    is_dblp_hit_for_conference,
    is_openalex_work_for_conference,
)


@dataclass
class AuditResult:
    invalid_source_records: int = 0
    orphan_papers: int = 0
    dangling_source_records: int = 0
    dangling_paper_tags: int = 0


def source_record_is_valid(source: PaperSourceRecord) -> bool:
    paper = source.paper
    if paper is None or paper.conference is None:
        return False

    conference = registry.get(paper.conference.acronym)
    if conference is None:
        return False

    payload = source.raw_payload or {}
    if source.source_type == "dblp":
        return is_dblp_hit_for_conference(payload, conference, expected_year=paper.year)
    if source.source_type == "acm_dl":
        return is_crossref_item_for_conference(payload, conference, expected_year=paper.year)
    if source.source_type == "openalex" and payload.get("venue_validated") is True:
        return is_openalex_work_for_conference(payload, conference, expected_year=paper.year)
    return True


def source_record_proves_venue(source: PaperSourceRecord) -> bool:
    payload = source.raw_payload or {}
    if source.source_type == "openalex":
        return payload.get("venue_validated") is True
    return source.source_type in {"acm_dl", "cvf", "dblp", "openreview", "usenix"}


def audit_and_clean(*, dry_run: bool = False) -> AuditResult:
    db = SessionLocal()
    try:
        paper_ids = {paper_id for (paper_id,) in db.query(Paper.id).all()}
        dangling_source_ids = [
            source.id
            for source in db.query(PaperSourceRecord).all()
            if source.paper_id not in paper_ids
        ]
        dangling_tag_ids = [
            tag.id
            for tag in db.query(PaperTag).all()
            if tag.paper_id not in paper_ids
        ]

        if dangling_source_ids and not dry_run:
            db.query(PaperSourceRecord).filter(PaperSourceRecord.id.in_(dangling_source_ids)).delete(
                synchronize_session=False
            )
        if dangling_tag_ids and not dry_run:
            db.query(PaperTag).filter(PaperTag.id.in_(dangling_tag_ids)).delete(synchronize_session=False)
        if not dry_run and (dangling_source_ids or dangling_tag_ids):
            db.flush()

        invalid_source_ids = [
            source.id
            for source in db.query(PaperSourceRecord).all()
            if not source_record_is_valid(source)
        ]

        if invalid_source_ids and not dry_run:
            db.query(PaperSourceRecord).filter(PaperSourceRecord.id.in_(invalid_source_ids)).delete(
                synchronize_session=False
            )
            db.flush()

        orphan_ids = [
            paper.id
            for paper in db.query(Paper).all()
            if not any(source_record_proves_venue(source) for source in paper.source_records)
        ]

        if orphan_ids and not dry_run:
            db.query(PaperSourceRecord).filter(PaperSourceRecord.paper_id.in_(orphan_ids)).delete(
                synchronize_session=False
            )
            db.query(PaperTag).filter(PaperTag.paper_id.in_(orphan_ids)).delete(synchronize_session=False)
            db.query(Paper).filter(Paper.id.in_(orphan_ids)).delete(synchronize_session=False)
            db.commit()
        elif dry_run:
            db.rollback()
        elif not dry_run:
            db.commit()

        return AuditResult(
            invalid_source_records=len(invalid_source_ids),
            orphan_papers=len(orphan_ids),
            dangling_source_records=len(dangling_source_ids),
            dangling_paper_tags=len(dangling_tag_ids),
        )
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = audit_and_clean(dry_run=args.dry_run)
    prefix = "would_delete" if args.dry_run else "deleted"
    print(f"{prefix}_dangling_source_records={result.dangling_source_records}")
    print(f"{prefix}_dangling_paper_tags={result.dangling_paper_tags}")
    print(f"{prefix}_invalid_source_records={result.invalid_source_records}")
    print(f"{prefix}_orphan_papers={result.orphan_papers}")


if __name__ == "__main__":
    main()
