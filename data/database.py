"""Database connection setup (SQLite + SQLAlchemy)."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# The database is one file. Tests can point to a different one with an
# environment variable.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///recommendations.db")

# check_same_thread=False lets the Flask API use the database
# from several threads
db_engine = create_engine(DATABASE_URL, connect_args={
                          "check_same_thread": False})

# A "session" is one conversation with the database
SessionLocal = sessionmaker(bind=db_engine)

# Every table class we write in models.py will inherit from Base
Base = declarative_base()


def get_session():
    """Open a new database session. Remember to close it when done."""
    return SessionLocal()


def init_db():
    """Create all tables (does nothing for tables that already exist)."""
    from data import models  # noqa: F401  (importing registers the tables)
    Base.metadata.create_all(db_engine)
