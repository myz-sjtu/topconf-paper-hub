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


def test_crossref_rejects_workshop_item() -> None:
    conference = ConferenceSeed(acronym="KDD", full_name="ACM SIGKDD Conference", domain="ai")
    item = {
        "title": ["KDD 2025 Workshop on Prompt Optimization"],
        "container-title": ["Proceedings of the 31st ACM SIGKDD Conference"],
        "author": [{"given": "Ada", "family": "Lovelace"}],
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

