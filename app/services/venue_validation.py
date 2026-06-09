from typing import Any

from app.schemas import ConferenceSeed

DBLP_VENUE_KEYS: dict[str, list[str]] = {
    "AAAI": ["aaai"],
    "ACL": ["acl"],
    "ASPLOS": ["asplos"],
    "COLT": ["colt"],
    "CoNEXT": ["conext"],
    "CVPR": ["cvpr"],
    "ECCV": ["eccv"],
    "EMNLP": ["emnlp"],
    "EuroSys": ["eurosys"],
    "FAST": ["fast"],
    "HPCA": ["hpca"],
    "ICCV": ["iccv"],
    "ICLR": ["iclr"],
    "ICML": ["icml"],
    "IJCAI": ["ijcai"],
    "IMC": ["imc"],
    "INFOCOM": ["infocom"],
    "ISCA": ["isca"],
    "KDD": ["kdd"],
    "MICRO": ["micro"],
    "MobiCom": ["mobicom"],
    "NAACL": ["naacl"],
    "NSDI": ["nsdi"],
    "NeurIPS": ["nips", "neurips"],
    "SIGCOMM": ["sigcomm"],
    "SIGMETRICS": ["sigmetrics"],
}

EXCLUDED_PROCEEDINGS_TERMS = [
    "artifact",
    "challenge",
    "companion",
    "demo",
    "doctoral",
    "industry day",
    "panel",
    "poster",
    "student research",
    "tutorial",
    "workshop",
]

SEARCH_BASED_SOURCES = {"acm_dl", "dblp", "openalex"}


def candidate_names(conference: ConferenceSeed) -> list[str]:
    return [conference.acronym, conference.full_name, *conference.aliases]


def has_excluded_proceedings_term(*values: str | None) -> bool:
    haystack = " ".join(value or "" for value in values).lower()
    return any(term in haystack for term in EXCLUDED_PROCEEDINGS_TERMS)


def looks_like_proceedings_volume(title: str | None, authors: list[str] | None = None) -> bool:
    normalized = (title or "").strip().lower()
    return normalized.startswith("proceedings of ")


def is_dblp_hit_for_conference(hit: dict[str, Any], conference: ConferenceSeed) -> bool:
    info = hit.get("info", {})
    key = str(info.get("key") or "").lower()
    title = str(info.get("title") or "")
    venue = str(info.get("venue") or "")
    authors = _dblp_authors(info)

    venue_keys = DBLP_VENUE_KEYS.get(conference.acronym, [conference.acronym.lower()])
    if not any(key.startswith(f"conf/{venue_key}/") for venue_key in venue_keys):
        return False
    if looks_like_proceedings_volume(title, authors):
        return False
    return not has_excluded_proceedings_term(title, venue)


def is_openalex_work_for_conference(item: dict[str, Any], conference: ConferenceSeed) -> bool:
    title = str(item.get("title") or "")
    venue_names = openalex_venue_names(item)
    if looks_like_proceedings_volume(title, _openalex_authors(item)):
        return False
    if has_excluded_proceedings_term(title, *venue_names):
        return False

    venue_haystack = " ".join(venue_names).lower()
    return any(candidate.lower() in venue_haystack for candidate in candidate_names(conference))


def openalex_venue_names(item: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for location in [item.get("primary_location"), *(item.get("locations") or [])]:
        if not isinstance(location, dict):
            continue
        source = location.get("source") or {}
        display_name = source.get("display_name")
        if display_name:
            names.append(str(display_name))
    return names


def is_crossref_item_for_conference(item: dict[str, Any], conference: ConferenceSeed) -> bool:
    title = _first_text(item.get("title")) or ""
    authors = item.get("author") or []
    if looks_like_proceedings_volume(title, authors):
        return False

    venue_parts: list[str] = []
    for key in ["container-title", "event"]:
        value = item.get(key)
        if isinstance(value, list):
            venue_parts.extend(str(part) for part in value)
        elif value:
            venue_parts.append(str(value))

    if has_excluded_proceedings_term(title, *venue_parts):
        return False

    venue_haystack = " ".join(venue_parts).lower()
    return any(candidate.lower() in venue_haystack for candidate in candidate_names(conference))


def raw_record_passed_venue_validation(source_type: str, raw_payload: dict[str, Any]) -> bool:
    if source_type not in SEARCH_BASED_SOURCES:
        return True
    return raw_payload.get("venue_validated") is True


def _dblp_authors(info: dict[str, Any]) -> list[str]:
    authors_payload = info.get("authors", {}).get("author", [])
    if isinstance(authors_payload, dict):
        return [str(authors_payload.get("text", ""))]
    if isinstance(authors_payload, list):
        return [
            str(item.get("text", item)) if isinstance(item, dict) else str(item)
            for item in authors_payload
        ]
    return []


def _openalex_authors(item: dict[str, Any]) -> list[str]:
    return [
        str(authorship.get("author", {}).get("display_name", ""))
        for authorship in item.get("authorships", [])
    ]


def _first_text(value: Any) -> str | None:
    if isinstance(value, list) and value:
        return str(value[0]).strip() or None
    if isinstance(value, str):
        return value.strip() or None
    return None
