from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.course import Course
from backend.app.schemas.course import CourseCreate


def upsert_courses(
    db: Session,
    courses: Iterable[CourseCreate],
    since: Optional[datetime] = None,
) -> List[Course]:
    saved: List[Course] = []

    for c in courses:
        if since is not None and c.last_updated_at_source is not None:
            if c.last_updated_at_source < since:
                continue

        row = db.execute(
            select(Course).where(
                Course.source_id == c.source_id,
                Course.source_course_id == c.source_course_id,
            )
        ).scalar_one_or_none()

        if row is None:
            row = Course(
                source_id=c.source_id,
                source_course_id=c.source_course_id,
                title=c.title,
                short_description=c.short_description,
                full_description=c.full_description,
                keywords=c.keywords,
                topic=c.topic,
                language=c.language,
                level=c.level,
                course_url=str(c.course_url),
                enrollment_url=str(c.enrollment_url) if c.enrollment_url else None,
                image_url=str(c.image_url) if c.image_url else None,
                last_updated_at_source=c.last_updated_at_source,
            )
            db.add(row)
        else:
            row.title = c.title
            row.short_description = c.short_description
            row.full_description = c.full_description
            row.keywords = c.keywords
            row.topic = c.topic
            row.language = c.language
            row.level = c.level
            row.course_url = str(c.course_url)
            row.enrollment_url = str(c.enrollment_url) if c.enrollment_url else None
            row.image_url = str(c.image_url) if c.image_url else None
            row.last_updated_at_source = c.last_updated_at_source

        saved.append(row)

    db.commit()
    for r in saved:
        db.refresh(r)
    return saved
