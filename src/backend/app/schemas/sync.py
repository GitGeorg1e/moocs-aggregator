"""
Pydantic schemas for sync (data-harvesting) request/response models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel


class SyncSource(str, Enum):
    """Available sync sources."""
    coursera = "coursera"
    mit_ocw = "mit_ocw"


class SyncRequest(BaseModel):
    """Sync request body."""
    max_courses: Optional[int] = None


class SyncResponse(BaseModel):
    """Sync response."""
    task_id: str
    source: str
    status: str
    message: str


class SyncStatusResponse(BaseModel):
    """Sync task status."""
    task_id: str
    status: str
    source: Optional[str] = None
    total_courses: Optional[int] = None
    imported_courses: Optional[int] = None
    errors: Optional[List[str]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
