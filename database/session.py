"""Database engine, session factory, and initialization utilities."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from config.settings import DATABASE_URL
from database.models import Base


def build_engine(database_url: str) -> Engine:
    """
    Create the SQLAlchemy engine.

    Args:
        database_url: SQLAlchemy-compatible database connection URL.

    Returns:
        Configured SQLAlchemy engine.
    """

    engine_options: dict[str, object] = {
        "pool_pre_ping": True,
    }

    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {
            "check_same_thread": False,
        }

    return create_engine(
        database_url,
        **engine_options,
    )


engine = build_engine(DATABASE_URL)


if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection: object,
        connection_record: object,
    ) -> None:
        """
        Enable SQLite foreign-key enforcement for every connection.
        """

        del connection_record

        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def init_db() -> None:
    """
    Create database tables that do not already exist.

    This is suitable for local development and the prototype. Production
    schema changes should later be managed with Alembic migrations.
    """

    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional database session.

    The session is committed on success, rolled back on failure, and always
    closed after use.

    Yields:
        Active SQLAlchemy session.
    """

    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for dependency-style usage.

    This is useful if Aoun later adds a FastAPI service.
    """

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()