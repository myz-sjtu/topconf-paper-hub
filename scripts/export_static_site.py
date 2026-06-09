from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Conference, Paper, PaperTag
from app.db.session import SessionLocal, init_db
from app.services.conference_registry import registry
from app.services.ingestion_pipeline import seed_conferences, seed_taxonomy


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
PUBLIC_DATA_DIR = DOCS_DIR / "public" / "data"
CONFERENCE_DIR = DOCS_DIR / "conferences"
YEAR_DIR = DOCS_DIR / "years"
DOMAIN_DIR = DOCS_DIR / "domains"
VITEPRESS_DIR = DOCS_DIR / ".vitepress"

DOMAIN_LABELS = {
    "network": "Computer Network",
    "architecture": "Computer Architecture",
    "ai": "Artificial Intelligence",
}


@dataclass
class StaticPaper:
    id: int
    title: str
    authors: list[str]
    abstract: str | None
    doi: str | None
    paper_url: str | None
    pdf_url: str | None
    conference: str
    year: int
    domain: str
    tags: list[str]
    sources: list[dict[str, str | None]]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return slug or "item"


def ensure_seed_data() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_conferences(db, registry.conferences)
        seed_taxonomy(db)
    finally:
        db.close()


def load_papers() -> list[StaticPaper]:
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Paper)
            .options(
                selectinload(Paper.conference),
                selectinload(Paper.source_records),
                selectinload(Paper.tags).selectinload(PaperTag.tag),
            )
            .order_by(Paper.year.desc(), Paper.conference_id, Paper.title)
        ).all()

        papers: list[StaticPaper] = []
        for paper in rows:
            papers.append(
                StaticPaper(
                    id=paper.id,
                    title=paper.title,
                    authors=paper.authors or [],
                    abstract=paper.abstract,
                    doi=paper.doi,
                    paper_url=paper.paper_url,
                    pdf_url=paper.pdf_url,
                    conference=paper.conference.acronym,
                    year=paper.year,
                    domain=paper.domain,
                    tags=sorted({item.tag.label for item in paper.tags}),
                    sources=[
                        {
                            "type": source.source_type,
                            "url": source.source_url,
                        }
                        for source in sorted(
                            paper.source_records,
                            key=lambda item: (item.source_type, item.id),
                        )
                    ],
                )
            )
        return papers
    finally:
        db.close()


