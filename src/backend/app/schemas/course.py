from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, HttpUrl


class SyncSource(str, Enum):
    """Available sync sources"""
    coursera = "coursera"
    mit_ocw = "mit_ocw"


class CourseBase(BaseModel):
    """Base course schema"""
    title: str
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    keywords: Optional[str] = None
    language: Optional[str] = None
    level: Optional[str] = None
    instructor: Optional[str] = None
    thumbnail_url: Optional[str] = None
    course_url: Optional[str] = None
    enrollment_url: Optional[str] = None


class CourseCreate(CourseBase):
    """Schema for creating courses from connectors"""
    source_id: int
    source_course_id: str
    course_url: str  # Required - connectors always provide this
    image_url: Optional[str] = None  # Connectors use image_url, not thumbnail_url
    topic: Optional[str] = None
    last_updated_at_source: Optional[datetime] = None


class CourseRead(CourseBase):
    id: int

    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    """Schema για source info."""
    id: int
    name: str
    base_url: str

    class Config:
        from_attributes = True


class CourseResponse(CourseBase):
    """Course response schema"""
    id: int
    source_name: Optional[str] = None
    source_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    """Detailed course response with source info"""
    source: Optional[dict] = None


class SimilarCourseResponse(BaseModel):
    """Similar course response"""
    id: int
    title: str
    short_description: Optional[str] = None
    similarity_score: float
    source_name: Optional[str] = None

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    """Metadata για pagination."""
    total: int
    page: int
    per_page: int
    total_pages: int


class CourseListResponse(BaseModel):
    """Paginated course list response"""
    data: List[CourseResponse]
    meta: PaginationMeta


class SyncRequest(BaseModel):
    """Sync request schema"""
    max_courses: Optional[int] = None


class SyncResponse(BaseModel):
    """Sync response schema"""
    task_id: str
    source: str
    status: str
    message: str


class SyncStatusResponse(BaseModel):
    """Sync status response"""
    task_id: str
    status: str
    source: Optional[str] = None
    total_courses: Optional[int] = None
    imported_courses: Optional[int] = None
    errors: Optional[List[str]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AnalyticsResponse(BaseModel):
    """Analytics response schema"""
    totalCourses: int
    coursesBySource: dict
    coursesByLanguage: dict
    coursesByLevel: dict
    recentlyAdded: int = 0
    topRatedCourses: List[dict] = []
    
    class Config:
        from_attributes = True
