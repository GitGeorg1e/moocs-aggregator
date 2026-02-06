"""
Shared test fixtures for the MOOCs Aggregator project.

Uses an in-memory SQLite database to avoid requiring a live MySQL server.
"""

import pytest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.models.base import Base
from backend.app.models.source import Source
from backend.app.models.course import Course
from backend.app.models.similar_course import SimilarCourse
from backend.app.core.db import get_db
from backend.app.main import app


# ---------------------------------------------------------------------------
# In-memory SQLite engine (shared across the whole test session)
# ---------------------------------------------------------------------------
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_TestSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


# ---------------------------------------------------------------------------
# Session-scoped: create tables once
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


# ---------------------------------------------------------------------------
# Per-test database session with automatic cleanup
# ---------------------------------------------------------------------------
@pytest.fixture()
def db_session():
    """Yield a fresh SQLAlchemy session; roll back everything after the test."""
    connection = _engine.connect()
    transaction = connection.begin()
    session = _TestSession(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# FastAPI TestClient with overridden DB dependency
# ---------------------------------------------------------------------------
@pytest.fixture()
def client(db_session):
    """Provide a TestClient that uses the test database session."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sample data helpers
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_source(db_session):
    """Insert and return a sample Source row."""
    source = Source(name="coursera", base_url="https://www.coursera.org")
    db_session.add(source)
    db_session.flush()
    return source


@pytest.fixture()
def sample_source_mit(db_session):
    """Insert and return a second Source (MIT OCW)."""
    source = Source(name="mit_ocw", base_url="https://ocw.mit.edu")
    db_session.add(source)
    db_session.flush()
    return source


@pytest.fixture()
def sample_courses(db_session, sample_source):
    """Insert 5 sample courses belonging to the Coursera source."""
    now = datetime.now(timezone.utc)
    courses = []
    for i in range(5):
        course = Course(
            source_id=sample_source.id,
            source_course_id=f"course-{i}",
            title=f"Introduction to Python {i}",
            short_description=f"Learn Python basics part {i}",
            full_description=f"A comprehensive course on Python programming part {i}",
            keywords="python, programming, beginner",
            topic="Computer Science",
            language="en",
            level="Beginner",
            course_url=f"https://www.coursera.org/learn/python-{i}",
            image_url=f"https://example.com/img/{i}.jpg",
            created_at=now,
            updated_at=now,
        )
        db_session.add(course)
        courses.append(course)

    db_session.flush()
    return courses


@pytest.fixture()
def sample_similar(db_session, sample_courses):
    """Create similarity relationships between the first three sample courses."""
    pairs = [
        (sample_courses[0].id, sample_courses[1].id, 0.92),
        (sample_courses[0].id, sample_courses[2].id, 0.85),
        (sample_courses[1].id, sample_courses[2].id, 0.78),
    ]
    entries = []
    for cid, sid, score in pairs:
        entry = SimilarCourse(course_id=cid, similar_course_id=sid, similarity=score)
        db_session.add(entry)
        entries.append(entry)
    db_session.flush()
    return entries
