"""
Platform connectors – fetch course metadata from external MOOC providers.

Each connector implements :class:`BaseConnector` and yields
:class:`~backend.app.schemas.course.CourseCreate` objects.
"""
from .base import BaseConnector
from .coursera import CourseraConnector
from .mit_ocw import MitOcwConnector

__all__ = ["BaseConnector", "CourseraConnector", "MitOcwConnector"]
