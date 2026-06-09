from app.adapters.acm_dl import ACMDLAdapter
from app.schemas import ConferenceSeed


def test_acm_dl_parse_crossref_item() -> None:
    adapter = ACMDLAdapter()
    conference = ConferenceSeed(
        acronym="SIGCOMM",
        full_name="ACM SIGCOMM Conference",
        domain="network",
        aliases=["ACM SIGCOMM"],
    )
    record = adapter._parse_item(
        {
            "DOI": "10.1145/1234567.1234568",
            "title": ["Example ACM Paper"],
            "author": [{"given": "Ada", "family": "Lovelace"}],
            "container-title": ["Proceedings of the ACM SIGCOMM Conference"],
            "published-online": {"date-parts": [[2025, 8, 1]]},
            "abstract": "<jats:p>This paper studies networks.</jats:p>",
        },
        conference,
        2025,
    )

    assert record is not None
    assert record.source_type == "acm_dl"
    assert record.title == "Example ACM Paper"
    assert record.authors == ["Ada Lovelace"]
    assert record.doi == "10.1145/1234567.1234568"
    assert record.paper_url == "https://dl.acm.org/doi/10.1145/1234567.1234568"
    assert record.abstract == "This paper studies networks."

