"""
Pydantic schemas for Course-related request/response models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# ── Course schemas ────────────────────────────────────────────────────


class CourseCreate(BaseModel):
    """Schema for creating / updating courses from connectors."""
    source_id: int
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


class CourseResponse(BaseModel):
    """Schema for course list items."""
    model_config = ConfigDict(from_attributes=True)

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


class CourseDetailResponse(BaseModel):
    """Schema for full course detail."""
    model_config = ConfigDict(from_attributes=True)

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


class SimilarCourseResponse(BaseModel):
    """Schema for a similar course entry."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    course_url: Optional[str] = None
    source_name: Optional[str] = None
    image_url: Optional[str] = None
    topic: Optional[str] = None
    similarity_score: float


# ── Pagination ────────────────────────────────────────────────────────


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int
    page: int
    per_page: int
    total_pages: int


class CourseListResponse(BaseModel):
    """Paginated course list."""
    data: List[CourseResponse]
    meta: PaginationMeta
