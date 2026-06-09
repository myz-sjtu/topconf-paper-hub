from sqlalchemy import func, select

from app.db.models import Conference, CrawlJob, Paper, PaperSourceRecord
from app.db.session import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        total = db.scalar(select(func.count(Paper.id))) or 0
        with_abstract = db.scalar(select(func.count(Paper.id)).where(Paper.abstract.is_not(None))) or 0
        with_doi_missing_abstract = (
            db.scalar(
                select(func.count(Paper.id)).where(
                    Paper.doi.is_not(None),
                    Paper.abstract.is_(None),
                )
            )
            or 0
        )

        print(f"total_papers={total}")
        print(f"with_abstract={with_abstract}")
        print(f"doi_backed_missing_abstract={with_doi_missing_abstract}")

        print("\nby_domain:")
        for domain, count in db.execute(
            select(Paper.domain, func.count(Paper.id)).group_by(Paper.domain).order_by(Paper.domain)
        ):
            print(f"  {domain}: {count}")

        print("\nby_source:")
        for source_type, count in db.execute(
            select(PaperSourceRecord.source_type, func.count(PaperSourceRecord.id))
            .group_by(PaperSourceRecord.source_type)
            .order_by(PaperSourceRecord.source_type)
        ):
            print(f"  {source_type}: {count}")

        print("\nby_conference:")
        for acronym, count in db.execute(
            select(Conference.acronym, func.count(Paper.id))
            .join(Paper)
            .group_by(Conference.acronym)
            .order_by(Conference.acronym)
        ):
            print(f"  {acronym}: {count}")

        print("\nrecent_jobs:")
        for job in db.scalars(select(CrawlJob).order_by(CrawlJob.created_at.desc()).limit(8)):
            error_count = len([line for line in (job.error or "").splitlines() if line.strip()])
            print(
                "  "
                f"{job.id} status={job.status} "
                f"tasks={job.completed_tasks}/{job.total_tasks} "
                f"inserted={job.inserted_count} updated={job.updated_count} "
                f"errors={error_count}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()

