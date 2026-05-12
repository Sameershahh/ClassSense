# backend/database.py
# SQLAlchemy database connection and session management.

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./classsense_dev.db"
)

# SQLite needs special connect args; PostgreSQL uses NullPool (no connection leak)
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
else:
    engine = create_engine(DATABASE_URL, poolclass=NullPool, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency. Yields one DB session per request,
    closes it automatically when the request finishes.
    Usage:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Creates all tables defined via Base.metadata.
    Called once at application startup.
    """
    from backend.models.session import Session, FrameAnalytic, SessionSummary  # noqa
    Base.metadata.create_all(bind=engine)
