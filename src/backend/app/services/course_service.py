from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import or_, cast, String, text
from sqlalchemy.orm import Session, joinedload

from backend.app.models.course import Course
from backend.app.models.source import Source
from backend.app.models.similar_course import SimilarCourse


class CourseService:
    """Service για αναζήτηση και ανάκτηση courses."""

    def __init__(self, db: Session):
        self.db = db

    def get_courses(
        self,
        q: Optional[str] = None,
        language: Optional[str] = None,
        level: Optional[str] = None,
        source: Optional[str] = None,
        topic: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Course], int]:
        """
        Ανάκτηση μαθημάτων με search, filters και pagination.
        
        Returns:
            Tuple of (courses list, total count)
        """
        query = self.db.query(Course)

        # Full-text search σε title, description, keywords
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Course.title.ilike(search_term),
                    Course.short_description.ilike(search_term),
                    Course.full_description.ilike(search_term),
                    Course.keywords.ilike(search_term),
                )
            )

        # Filters
        if language:
            query = query.filter(Course.language.ilike(f"%{language}%"))
        if level:
            query = query.filter(Course.level.ilike(f"%{level}%"))
        if topic:
            query = query.filter(Course.topic.ilike(f"%{topic}%"))
        if source:
            query = query.join(Source).filter(Source.name.ilike(f"%{source}%"))
        
        # Keyword filter - keywords is comma-separated string
        if keyword:
            query = query.filter(Course.keywords.ilike(f"%{keyword}%"))

        # Count total πριν το pagination
        total = query.count()

        # Pagination
        offset = (page - 1) * per_page
        courses = (
            query
            .order_by(Course.updated_at.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

        return courses, total

    def get_course_by_id(self, course_id: int) -> Optional[Course]:
        """Ανάκτηση course με eager loading του source."""
        return (
            self.db.query(Course)
            .options(joinedload(Course.source))
            .filter(Course.id == course_id)
            .first()
        )

    def get_course_cluster_id(self, course_id: int) -> Optional[int]:
        """Return the Spark cluster ID for a course (if available)."""
        try:
            row = self.db.execute(
                text(
                    "SELECT cluster_id FROM course_clusters "
                    "WHERE course_id = :course_id LIMIT 1"
                ),
                {"course_id": course_id},
            ).fetchone()
        except Exception:
            return None

        return row[0] if row else None

    def get_source_name(self, source_id: int) -> Optional[str]:
        """Ανάκτηση ονόματος source από ID."""
        source = self.db.query(Source).filter(Source.id == source_id).first()
        return source.name if source else None

    def get_similar_courses(self, course_id: int, top_k: int = 10) -> List[dict]:
        """
        Ανάκτηση παρόμοιων μαθημάτων από Spark results.
        
        Διαβάζει από τον πίνακα similar_courses που γεμίζει
        το Spark batch job.
        """
        similar_entries = (
            self.db.query(SimilarCourse)
            .filter(SimilarCourse.course_id == course_id)
            .order_by(SimilarCourse.similarity.desc())
            .limit(top_k)
            .all()
        )

        results = []
        for entry in similar_entries:
            similar_course = (
                self.db.query(Course)
                .options(joinedload(Course.source))
                .filter(Course.id == entry.similar_course_id)
                .first()
            )

            if similar_course:
                results.append({
                    "id": similar_course.id,
                    "title": similar_course.title,
                    "course_url": similar_course.course_url,
                    "source_name": similar_course.source.name if similar_course.source else None,
                    "image_url": similar_course.image_url,
                    "topic": similar_course.topic,
                    "similarity_score": entry.similarity,
                })

        return results