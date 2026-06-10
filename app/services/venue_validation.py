import re
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

CONFERENCE_CONTAINER_TERMS = [
    "proceedings",
    "conference",
    "symposium",
]

META_RECORD_TITLE_PATTERNS = [
    r":\s*overview\.?$",
    r"^front\s+matter\b",
    r"^preface\b",
    r"^message\s+from\b",
    r"\bprogram\s+committee\b",
    r"\borganizing\s+committee\b",
]

SEARCH_BASED_SOURCES = {"acm_dl", "dblp", "openalex"}


def candidate_names(conference: ConferenceSeed) -> list[str]:
    return [conference.acronym, conference.full_name, *conference.aliases]


def has_excluded_proceedings_term(*values: str | None) -> bool:
    haystack = " ".join(value or "" for value in values).lower()
    return any(re.search(rf"\b{re.escape(term)}\b", haystack) for term in EXCLUDED_PROCEEDINGS_TERMS)


def looks_like_proceedings_volume(title: str | None, authors: list[str] | None = None) -> bool:
    normalized = (title or "").strip().lower()
    return normalized.startswith("proceedings of ")


def looks_like_meta_record(title: str | None) -> bool:
    normalized = (title or "").strip().lower()
    return any(re.search(pattern, normalized) for pattern in META_RECORD_TITLE_PATTERNS)


def is_dblp_hit_for_conference(
    hit: dict[str, Any],
    conference: ConferenceSeed,
    *,
    expected_year: int | None = None,
) -> bool:
    info = hit.get("info", {})
    key = str(info.get("key") or "").lower()
    title = str(info.get("title") or "")
    venue = str(info.get("venue") or "")
    publication_type = str(info.get("type") or "").lower()
    authors = _dblp_authors(info)
    year = expected_year or _int_or_none(hit.get("queried_year"))

    if publication_type == "editorship":
        return False
    if looks_like_meta_record(title):
        return False
    if year is not None and _int_or_none(info.get("year")) != year:
        return False

    venue_keys = DBLP_VENUE_KEYS.get(conference.acronym, [conference.acronym.lower()])
    if not any(key.startswith(f"conf/{venue_key}/") for venue_key in venue_keys):
        return False
    if looks_like_proceedings_volume(title, authors):
        return False
    return not has_excluded_proceedings_term(title, venue)


def is_openalex_work_for_conference(
    item: dict[str, Any],
    conference: ConferenceSeed,
    *,
    expected_year: int | None = None,
) -> bool:
    title = str(item.get("title") or "")
    venue_names = openalex_venue_names(item)
    year = expected_year or _int_or_none(item.get("queried_year"))
    if year is not None and _openalex_year(item) != year:
        return False
    if looks_like_meta_record(title):
        return False
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


def is_crossref_item_for_conference(
    item: dict[str, Any],
    conference: ConferenceSeed,
    *,
    expected_year: int | None = None,
) -> bool:
    title = _first_text(item.get("title")) or ""
    authors = item.get("author") or []
    year = expected_year or _int_or_none(item.get("queried_year"))
    if year is not None and _crossref_year(item) != year:
        return False
    if looks_like_meta_record(title):
        return False
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
    if not any(term in venue_haystack for term in CONFERENCE_CONTAINER_TERMS):
        return False

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


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _openalex_year(item: dict[str, Any]) -> int | None:
    return _int_or_none(item.get("publication_year")) or _int_or_none(str(item.get("publication_date") or "")[:4])


def _crossref_year(item: dict[str, Any]) -> int | None:
    for key in ["published-online", "published-print", "published", "issued"]:
        date_parts = item.get(key, {}).get("date-parts", [])
        if date_parts and date_parts[0]:
            return _int_or_none(date_parts[0][0])
    return None
