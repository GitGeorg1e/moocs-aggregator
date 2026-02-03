from __future__ import annotations
from abc import ABC, abstractmethod

from datetime import datetime
from typing import Iterable, Optional
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from backend.app.schemas.course import CourseCreate 

class BaseConnector(ABC):
    @abstractmethod
    def fetch_courses(self, since: Optional[datetime] = None) -> Iterable[CourseCreate]:
        raise NotImplementedError

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
