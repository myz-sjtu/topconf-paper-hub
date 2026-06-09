from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.schemas import ConferenceSeed


@dataclass
class RawPaperRecord:
    source_type: str
    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    doi: str | None = None
    paper_url: str | None = None
    pdf_url: str | None = None
    publication_date: date | None = None
    source_url: str | None = None
    source_paper_id: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


class SourceAdapter(ABC):
    source_type: str

    @abstractmethod
    async def fetch_papers(self, conference: ConferenceSeed, year: int) -> list[RawPaperRecord]:
        """Fetch metadata records for one conference edition."""

