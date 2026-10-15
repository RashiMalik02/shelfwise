from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings


def _make_engine(url: str):
    # SQLite is only used by the test suite. An in-memory database needs a
    # single shared connection, otherwise every session sees an empty DB.
    if url.startswith("sqlite"):
        sqlite_engine = create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)

        # SQLite ignores foreign keys (and ON DELETE CASCADE) unless asked; Postgres always enforces them.
        @event.listens_for(sqlite_engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        return sqlite_engine
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
