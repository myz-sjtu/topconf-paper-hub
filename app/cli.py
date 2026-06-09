import argparse
import asyncio

from app.db.session import SessionLocal, init_db
from app.schemas import CrawlPreviewRequest
from app.services.abstract_enrichment import enrich_missing_abstracts_from_openalex
from app.services.conference_registry import registry
from app.services.crawl import create_crawl_job, run_crawl_job
from app.services.ingestion_pipeline import seed_conferences, seed_taxonomy


def cmd_init_db(_: argparse.Namespace) -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_conferences(db, registry.conferences)
        seed_taxonomy(db)
    finally:
        db.close()
    print("Initialized database and seeded conferences/taxonomy.")


def cmd_preview(args: argparse.Namespace) -> None:
    request = CrawlPreviewRequest(
        domain=args.domain,
        conferences=args.conferences,
        years=args.years,
        sources=args.sources,
    )
    tasks = registry.build_crawl_preview(request)
    for task in tasks:
        print(f"{task.conference}\t{task.year}\t{task.source_type}\t{task.domain}")
    print(f"total={len(tasks)}")


def cmd_crawl(args: argparse.Namespace) -> None:
    init_db()
    request = CrawlPreviewRequest(
        domain=args.domain,
        conferences=args.conferences,
        years=args.years,
        sources=args.sources,
    )
    tasks = registry.build_crawl_preview(request)
    db = SessionLocal()
    try:
        job = create_crawl_job(db, request, tasks)
        job_id = job.id
    finally:
        db.close()
    asyncio.run(run_crawl_job(job_id, request))
    print(f"crawl_job={job_id}")


def cmd_enrich_abstracts(args: argparse.Namespace) -> None:
    init_db()
    db = SessionLocal()
    try:
        result = asyncio.run(
            enrich_missing_abstracts_from_openalex(
                db,
                limit=args.limit,
                batch_size=args.batch_size,
                delay_seconds=args.delay_seconds,
            )
        )
    finally:
        db.close()

    print(f"scanned={result.scanned}")
    print(f"enriched={result.enriched}")
    print(f"source_records_added={result.source_records_added}")
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(error)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="topconf")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-db", help="Create tables and seed registry data")
    init_parser.set_defaults(func=cmd_init_db)

    preview_parser = subparsers.add_parser("preview", help="Preview crawl tasks")
    add_crawl_args(preview_parser)
    preview_parser.set_defaults(func=cmd_preview)

    crawl_parser = subparsers.add_parser("crawl", help="Run crawl tasks synchronously")
    add_crawl_args(crawl_parser)
    crawl_parser.set_defaults(func=cmd_crawl)

    enrich_parser = subparsers.add_parser(
        "enrich-abstracts",
        help="Fill missing abstracts for existing DOI-backed papers via OpenAlex",
    )
    enrich_parser.add_argument("--limit", type=int, default=None)
    enrich_parser.add_argument("--batch-size", type=int, default=50)
    enrich_parser.add_argument("--delay-seconds", type=float, default=0.2)
    enrich_parser.set_defaults(func=cmd_enrich_abstracts)
    return parser


def add_crawl_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--domain", choices=["network", "architecture", "ai"], default=None)
    parser.add_argument("--conference", action="append", dest="conferences", default=None)
    parser.add_argument("--year", action="append", dest="years", type=int, default=None)
    parser.add_argument("--source", action="append", dest="sources", default=None)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
