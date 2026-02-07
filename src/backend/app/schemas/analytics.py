"""
Pydantic schemas for analytics response models.
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict


class AnalyticsResponse(BaseModel):
    """Analytics summary."""
    model_config = ConfigDict(from_attributes=True)

    totalCourses: int
    coursesBySource: dict
    coursesByLanguage: dict
    coursesByLevel: dict
    recentlyAdded: int = 0
    topRatedCourses: List[dict] = []
