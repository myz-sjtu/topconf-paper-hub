from datetime import date
from typing import Any

import httpx

from app.adapters.base import RawPaperRecord, SourceAdapter
from app.core.config import settings
from app.schemas import ConferenceSeed
from app.services.venue_validation import is_crossref_item_for_conference


class ACMDLAdapter(SourceAdapter):
    """Metadata-only ACM Digital Library adapter.

    ACM DL does not need to be scraped for this project. Crossref exposes DOI
    metadata for ACM records, and the DOI landing URL points back to ACM DL.
    """

    source_type = "acm_dl"
    endpoint = "https://api.crossref.org/works"
    doi_prefix = "10.1145"

    async def fetch_papers(self, conference: ConferenceSeed, year: int) -> list[RawPaperRecord]:
        headers = {"User-Agent": settings.crawler_user_agent}
        queries = [conference.acronym, conference.full_name]
        records_by_doi: dict[str, RawPaperRecord] = {}

        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, headers=headers) as client:
            for query in queries:
                params = {
                    "query.container-title": query,
                    "filter": (
                        f"from-pub-date:{year}-01-01,"
                        f"until-pub-date:{year}-12-31,"
                        f"prefix:{self.doi_prefix}"
                    ),
                    "rows": 1000,
                    "select": "DOI,title,author,container-title,event,published-print,published-online,URL,abstract",
                }
                response = await client.get(self.endpoint, params=params)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("message", {}).get("items", []):
                    record = self._parse_item(item, conference, year)
                    if record and record.doi:
                        records_by_doi[record.doi] = record

        return list(records_by_doi.values())

    def _parse_item(
        self,
        item: dict[str, Any],
        conference: ConferenceSeed,
        year: int,
    ) -> RawPaperRecord | None:
        title = self._first_text(item.get("title"))
        if not title:
            return None

        if not is_crossref_item_for_conference(item, conference):
            return None

        doi = str(item.get("DOI") or "").strip().lower()
        if not doi.startswith(self.doi_prefix):
            return None

        authors = []
        for author in item.get("author", []) or []:
            given = author.get("given") or ""
            family = author.get("family") or ""
            name = " ".join(part for part in [given, family] if part).strip()
            if name:
                authors.append(name)

        publication_date = self._published_date(item)
        acm_url = f"https://dl.acm.org/doi/{doi}"

        return RawPaperRecord(
            source_type=self.source_type,
            title=title,
            authors=authors,
            abstract=self._clean_abstract(item.get("abstract")),
            doi=doi,
            paper_url=acm_url,
            publication_date=publication_date,
            source_url=acm_url,
            source_paper_id=doi,
            raw_payload={**item, "venue_validated": True},
        )

    def _first_text(self, value: Any) -> str | None:
        if isinstance(value, list) and value:
            return str(value[0]).strip() or None
        if isinstance(value, str):
            return value.strip() or None
        return None

    def _published_date(self, item: dict[str, Any]) -> date | None:
        for key in ["published-online", "published-print"]:
            date_parts = item.get(key, {}).get("date-parts", [])
            if not date_parts or not date_parts[0]:
                continue
            parts = list(date_parts[0])
            while len(parts) < 3:
                parts.append(1)
            try:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            except ValueError:
                continue
        return None

    def _clean_abstract(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        cleaned = (
            value.replace("<jats:p>", "")
            .replace("</jats:p>", "")
            .replace("<p>", "")
            .replace("</p>", "")
            .strip()
        )
        return cleaned or None
