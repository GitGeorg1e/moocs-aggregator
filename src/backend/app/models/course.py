from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


# ============== Course Schemas ==============

class CourseResponse(BaseModel):
    """Schema για course response (λίστα)."""
    id: int
    source_id: int
    source_name: Optional[str] = None
    source_course_id: str
    title: str
    short_description: Optional[str] = None
    topic: Optional[str] = None
    language: Optional[str] = None
    level: Optional[str] = None
    course_url: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class CourseDetailResponse(BaseModel):
    """Schema για πλήρη στοιχεία course."""
    id: int
    source_id: int
    source_name: Optional[str] = None
    source_course_id: str
    title: str
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    keywords: Optional[str] = None
    topic: Optional[str] = None
    language: Optional[str] = None
    level: Optional[str] = None
    course_url: str
    enrollment_url: Optional[str] = None
    image_url: Optional[str] = None
    last_updated_at_source: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SimilarCourseResponse(BaseModel):
    """Schema για similar course."""
    id: int
    title: str
    course_url: str
    source_name: Optional[str] = None
    image_url: Optional[str] = None
    topic: Optional[str] = None
    score: float

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    """Metadata για pagination."""
    total: int
    page: int
    per_page: int
    total_pages: int


class CourseListResponse(BaseModel):
    """Schema για paginated course list."""
    data: List[CourseResponse]
    meta: PaginationMeta


# ============== Sync Schemas ==============

class SyncSource(str, Enum):
    """Enum για τις διαθέσιμες πηγές sync."""
    coursera = "coursera"
    mit_ocw = "mit_ocw"


class SyncRequest(BaseModel):
    """Request schema για sync endpoint."""
    max_courses: Optional[int] = None
    topics: Optional[str] = None  # comma-separated


class SyncResponse(BaseModel):
    """Response schema για sync endpoint."""
    task_id: str
    source: str
    status: str
    message: str


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
