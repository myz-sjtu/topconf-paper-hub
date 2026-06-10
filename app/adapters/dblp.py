import html
from typing import Any

import httpx

from app.adapters.base import RawPaperRecord, SourceAdapter
from app.core.config import settings
from app.schemas import ConferenceSeed
from app.services.venue_validation import is_dblp_hit_for_conference


class DBLPAdapter(SourceAdapter):
    source_type = "dblp"
    endpoint = "https://dblp.org/search/publ/api"

    async def fetch_papers(self, conference: ConferenceSeed, year: int) -> list[RawPaperRecord]:
        query = f"{conference.acronym} {year}"
        params = {"q": query, "format": "json", "h": 1000}
        headers = {"User-Agent": settings.crawler_user_agent}
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, headers=headers) as client:
            response = await client.get(self.endpoint, params=params)
            response.raise_for_status()
            payload = response.json()

        hits = payload.get("result", {}).get("hits", {}).get("hit", [])
        records = [
            record
            for hit in hits
            if is_dblp_hit_for_conference(hit, conference, expected_year=year)
            and (record := self._parse_hit(hit, year))
        ]
        return records

    def _parse_hit(self, hit: dict[str, Any], year: int | None = None) -> RawPaperRecord | None:
        info = hit.get("info", {})
        title = html.unescape(str(info.get("title", ""))).strip().rstrip(".")
        if not title:
            return None

        authors_payload = info.get("authors", {}).get("author", [])
        if isinstance(authors_payload, dict):
            authors = [authors_payload.get("text", "")]
        elif isinstance(authors_payload, list):
            authors = [
                str(item.get("text", item)) if isinstance(item, dict) else str(item)
                for item in authors_payload
            ]
        else:
            authors = []

        source_url = info.get("url")
        return RawPaperRecord(
            source_type=self.source_type,
            title=title,
            authors=[author for author in authors if author],
            doi=info.get("doi"),
            paper_url=source_url,
            source_url=source_url,
            source_paper_id=info.get("key") or hit.get("@id"),
            raw_payload={**hit, "queried_year": year, "venue_validated": True},
        )
