from datetime import date
from typing import Any
from urllib.parse import quote

import httpx

from app.adapters.base import RawPaperRecord, SourceAdapter
from app.core.config import settings
from app.schemas import ConferenceSeed
from app.services.venue_validation import is_openalex_work_for_conference, openalex_venue_names


class OpenAlexAdapter(SourceAdapter):
    source_type = "openalex"
    endpoint = "https://api.openalex.org/works"

    async def fetch_papers(self, conference: ConferenceSeed, year: int) -> list[RawPaperRecord]:
        params = {
            "search": f"{conference.full_name} {conference.acronym}",
            "filter": f"from_publication_date:{year}-01-01,to_publication_date:{year}-12-31",
            "per-page": 200,
        }
        headers = {"User-Agent": settings.crawler_user_agent}
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, headers=headers) as client:
            response = await client.get(self.endpoint, params=params)
            response.raise_for_status()
            payload = response.json()

        return [
            record
            for item in payload.get("results", [])
            if is_openalex_work_for_conference(item, conference)
            and (record := self._parse_work(item, venue_validated=True))
        ]

    async def fetch_by_dois(self, dois: list[str]) -> list[RawPaperRecord]:
        normalized_dois = [self._doi_url(doi) for doi in dois if doi]
        if not normalized_dois:
            return []

        params = {
            "filter": "doi:" + "|".join(normalized_dois),
            "per-page": min(len(normalized_dois), 50),
        }
        headers = {"User-Agent": settings.crawler_user_agent}
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, headers=headers) as client:
            response = await client.get(self.endpoint, params=params)
            response.raise_for_status()
            payload = response.json()

        return [
            record
            for item in payload.get("results", [])
            if (record := self._parse_work(item, venue_validated=False))
        ]

    def _doi_url(self, doi: str) -> str:
        stripped = doi.strip()
        if stripped.startswith("http://doi.org/") or stripped.startswith("https://doi.org/"):
            return stripped.replace("http://doi.org/", "https://doi.org/", 1)
        return f"https://doi.org/{quote(stripped, safe='/:')}"

    def _abstract_from_inverted_index(self, item: dict[str, Any]) -> str | None:
        inverted_index = item.get("abstract_inverted_index")
        if not isinstance(inverted_index, dict):
            return None

        words: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            if not isinstance(word, str) or not isinstance(positions, list):
                continue
            for position in positions:
                if isinstance(position, int):
                    words.append((position, word))

        if not words:
            return None
        return " ".join(word for _, word in sorted(words)).strip() or None

    def _parse_work(self, item: dict[str, Any], *, venue_validated: bool) -> RawPaperRecord | None:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        authors = [
            authorship.get("author", {}).get("display_name", "")
            for authorship in item.get("authorships", [])
        ]
        doi = item.get("doi")
        if isinstance(doi, str):
            doi = doi.removeprefix("https://doi.org/")

        publication_date = None
        if item.get("publication_date"):
            publication_date = date.fromisoformat(item["publication_date"])

        primary_location = item.get("primary_location") or {}
        pdf_url = None
        source_url = item.get("id")
        if primary_location.get("pdf_url"):
            pdf_url = primary_location.get("pdf_url")
        if primary_location.get("landing_page_url"):
            source_url = primary_location.get("landing_page_url")

        return RawPaperRecord(
            source_type=self.source_type,
            title=title,
            authors=[author for author in authors if author],
            abstract=self._abstract_from_inverted_index(item),
            doi=doi,
            paper_url=source_url,
            pdf_url=pdf_url,
            publication_date=publication_date,
            source_url=source_url,
            source_paper_id=item.get("id"),
            raw_payload={
                **item,
                "venue_names": openalex_venue_names(item),
                "venue_validated": venue_validated,
            },
        )
