from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class Conference(Base):
    __tablename__ = "conference"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    acronym: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(512))
    domain: Mapped[str] = mapped_column(String(64), index=True)
    subdomain_default: Mapped[str | None] = mapped_column(String(128), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(128), nullable=True)
    official_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    default_sources: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    editions: Mapped[list["ConferenceEdition"]] = relationship(
        back_populates="conference",
        cascade="all, delete-orphan",
    )
    papers: Mapped[list["Paper"]] = relationship(back_populates="conference")


class ConferenceEdition(Base):
    __tablename__ = "conference_edition"
    __table_args__ = (UniqueConstraint("conference_id", "year", name="uq_edition_conf_year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conference_id: Mapped[int] = mapped_column(ForeignKey("conference.id"), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    proceedings_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conference: Mapped[Conference] = relationship(back_populates="editions")
    papers: Mapped[list["Paper"]] = relationship(back_populates="edition")


class Paper(Base):
    __tablename__ = "paper"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(2048))
    title_key: Mapped[str] = mapped_column(String(2048), index=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    authors: Mapped[list[str]] = mapped_column(JSON, default=list)
    first_author_key: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    doi: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    paper_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    conference_id: Mapped[int] = mapped_column(ForeignKey("conference.id"), index=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("conference_edition.id"), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    domain: Mapped[str] = mapped_column(String(64), index=True)
    source_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    conference: Mapped[Conference] = relationship(back_populates="papers")
    edition: Mapped[ConferenceEdition] = relationship(back_populates="papers")
    source_records: Mapped[list["PaperSourceRecord"]] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list["PaperTag"]] = relationship(back_populates="paper", cascade="all, delete-orphan")


class PaperSourceRecord(Base):
    __tablename__ = "paper_source_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_paper_id: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    paper: Mapped[Paper] = relationship(back_populates="source_records")


class TaxonomyTag(Base):
    __tablename__ = "taxonomy_tag"
    __table_args__ = (UniqueConstraint("domain", "slug", name="uq_tag_domain_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(String(64), index=True)
    slug: Mapped[str] = mapped_column(String(128), index=True)
    label: Mapped[str] = mapped_column(String(256))

    papers: Mapped[list["PaperTag"]] = relationship(back_populates="tag")


class PaperTag(Base):
    __tablename__ = "paper_tag"
    __table_args__ = (UniqueConstraint("paper_id", "tag_id", "method", name="uq_paper_tag_method"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id"), index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("taxonomy_tag.id"), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    method: Mapped[str] = mapped_column(String(64), default="keyword_rule")

    paper: Mapped[Paper] = relationship(back_populates="tags")
    tag: Mapped[TaxonomyTag] = relationship(back_populates="papers")


class CrawlJob(Base):
    __tablename__ = "crawl_job"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="queued")
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    inserted_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

