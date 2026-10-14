"""Shared test setup. pytest loads this file before any test."""
import os

# Use a temporary in-memory database so tests never touch recommendations.db.
# This must be set before data.database is imported.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402

from data.database import Base, db_engine, get_session, init_db  # noqa: E402
from scripts.seed_data import seed  # noqa: E402


@pytest.fixture
def session():
    """A fresh, seeded database session for each test."""
    init_db()
    Base.metadata.drop_all(db_engine)
    Base.metadata.create_all(db_engine)
    db_session = get_session()
    seed(db_session)
    yield db_session
    db_session.close()
