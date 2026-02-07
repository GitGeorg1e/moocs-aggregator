from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Source / repository
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"),
        index=True,
    )
    source_course_id: Mapped[str] = mapped_column(String(200), index=True)

    # Core metadata
    title: Mapped[str] = mapped_column(String(300), index=True)
    short_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    full_description: Mapped[Optional[str]] = mapped_column(
        Text(),
        nullable=True,
    )

    # Classification fields
    keywords: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )  # comma-separated keywords
    topic: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    language: Mapped[Optional[str]] = mapped_column(
        String(10),
        index=True,
        nullable=True,
    )
    level: Mapped[Optional[str]] = mapped_column(
        String(50),
        index=True,
        nullable=True,
    )

    # URLs
    course_url: Mapped[str] = mapped_column(String(500))
    enrollment_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Last update from source
    last_updated_at_source: Mapped[Optional[datetime]] = mapped_column(
        DateTime(),
        index=True,
        nullable=True,
    )

    # Relationships
    source = relationship("Source", back_populates="courses")
    similar_courses = relationship(
        "SimilarCourse",
        primaryjoin="Course.id==SimilarCourse.course_id",
        cascade="all, delete-orphan",
    )
    similar_to = relationship(
        "SimilarCourse",
        primaryjoin="Course.id==SimilarCourse.similar_course_id",
        cascade="all, delete-orphan",
    )
