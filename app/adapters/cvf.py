import re

import httpx

from app.adapters.base import RawPaperRecord, SourceAdapter
from app.core.config import settings
from app.schemas import ConferenceSeed


class CVFAdapter(SourceAdapter):
    source_type = "cvf"

    async def fetch_papers(self, conference: ConferenceSeed, year: int) -> list[RawPaperRecord]:
        venue = conference.acronym.upper()
        if venue not in {"CVPR", "ICCV"}:
            return []

        headers = {"User-Agent": settings.crawler_user_agent}
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, headers=headers) as client:
            for url in self._candidate_urls(venue, year):
                response = await client.get(url)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                records = self._parse_listing(response.text, url)
                if records:
                    return records
        return []

    def _candidate_urls(self, venue: str, year: int) -> list[str]:
        base = f"https://openaccess.thecvf.com/{venue}{year}"
        return [
            base,
            f"{base}?day=all",
            f"{base}.py",
            f"{base}.py?day=all",
        ]

    def _parse_listing(self, html: str, base_url: str) -> list[RawPaperRecord]:
        records: list[RawPaperRecord] = []
        paper_pattern = re.compile(r'<a href="(?P<href>[^"]+\.html)">(?P<title>.*?)</a>', re.S)
        for match in paper_pattern.finditer(html):
            title = re.sub(r"\s+", " ", match.group("title")).strip()
            href = match.group("href")
            if "content/CVPR" not in href and "content/ICCV" not in href:
                continue
            paper_url = f"https://openaccess.thecvf.com/{href.lstrip('/')}"
            pdf_url = paper_url.replace("/html/", "/papers/").replace(".html", ".pdf")
            records.append(
                RawPaperRecord(
                    source_type=self.source_type,
                    title=title,
                    paper_url=paper_url,
                    pdf_url=pdf_url,
                    source_url=base_url,
                    source_paper_id=href,
                    raw_payload={"href": href},
                )
            )
        return records
