"""
Pydantic schemas (request / response models).

Submodules
----------
course     – Course CRUD and list schemas
sync       – Data-harvesting sync schemas
analytics  – Analytics summary schemas
"""
from .course import (
    CourseCreate,
    CourseResponse,
    CourseDetailResponse,
    CourseListResponse,
    SimilarCourseResponse,
    PaginationMeta,
)
from .sync import SyncSource, SyncRequest, SyncResponse, SyncStatusResponse
from .analytics import AnalyticsResponse

__all__ = [
    # course
    "CourseCreate",
    "CourseResponse",
    "CourseDetailResponse",
    "CourseListResponse",
    "SimilarCourseResponse",
    "PaginationMeta",
    # sync
    "SyncSource",
    "SyncRequest",
    "SyncResponse",
    "SyncStatusResponse",
    # analytics
    "AnalyticsResponse",
]
