"""Database engine, session factory, and Base for SQLAlchemy models"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


# Declarative base for all ORM models
class Base(DeclarativeBase):
    pass


# Create engine - sync only (no async)
# SQLite: check_same_thread=False needed for FastAPI multi-threading
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, echo=False)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
