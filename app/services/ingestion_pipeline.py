from dataclasses import dataclass
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.adapters.base import RawPaperRecord
from app.db.models import (
    Conference,
    ConferenceEdition,
    Paper,
    PaperSourceRecord,
    PaperTag,
    TaxonomyTag,
)
from app.schemas import ConferenceSeed
from app.services.classification import infer_subtopics, load_keyword_rules
from app.services.dedup import normalize_author, normalize_doi, normalize_title
from app.services.venue_validation import raw_record_passed_venue_validation

SOURCE_CONFIDENCE = {
    "official": 0.98,
    "openreview": 0.95,
    "pmlr": 0.9,
    "cvf": 0.9,
    "usenix": 0.9,
    "acl_anthology": 0.9,
    "acm_dl": 0.88,
    "dblp": 0.82,
    "openalex": 0.72,
    "ieee_xplore": 0.7,
}


@dataclass
class IngestResult:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0

    def add(self, action: str) -> None:
        if action == "inserted":
            self.inserted += 1
        elif action == "updated":
            self.updated += 1
        else:
            self.skipped += 1


def seed_conferences(db: Session, seeds: list[ConferenceSeed]) -> None:
    for seed in seeds:
        ensure_conference(db, seed)
    db.commit()


def seed_taxonomy(db: Session) -> None:
    for domain, tags in load_keyword_rules().items():
        for slug in tags:
            existing = db.scalar(
                select(TaxonomyTag).where(TaxonomyTag.domain == domain, TaxonomyTag.slug == slug)
            )
            if existing:
                continue
            db.add(TaxonomyTag(domain=domain, slug=slug, label=slug.replace("_", " ").title()))
    db.commit()


def ensure_conference(db: Session, seed: ConferenceSeed) -> Conference:
    conference = db.scalar(select(Conference).where(Conference.acronym == seed.acronym))
    if conference is None:
        conference = Conference(acronym=seed.acronym, full_name=seed.full_name, domain=seed.domain)
        db.add(conference)
        db.flush()

    conference.full_name = seed.full_name
    conference.domain = seed.domain
    conference.subdomain_default = seed.subdomain_default
    conference.publisher = seed.publisher
    conference.official_url = seed.official_url
    conference.active = seed.active
    conference.aliases = list(seed.aliases)
    conference.default_sources = list(seed.default_sources)
    return conference


def ensure_edition(
    db: Session,
    conference: Conference,
    year: int,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    proceedings_url: str | None = None,
) -> ConferenceEdition:
    edition = db.scalar(
        select(ConferenceEdition).where(
            ConferenceEdition.conference_id == conference.id,
            ConferenceEdition.year == year,
        )
    )
    if edition is None:
        edition = ConferenceEdition(conference_id=conference.id, year=year)
        db.add(edition)
        db.flush()
    if start_date:
        edition.start_date = start_date
    if end_date:
        edition.end_date = end_date
    if proceedings_url:
        edition.proceedings_url = proceedings_url
    return edition


def ingest_records(
    db: Session,
    *,
    conference_seed: ConferenceSeed,
    year: int,
    records: list[RawPaperRecord],
) -> IngestResult:
    conference = ensure_conference(db, conference_seed)
    edition = ensure_edition(db, conference, year)
    result = IngestResult()
    for raw in records:
        result.add(ingest_raw_record(db, conference, edition, raw))
    db.commit()
    return result


def ingest_raw_record(
    db: Session,
    conference: Conference,
    edition: ConferenceEdition,
    raw: RawPaperRecord,
) -> str:
    title = raw.title.strip()
    if not title:
        return "skipped"
    if not raw_record_passed_venue_validation(raw.source_type, raw.raw_payload):
        return "skipped"

    title_key = normalize_title(title)
    doi = normalize_doi(raw.doi)
    first_author_key = normalize_author(raw.authors[0]) if raw.authors else None
    confidence = SOURCE_CONFIDENCE.get(raw.source_type, 0.5)

    paper = find_existing_paper(
        db,
        conference_id=conference.id,
        edition_id=edition.id,
        year=edition.year,
        title_key=title_key,
        first_author_key=first_author_key,
        doi=doi,
        paper_url=raw.paper_url,
        pdf_url=raw.pdf_url,
        source_type=raw.source_type,
        source_paper_id=raw.source_paper_id,
    )

    action = "updated"
    if paper is None:
        paper = Paper(
            title=title,
            title_key=title_key,
            authors=list(raw.authors),
            first_author_key=first_author_key,
            abstract=raw.abstract.strip() if raw.abstract else None,
            doi=doi,
            paper_url=raw.paper_url,
            pdf_url=raw.pdf_url,
            publication_date=raw.publication_date,
            conference_id=conference.id,
            edition_id=edition.id,
            year=edition.year,
            domain=conference.domain,
            source_confidence=confidence,
        )
        db.add(paper)
        db.flush()
        action = "inserted"
    else:
        merge_paper_fields(paper, raw, doi=doi, confidence=confidence)

    ensure_source_record(db, paper, raw)
    ensure_paper_tags(db, paper, conference.domain)
    return action


