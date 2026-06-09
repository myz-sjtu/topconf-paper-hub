import re
from dataclasses import dataclass

_TITLE_PUNCT_RE = re.compile(r"[^a-z0-9]+")
_SPACE_RE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    lowered = title.lower().strip()
    return _SPACE_RE.sub(" ", _TITLE_PUNCT_RE.sub(" ", lowered)).strip()


def normalize_author(author: str | None) -> str | None:
    if not author:
        return None
    normalized = _SPACE_RE.sub(" ", author.lower().strip())
    return normalized or None


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    normalized = doi.strip().lower()
    normalized = normalized.removeprefix("https://doi.org/")
    normalized = normalized.removeprefix("http://doi.org/")
    normalized = normalized.removeprefix("doi:")
    return normalized.strip() or None


@dataclass(frozen=True)
class PaperIdentity:
    title_key: str
    year: int | None = None
    first_author_key: str | None = None
    doi: str | None = None
    paper_url: str | None = None
    pdf_url: str | None = None
    source_type: str | None = None
    source_paper_id: str | None = None


def build_identity(
    *,
    title: str,
    year: int | None,
    authors: list[str] | None = None,
    doi: str | None = None,
    paper_url: str | None = None,
    pdf_url: str | None = None,
    source_type: str | None = None,
    source_paper_id: str | None = None,
) -> PaperIdentity:
    first_author = normalize_author(authors[0]) if authors else None
    return PaperIdentity(
        title_key=normalize_title(title),
        year=year,
        first_author_key=first_author,
        doi=normalize_doi(doi),
        paper_url=paper_url,
        pdf_url=pdf_url,
        source_type=source_type,
        source_paper_id=source_paper_id,
    )


def is_probably_same(left: PaperIdentity, right: PaperIdentity) -> bool:
    if left.doi and right.doi and left.doi == right.doi:
        return True
    if left.paper_url and right.paper_url and left.paper_url == right.paper_url:
        return True
    if left.pdf_url and right.pdf_url and left.pdf_url == right.pdf_url:
        return True
    if (
        left.source_type
        and right.source_type
        and left.source_paper_id
        and right.source_paper_id
        and left.source_type == right.source_type
        and left.source_paper_id == right.source_paper_id
    ):
        return True
    if left.title_key == right.title_key and left.year == right.year:
        if not left.first_author_key or not right.first_author_key:
            return True
        return left.first_author_key == right.first_author_key
    return False

