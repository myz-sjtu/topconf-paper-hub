from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConferenceSeed(BaseModel):
    acronym: str
    full_name: str
    domain: str
    subdomain_default: str | None = None
    publisher: str | None = None
    official_url: str | None = None
    aliases: list[str] = Field(default_factory=list)
    default_sources: list[str] = Field(default_factory=list)
    active: bool = True


class ConferenceRead(BaseModel):
    id: int
    acronym: str
    full_name: str
    domain: str
    subdomain_default: str | None = None
    publisher: str | None = None
    official_url: str | None = None
    aliases: list[str] = Field(default_factory=list)
    default_sources: list[str] = Field(default_factory=list)
    active: bool

    model_config = ConfigDict(from_attributes=True)


class ConferenceEditionRead(BaseModel):
    id: int
    conference_id: int
    conference: str | None = None
    year: int
    start_date: date | None = None
    end_date: date | None = None
    location: str | None = None
    proceedings_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RawPaperPayload(BaseModel):
    source_type: str
    source_url: str | None = None
    source_paper_id: str | None = None
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    doi: str | None = None
    paper_url: str | None = None
    pdf_url: str | None = None
    publication_date: date | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class CrawlJobPreview(BaseModel):
    conference: str
    domain: str
    year: int
    source_type: str
    official_url: str | None = None


class CrawlPreviewRequest(BaseModel):
    domain: str | None = Field(default=None, description="network / architecture / ai")
    conferences: list[str] | None = Field(default=None, description="Conference acronyms or aliases")
    years: list[int] | None = Field(default=None, description="Defaults to the latest configured year window")
    sources: list[str] | None = Field(default=None, description="Override conference default sources")


class CrawlPreviewResponse(BaseModel):
    total: int
    items: list[CrawlJobPreview]


class CrawlRunRequest(CrawlPreviewRequest):
    async_run: bool = Field(default=True, description="Run in a FastAPI background task when true")


class CrawlJobRead(BaseModel):
    id: str
    status: str
    total_tasks: int
    completed_tasks: int
    inserted_count: int
    updated_count: int
    error: str | None = None
    requested_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PaperSourceRecordRead(BaseModel):
    id: int
    source_type: str
    source_url: str | None = None
    source_paper_id: str | None = None
    fetched_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaperTagRead(BaseModel):
    domain: str
    slug: str
    label: str
    score: float
    method: str


class PaperRead(BaseModel):
    id: int
    title: str
    authors: list[str]
    abstract: str | None = None
    doi: str | None = None
    paper_url: str | None = None
    pdf_url: str | None = None
    publication_date: date | None = None
    conference: str
    year: int
    domain: str
    edition_start_date: date | None = None
    edition_end_date: date | None = None
    tags: list[PaperTagRead] = Field(default_factory=list)
    source_records: list[PaperSourceRecordRead] = Field(default_factory=list)


class PaperListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[PaperRead]

