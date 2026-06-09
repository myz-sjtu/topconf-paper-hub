from app.schemas import CrawlPreviewRequest
from app.services.conference_registry import registry


def test_registry_loads_seed_conferences() -> None:
    conferences = registry.list(active=True)
    acronyms = {conference.acronym for conference in conferences}
    assert {"SIGCOMM", "ISCA", "NeurIPS", "CVPR"}.issubset(acronyms)


def test_registry_matches_alias_and_filters_domain() -> None:
    assert registry.get("NIPS").acronym == "NeurIPS"  # type: ignore[union-attr]
    ai_conferences = registry.list(domain="ai", active=True)
    assert ai_conferences
    assert all(conference.domain == "ai" for conference in ai_conferences)


def test_crawl_preview_uses_default_year_window() -> None:
    items = registry.build_crawl_preview(
        CrawlPreviewRequest(conferences=["SIGCOMM"], sources=["dblp"])
    )
    assert len(items) == 5
    assert {item.conference for item in items} == {"SIGCOMM"}
    assert {item.source_type for item in items} == {"dblp"}

