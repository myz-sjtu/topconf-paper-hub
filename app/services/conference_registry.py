from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path

import yaml

from app.core.config import settings
from app.schemas import ConferenceSeed, CrawlJobPreview, CrawlPreviewRequest


@dataclass(frozen=True)
class ConferenceRegistryPayload:
    version: int
    domains: dict
    conferences: list[ConferenceSeed]


class ConferenceRegistry:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or settings.conference_config_path)

    @cached_property
    def payload(self) -> ConferenceRegistryPayload:
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        conferences = [ConferenceSeed(**item) for item in raw.get("conferences", [])]
        return ConferenceRegistryPayload(
            version=int(raw.get("version", 1)),
            domains=raw.get("domains", {}),
            conferences=conferences,
        )

    @property
    def conferences(self) -> list[ConferenceSeed]:
        return self.payload.conferences

    def list(self, domain: str | None = None, active: bool | None = None) -> list[ConferenceSeed]:
        items = self.conferences
        if domain:
            items = [item for item in items if item.domain.lower() == domain.lower()]
        if active is not None:
            items = [item for item in items if item.active is active]
        return sorted(items, key=lambda item: (item.domain, item.acronym.lower()))

    def get(self, acronym_or_alias: str) -> ConferenceSeed | None:
        needle = acronym_or_alias.lower()
        for item in self.conferences:
            candidates = [item.acronym, *item.aliases]
            if any(candidate.lower() == needle for candidate in candidates):
                return item
        return None

    def default_years(self) -> list[int]:
        current_year = datetime.utcnow().year
        return list(range(current_year - settings.default_year_window + 1, current_year + 1))

    def build_crawl_preview(self, request: CrawlPreviewRequest) -> list[CrawlJobPreview]:
        if request.conferences:
            conferences = [self.get(item) for item in request.conferences]
            missing = [name for name, item in zip(request.conferences, conferences, strict=False) if item is None]
            if missing:
                raise ValueError(f"Unknown conferences: {', '.join(missing)}")
            selected = [item for item in conferences if item is not None]
        else:
            selected = self.list(domain=request.domain, active=True)

        if request.domain:
            selected = [item for item in selected if item.domain.lower() == request.domain.lower()]

        years = request.years or self.default_years()
        items: list[CrawlJobPreview] = []
        for conference in selected:
            source_types = request.sources or conference.default_sources
            for year in years:
                for source_type in source_types:
                    items.append(
                        CrawlJobPreview(
                            conference=conference.acronym,
                            domain=conference.domain,
                            year=year,
                            source_type=source_type,
                            official_url=conference.official_url,
                        )
                    )
        return items


registry = ConferenceRegistry()
