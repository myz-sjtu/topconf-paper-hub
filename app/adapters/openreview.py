from typing import Any

import httpx

from app.adapters.base import RawPaperRecord, SourceAdapter
from app.core.config import settings
from app.schemas import ConferenceSeed


class OpenReviewAdapter(SourceAdapter):
    source_type = "openreview"
    endpoint = "https://api2.openreview.net/notes"

    async def fetch_papers(self, conference: ConferenceSeed, year: int) -> list[RawPaperRecord]:
        venue_id = self._venue_id(conference.acronym, year)
        params = {"content.venueid": venue_id, "limit": 1000}
        headers = {"User-Agent": settings.crawler_user_agent}
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, headers=headers) as client:
            response = await client.get(self.endpoint, params=params)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            payload = response.json()
        return [record for note in payload.get("notes", []) if (record := self._parse_note(note))]

    def _venue_id(self, acronym: str, year: int) -> str:
        normalized = acronym.upper()
        if normalized == "ICLR":
            return f"ICLR.cc/{year}/Conference"
        if normalized == "NEURIPS":
            return f"NeurIPS.cc/{year}/Conference"
        if normalized == "ICML":
            return f"ICML.cc/{year}/Conference"
        return f"{normalized}.cc/{year}/Conference"

    def _content_value(self, content: dict[str, Any], key: str) -> Any:
        value = content.get(key)
        if isinstance(value, dict) and "value" in value:
            return value["value"]
        return value

    def _parse_note(self, note: dict[str, Any]) -> RawPaperRecord | None:
        content = note.get("content") or {}
        title = (self._content_value(content, "title") or "").strip()
        if not title:
            return None

        authors = self._content_value(content, "authors") or []
        abstract = self._content_value(content, "abstract")
        forum = note.get("forum") or note.get("id")
        paper_url = f"https://openreview.net/forum?id={forum}" if forum else None
        pdf_url = f"https://openreview.net/pdf?id={forum}" if forum else None

        return RawPaperRecord(
            source_type=self.source_type,
            title=title,
            authors=authors if isinstance(authors, list) else [],
            abstract=abstract,
            paper_url=paper_url,
            pdf_url=pdf_url,
            source_url=paper_url,
            source_paper_id=forum,
            raw_payload=note,
        )

