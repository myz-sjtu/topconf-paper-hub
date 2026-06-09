from app.schemas import ConferenceSeed
from app.services.classification import classify_domain_by_conference, infer_subtopics
from app.services.dedup import build_identity, is_probably_same, normalize_doi, normalize_title


def test_normalizers() -> None:
    assert normalize_doi("https://doi.org/10.1145/ABC") == "10.1145/abc"
    assert normalize_title("A Fast, Fast! Network.") == "a fast fast network"


def test_identity_matches_by_doi_url_and_title_author() -> None:
    left = build_identity(
        title="Fast Datacenter Transport",
        year=2025,
        authors=["Ada Lovelace"],
        doi="10.1/ABC",
        paper_url="https://example.com/a",
    )
    assert is_probably_same(left, build_identity(title="Other", year=2024, doi="10.1/abc"))
    assert is_probably_same(
        left,
        build_identity(
            title="Fast Datacenter Transport",
            year=2025,
            authors=["Ada Lovelace"],
        ),
    )


def test_classification_rules() -> None:
    conference = ConferenceSeed(
        acronym="SIGCOMM",
        full_name="ACM SIGCOMM Conference",
        domain="network",
    )
    assert classify_domain_by_conference(conference) == "network"
    tags = infer_subtopics("network", ["RDMA congestion control for datacenter networks"])
    assert tags[0][0] == "datacenter"

