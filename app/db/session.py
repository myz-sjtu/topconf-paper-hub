from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models import Base


def _connect_args() -> dict[str, object]:
    if settings.database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(settings.database_url, connect_args=_connect_args(), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

