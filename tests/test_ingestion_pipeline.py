from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.adapters.base import RawPaperRecord
from app.db.models import Base, Paper
from app.schemas import ConferenceSeed
from app.services.ingestion_pipeline import ingest_records, seed_taxonomy


def make_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def test_ingestion_inserts_and_deduplicates_by_doi() -> None:
    db = make_session()
    seed_taxonomy(db)
    conference = ConferenceSeed(
        acronym="SIGCOMM",
        full_name="ACM SIGCOMM Conference",
        domain="network",
        default_sources=["dblp"],
    )
    first = RawPaperRecord(
        source_type="dblp",
        title="RDMA Congestion Control in Datacenters",
        authors=["Ada Lovelace"],
        doi="https://doi.org/10.1145/test",
        raw_payload={"venue_validated": True},
    )
    second = RawPaperRecord(
        source_type="openalex",
        title="RDMA Congestion Control in Datacenters",
        authors=["Ada Lovelace"],
        doi="10.1145/TEST",
        paper_url="https://example.org/paper",
        raw_payload={"venue_validated": True},
    )

    result = ingest_records(db, conference_seed=conference, year=2025, records=[first, second])
    papers = list(db.scalars(select(Paper)).all())

    assert result.inserted == 1
    assert result.updated == 1
    assert len(papers) == 1
    assert papers[0].year == 2025
    assert papers[0].conference.acronym == "SIGCOMM"
    assert papers[0].tags


def test_ingestion_skips_unvalidated_search_source() -> None:
    db = make_session()
    seed_taxonomy(db)
    conference = ConferenceSeed(
        acronym="KDD",
        full_name="ACM SIGKDD Conference",
        domain="ai",
    )
    raw = RawPaperRecord(
        source_type="openalex",
        title="Mobile application based on KDD to predict high-crime areas",
        authors=["Ada Lovelace"],
        doi="10.3389/fcomp.2025.1585632",
        raw_payload={"venue_validated": False},
    )

    result = ingest_records(db, conference_seed=conference, year=2025, records=[raw])

    assert result.skipped == 1
    assert list(db.scalars(select(Paper)).all()) == []
