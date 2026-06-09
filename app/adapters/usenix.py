import re

import httpx

from app.adapters.base import RawPaperRecord, SourceAdapter
from app.core.config import settings
from app.schemas import ConferenceSeed


class USENIXAdapter(SourceAdapter):
    source_type = "usenix"

    async def fetch_papers(self, conference: ConferenceSeed, year: int) -> list[RawPaperRecord]:
        slug = conference.acronym.lower()
        url = f"https://www.usenix.org/conference/{slug}{year}/technical-sessions"
        headers = {"User-Agent": settings.crawler_user_agent}
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, headers=headers) as client:
            response = await client.get(url)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            html = response.text
        return self._parse_listing(html, url)

    def _parse_listing(self, html: str, base_url: str) -> list[RawPaperRecord]:
        records: list[RawPaperRecord] = []
        pattern = re.compile(
            r'<a[^>]+href="(?P<href>/conference/[^"]+/presentation/[^"]+)"[^>]*>(?P<title>.*?)</a>',
            re.S,
        )
        seen: set[str] = set()
        for match in pattern.finditer(html):
            href = match.group("href")
            if href in seen:
                continue
            seen.add(href)
            title = re.sub(r"<[^>]+>", "", match.group("title"))
            title = re.sub(r"\s+", " ", title).strip()
            if not title:
                continue
            paper_url = f"https://www.usenix.org{href}"
            records.append(
                RawPaperRecord(
                    source_type=self.source_type,
                    title=title,
                    paper_url=paper_url,
                    source_url=base_url,
                    source_paper_id=href.rsplit("/", 1)[-1],
                    raw_payload={"href": href},
                )
            )
        return records