def find_existing_paper(
    db: Session,
    *,
    conference_id: int,
    edition_id: int,
    year: int,
    title_key: str,
    first_author_key: str | None,
    doi: str | None,
    paper_url: str | None,
    pdf_url: str | None,
    source_type: str,
    source_paper_id: str | None,
) -> Paper | None:
    if source_paper_id:
        source_record = db.scalar(
            select(PaperSourceRecord).where(
                PaperSourceRecord.source_type == source_type,
                PaperSourceRecord.source_paper_id == source_paper_id,
            )
        )
        if source_record:
            return source_record.paper

    if doi:
        paper = db.scalar(select(Paper).where(Paper.doi == doi))
        if paper:
            return paper

    url_filters = []
    if paper_url:
        url_filters.append(Paper.paper_url == paper_url)
    if pdf_url:
        url_filters.append(Paper.pdf_url == pdf_url)
    if url_filters:
        paper = db.scalar(select(Paper).where(or_(*url_filters)))
        if paper:
            return paper

    query = select(Paper).where(
        Paper.conference_id == conference_id,
        Paper.edition_id == edition_id,
        Paper.year == year,
        Paper.title_key == title_key,
    )
    if first_author_key:
        query = query.where(
            or_(Paper.first_author_key == first_author_key, Paper.first_author_key.is_(None))
        )
    return db.scalar(query)


def merge_paper_fields(paper: Paper, raw: RawPaperRecord, *, doi: str | None, confidence: float) -> None:
    if confidence >= paper.source_confidence:
        paper.title = raw.title.strip() or paper.title
        if raw.authors:
            paper.authors = list(raw.authors)
            paper.first_author_key = normalize_author(raw.authors[0])
        paper.abstract = raw.abstract.strip() if raw.abstract else paper.abstract
    elif raw.abstract and not paper.abstract:
        paper.abstract = raw.abstract.strip()

    paper.doi = paper.doi or doi
    paper.paper_url = paper.paper_url or raw.paper_url
    paper.pdf_url = paper.pdf_url or raw.pdf_url
    paper.publication_date = paper.publication_date or raw.publication_date
    paper.source_confidence = max(paper.source_confidence, confidence)


def ensure_source_record(db: Session, paper: Paper, raw: RawPaperRecord) -> PaperSourceRecord:
    query = select(PaperSourceRecord).where(
        PaperSourceRecord.paper_id == paper.id,
        PaperSourceRecord.source_type == raw.source_type,
    )
    if raw.source_paper_id:
        query = query.where(PaperSourceRecord.source_paper_id == raw.source_paper_id)
    elif raw.source_url:
        query = query.where(PaperSourceRecord.source_url == raw.source_url)
    existing = db.scalar(query)
    if existing:
        existing.raw_payload = raw.raw_payload
        return existing

    source_record = PaperSourceRecord(
        paper_id=paper.id,
        source_type=raw.source_type,
        source_url=raw.source_url,
        source_paper_id=raw.source_paper_id,
        raw_payload=raw.raw_payload,
    )
    db.add(source_record)
    return source_record


def ensure_paper_tags(db: Session, paper: Paper, domain: str) -> None:
    inferred = infer_subtopics(domain, [paper.title, paper.abstract])
    seen: set[tuple[int, str]] = set()
    for slug, score, method in inferred:
        tag = db.scalar(select(TaxonomyTag).where(TaxonomyTag.domain == domain, TaxonomyTag.slug == slug))
        if tag is None:
            tag = TaxonomyTag(domain=domain, slug=slug, label=slug.replace("_", " ").title())
            db.add(tag)
            db.flush()

        key = (tag.id, method)
        if key in seen:
            continue
        seen.add(key)

        existing = db.scalar(
            select(PaperTag).where(
                PaperTag.paper_id == paper.id,
                PaperTag.tag_id == tag.id,
                PaperTag.method == method,
            )
        )
        if existing:
            existing.score = max(existing.score, score)
        else:
            db.add(PaperTag(paper_id=paper.id, tag_id=tag.id, score=score, method=method))
            db.flush()
