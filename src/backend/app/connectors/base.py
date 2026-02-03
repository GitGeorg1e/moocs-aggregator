from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable, Optional

from backend.app.schemas.course import CourseCreate


class BaseConnector(ABC):
    @abstractmethod
    def fetch_courses(self, since: Optional[datetime] = None) -> Iterable[CourseCreate]:
        raise NotImplementedError
