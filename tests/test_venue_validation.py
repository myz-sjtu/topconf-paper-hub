from app.schemas import ConferenceSeed
from app.services.venue_validation import (
    is_crossref_item_for_conference,
    is_dblp_hit_for_conference,
    is_openalex_work_for_conference,
)


def test_dblp_rejects_colocated_workshop() -> None:
    conference = ConferenceSeed(acronym="SIGCOMM", full_name="ACM SIGCOMM Conference", domain="network")
    hit = {
        "info": {
            "key": "conf/ebpf/KimH25",
            "title": "A Memory Pool Allocator for eBPF Applications",
            "venue": "eBPF",
            "authors": {"author": [{"text": "Ada Lovelace"}]},
        }
    }

    assert not is_dblp_hit_for_conference(hit, conference)


def test_dblp_accepts_exact_main_venue() -> None:
    conference = ConferenceSeed(acronym="SIGCOMM", full_name="ACM SIGCOMM Conference", domain="network")
    hit = {
        "info": {
            "key": "conf/sigcomm/Example25",
            "title": "Main Conference Paper",
            "venue": "SIGCOMM",
            "authors": {"author": [{"text": "Ada Lovelace"}]},
        }
    }

    assert is_dblp_hit_for_conference(hit, conference)


def test_dblp_rejects_editorship_volume() -> None:
    conference = ConferenceSeed(
        acronym="NSDI",
        full_name="USENIX Symposium on Networked Systems Design and Implementation",
        domain="network",
    )
    hit = {
        "info": {
            "key": "conf/nsdi/2026",
            "title": "23rd USENIX Symposium on Networked Systems Design and Implementation, NSDI 2026",
            "venue": "NSDI",
            "type": "Editorship",
            "authors": {"author": [{"text": "Ada Lovelace"}]},
        }
    }

    assert not is_dblp_hit_for_conference(hit, conference)


def test_dblp_rejects_wrong_publication_year() -> None:
    conference = ConferenceSeed(acronym="ACL", full_name="Association for Computational Linguistics", domain="ai")
    hit = {
        "queried_year": 2022,
        "info": {
            "key": "conf/acl/Example25",
            "title": "A 2025 ACL Paper Returned By A 2022 Search",
            "venue": "ACL",
            "year": "2025",
            "authors": {"author": [{"text": "Ada Lovelace"}]},
        },
    }

    assert not is_dblp_hit_for_conference(hit, conference)


def test_dblp_rejects_track_overview_meta_record() -> None:
    conference = ConferenceSeed(acronym="ACL", full_name="Association for Computational Linguistics", domain="ai")
    hit = {
        "queried_year": 2025,
        "info": {
            "key": "conf/acl/X25e",
            "title": "ACL 2025 Industry Track: Overview.",
            "venue": "ACL",
            "year": "2025",
            "authors": {"author": [{"text": "Ada Lovelace"}]},
        },
    }

    assert not is_dblp_hit_for_conference(hit, conference)


def test_crossref_rejects_workshop_item() -> None:
    conference = ConferenceSeed(acronym="KDD", full_name="ACM SIGKDD Conference", domain="ai")
    item = {
        "title": ["KDD 2025 Workshop on Prompt Optimization"],
        "container-title": ["Proceedings of the 31st ACM SIGKDD Conference"],
        "author": [{"given": "Ada", "family": "Lovelace"}],
    }

    assert not is_crossref_item_for_conference(item, conference)


def test_crossref_rejects_wrong_publication_year() -> None:
    conference = ConferenceSeed(acronym="SIGCOMM", full_name="ACM SIGCOMM Conference", domain="network")
    item = {
        "queried_year": 2025,
        "title": ["Example ACM Paper"],
        "container-title": ["Proceedings of the ACM SIGCOMM Conference"],
        "published-online": {"date-parts": [[2024, 8, 1]]},
    }

    assert not is_crossref_item_for_conference(item, conference)


def test_crossref_rejects_sigcomm_review_issue() -> None:
    conference = ConferenceSeed(acronym="SIGCOMM", full_name="ACM SIGCOMM Conference", domain="network")
    item = {
        "title": ["The April 2026 Issue"],
        "container-title": ["ACM SIGCOMM Computer Communication Review"],
        "author": [{"given": "Robert", "family": "Soule"}],
    }

    assert not is_crossref_item_for_conference(item, conference)


def test_openalex_rejects_title_only_acronym_match() -> None:
    conference = ConferenceSeed(acronym="KDD", full_name="ACM SIGKDD Conference", domain="ai")
    item = {
        "title": "Mobile application based on KDD to predict high-crime areas",
        "primary_location": {"source": {"display_name": "Frontiers in Computer Science"}},
        "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
    }

    assert not is_openalex_work_for_conference(item, conference)


def test_openalex_rejects_wrong_publication_year() -> None:
    conference = ConferenceSeed(acronym="KDD", full_name="ACM SIGKDD Conference", domain="ai")
    item = {
        "queried_year": 2025,
        "title": "Accepted Conference Paper",
        "publication_year": 2024,
        "primary_location": {"source": {"display_name": "Proceedings of the ACM SIGKDD Conference"}},
        "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
    }

    assert not is_openalex_work_for_conference(item, conference)
