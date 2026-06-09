from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conference, ConferenceEdition
from app.db.session import get_db
from app.schemas import ConferenceEditionRead, ConferenceRead
from app.services.conference_registry import registry

router = APIRouter(tags=["conferences"])


@router.get("/conferences", response_model=list[ConferenceRead])
def list_conferences(
    domain: str | None = None,
    active: bool | None = Query(default=True),
    db: Session = Depends(get_db),
) -> list[Conference]:
    query = select(Conference)
    if domain:
        query = query.where(Conference.domain == domain)
    if active is not None:
        query = query.where(Conference.active == active)
    query = query.order_by(Conference.domain, Conference.acronym)
    return list(db.scalars(query).all())


@router.get("/conferences/{acronym}", response_model=ConferenceRead)
def get_conference(acronym: str, db: Session = Depends(get_db)) -> Conference:
    seed = registry.get(acronym)
    normalized = seed.acronym if seed else acronym
    conference = db.scalar(select(Conference).where(Conference.acronym == normalized))
    if conference is None:
        raise HTTPException(status_code=404, detail="Conference not found")
    return conference


@router.get("/editions", response_model=list[ConferenceEditionRead])
def list_editions(
    conference: str | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
) -> list[ConferenceEditionRead]:
    query = select(ConferenceEdition, Conference.acronym).join(Conference)
    if conference:
        seed = registry.get(conference)
        acronym = seed.acronym if seed else conference
        query = query.where(Conference.acronym == acronym)
    if year:
        query = query.where(ConferenceEdition.year == year)
    query = query.order_by(Conference.acronym, ConferenceEdition.year.desc())

    items: list[ConferenceEditionRead] = []
    for edition, acronym in db.execute(query).all():
        items.append(
            ConferenceEditionRead(
                id=edition.id,
                conference_id=edition.conference_id,
                conference=acronym,
                year=edition.year,
                start_date=edition.start_date,
                end_date=edition.end_date,
                location=edition.location,
                proceedings_url=edition.proceedings_url,
            )
        )
    return items