def write_json(papers: list[StaticPaper]) -> None:
    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    paper_dicts = [asdict(paper) for paper in papers]
    (PUBLIC_DATA_DIR / "papers.json").write_text(
        json.dumps(paper_dicts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    by_domain = Counter(paper.domain for paper in papers)
    by_conference = Counter(paper.conference for paper in papers)
    by_year = Counter(str(paper.year) for paper in papers)
    summary = {
        "total_papers": len(papers),
        "with_abstract": sum(1 for paper in papers if paper.abstract),
        "by_domain": dict(sorted(by_domain.items())),
        "by_conference": dict(sorted(by_conference.items())),
        "by_year": dict(sorted(by_year.items(), reverse=True)),
    }
    (PUBLIC_DATA_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def md_link(label: str, href: str | None) -> str:
    if not href:
        return escape(label)
    return f"[{escape(label)}]({href})"


def paper_block(paper: StaticPaper) -> str:
    title = md_link(paper.title, paper.paper_url or paper.pdf_url)
    authors = ", ".join(escape(author) for author in paper.authors[:12])
    if len(paper.authors) > 12:
        authors += ", ..."
    tags = ", ".join(escape(tag) for tag in paper.tags) if paper.tags else "None"
    source_links = [
        md_link(source["type"] or "source", source["url"])
        for source in paper.sources
        if source.get("url")
    ]
    sources = " · ".join(source_links) if source_links else "None"
    abstract = escape(paper.abstract or "No abstract collected yet.")

    doi_line = f"- DOI: `{escape(paper.doi)}`\n" if paper.doi else ""
    return (
        f"### {title}\n\n"
        f"- Conference: `{paper.conference}`\n"
        f"- Year: `{paper.year}`\n"
        f"- Domain: `{paper.domain}`\n"
        f"{doi_line}"
        f"- Authors: {authors or 'Unknown'}\n"
        f"- Tags: {tags}\n"
        f"- Sources: {sources}\n\n"
        f"**Abstract**\n\n"
        f"{abstract}\n"
    )


def write_index(papers: list[StaticPaper]) -> None:
    by_domain = Counter(paper.domain for paper in papers)
    by_conference = Counter(paper.conference for paper in papers)
    by_year = Counter(paper.year for paper in papers)
    with_abstract = sum(1 for paper in papers if paper.abstract)

    lines = [
        "# TopConf Paper Hub",
        "",
        "<PaperBrowser />",
        "",
        "## Snapshot",
        "",
        f"- Total papers: **{len(papers)}**",
        f"- Papers with abstracts: **{with_abstract}**",
        f"- Conferences: **{len(by_conference)}**",
        f"- Years: **{len(by_year)}**",
        "",
        "## Domains",
        "",
        "| Domain | Papers |",
        "| --- | ---: |",
    ]
    for domain, count in sorted(by_domain.items()):
        label = DOMAIN_LABELS.get(domain, domain)
        lines.append(f"| [{label}](domains/{slugify(domain)}) | {count} |")

    lines.extend(
        [
            "",
            "## Recent Years",
            "",
            "| Year | Papers |",
            "| --- | ---: |",
        ]
    )
    for year, count in sorted(by_year.items(), reverse=True):
        lines.append(f"| [{year}](years/{year}) | {count} |")

    lines.extend(
        [
            "",
            "## Conferences",
            "",
            "| Conference | Papers |",
            "| --- | ---: |",
        ]
    )
    for conference, count in sorted(by_conference.items()):
        lines.append(f"| [{conference}](conferences/{slugify(conference)}) | {count} |")

    lines.extend(
        [
            "",
            "## Data",
            "",
            "- [papers.json](data/papers.json)",
            "- [summary.json](data/summary.json)",
            "",
        ]
    )
    (DOCS_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def write_group_pages(papers: list[StaticPaper]) -> None:
    CONFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    YEAR_DIR.mkdir(parents=True, exist_ok=True)
    DOMAIN_DIR.mkdir(parents=True, exist_ok=True)

    grouped_by_conference: dict[str, list[StaticPaper]] = defaultdict(list)
    grouped_by_year: dict[int, list[StaticPaper]] = defaultdict(list)
    grouped_by_domain: dict[str, list[StaticPaper]] = defaultdict(list)

    for paper in papers:
        grouped_by_conference[paper.conference].append(paper)
        grouped_by_year[paper.year].append(paper)
        grouped_by_domain[paper.domain].append(paper)

    write_listing_page(
        CONFERENCE_DIR / "index.md",
        "Conferences",
        [(name, f"./{slugify(name)}", len(items)) for name, items in grouped_by_conference.items()],
    )
    write_listing_page(
        YEAR_DIR / "index.md",
        "Years",
        [(str(year), f"./{year}", len(items)) for year, items in grouped_by_year.items()],
        reverse=True,
    )
    write_listing_page(
        DOMAIN_DIR / "index.md",
        "Domains",
        [
            (DOMAIN_LABELS.get(name, name), f"./{slugify(name)}", len(items))
            for name, items in grouped_by_domain.items()
        ],
    )

    for conference, items in grouped_by_conference.items():
        write_paper_page(CONFERENCE_DIR / f"{slugify(conference)}.md", conference, items)
    for year, items in grouped_by_year.items():
        write_paper_page(YEAR_DIR / f"{year}.md", str(year), items)
    for domain, items in grouped_by_domain.items():
        write_paper_page(
            DOMAIN_DIR / f"{slugify(domain)}.md",
            DOMAIN_LABELS.get(domain, domain),
            items,
        )


def write_listing_page(
    path: Path,
    title: str,
    rows: list[tuple[str, str, int]],
    *,
    reverse: bool = False,
) -> None:
    rows = sorted(rows, key=lambda item: item[0], reverse=reverse)
    lines = [
        f"# {title}",
        "",
        "| Name | Papers |",
        "| --- | ---: |",
    ]
    for name, href, count in rows:
        lines.append(f"| [{escape(name)}]({href}) | {count} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_paper_page(path: Path, title: str, papers: list[StaticPaper]) -> None:
    papers = sorted(papers, key=lambda item: (-item.year, item.conference, item.title))
    lines = [
        f"# {escape(title)}",
        "",
        f"Total papers: **{len(papers)}**",
        "",
    ]
    for paper in papers:
        lines.append(paper_block(paper))
        lines.append("\n---\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_vitepress_sidebar(papers: list[StaticPaper]) -> None:
    VITEPRESS_DIR.mkdir(parents=True, exist_ok=True)
    conferences = sorted({paper.conference for paper in papers})
    years = sorted({paper.year for paper in papers}, reverse=True)
    domains = sorted({paper.domain for paper in papers})

    sidebar = {
        "/conferences/": [
            {"text": "All Conferences", "link": "/conferences/"},
            *[
                {"text": conference, "link": f"/conferences/{slugify(conference)}"}
                for conference in conferences
            ],
        ],
        "/years/": [
            {"text": "All Years", "link": "/years/"},
            *[{"text": str(year), "link": f"/years/{year}"} for year in years],
        ],
        "/domains/": [
            {"text": "All Domains", "link": "/domains/"},
            *[
                {
                    "text": DOMAIN_LABELS.get(domain, domain),
                    "link": f"/domains/{slugify(domain)}",
                }
                for domain in domains
            ],
        ],
    }

    (VITEPRESS_DIR / "generated-sidebar.mjs").write_text(
        "export const generatedSidebar = "
        + json.dumps(sidebar, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )


def export_site() -> None:
    ensure_seed_data()
    papers = load_papers()
    write_json(papers)
    write_index(papers)
    write_group_pages(papers)
    write_vitepress_sidebar(papers)
    print(f"Exported {len(papers)} papers to {DOCS_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-empty-check", action="store_true")
    args = parser.parse_args()

    export_site()
    if not args.skip_empty_check:
        data = json.loads((PUBLIC_DATA_DIR / "summary.json").read_text(encoding="utf-8"))
        if data["total_papers"] == 0:
            raise SystemExit("No papers exported. Run a collector before building the static site.")


if __name__ == "__main__":
    main()
