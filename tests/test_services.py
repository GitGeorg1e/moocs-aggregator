"""
Unit tests for the service layer (CourseService, etc.).
"""

import pytest
from datetime import datetime, timezone

from backend.app.services.course_service import CourseService
from backend.app.models.course import Course
from backend.app.models.source import Source
from backend.app.models.similar_course import SimilarCourse


class TestCourseServiceGetCourses:
    """Tests for CourseService.get_courses()."""

    def test_returns_all_when_no_filters(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses()
        assert total == 5
        assert len(courses) == 5

    def test_search_query_filters_by_title(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(q="Python 0")
        assert total >= 1
        assert all("Python 0" in c.title for c in courses)

    def test_search_query_filters_by_description(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(q="basics part 2")
        assert total >= 1

    def test_filter_by_language(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(language="en")
        assert total == 5

    def test_filter_by_language_no_match(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(language="de")
        assert total == 0

    def test_filter_by_level(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(level="Beginner")
        assert total == 5

    def test_filter_by_topic(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(topic="Computer Science")
        assert total == 5

    def test_filter_by_source(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(source="coursera")
        assert total == 5

    def test_filter_by_source_no_match(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(source="udemy")
        assert total == 0

    def test_pagination(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(page=1, per_page=2)
        assert total == 5
        assert len(courses) == 2

    def test_pagination_page_2(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(page=2, per_page=2)
        assert total == 5
        assert len(courses) == 2

    def test_combined_filters(self, db_session, sample_courses):
        service = CourseService(db_session)
        courses, total = service.get_courses(language="en", level="Beginner", topic="Computer Science")
        assert total == 5


class TestCourseServiceGetById:
    """Tests for CourseService.get_course_by_id()."""

    def test_existing_course(self, db_session, sample_courses):
        service = CourseService(db_session)
        course = service.get_course_by_id(sample_courses[0].id)
        assert course is not None
        assert course.id == sample_courses[0].id
        assert "Python" in course.title

    def test_nonexistent_course(self, db_session):
        service = CourseService(db_session)
        course = service.get_course_by_id(99999)
        assert course is None

    def test_eager_loads_source(self, db_session, sample_courses):
        service = CourseService(db_session)
        course = service.get_course_by_id(sample_courses[0].id)
        # source relationship should be loaded (eager via joinedload)
        assert course.source is not None
        assert course.source.name == "coursera"


class TestCourseServiceGetSourceName:
    """Tests for CourseService.get_source_name()."""

    def test_known_source(self, db_session, sample_source):
        service = CourseService(db_session)
        name = service.get_source_name(sample_source.id)
        assert name == "coursera"

    def test_unknown_source(self, db_session):
        service = CourseService(db_session)
        name = service.get_source_name(99999)
        assert name is None


class TestCourseServiceSimilarCourses:
    """Tests for CourseService.get_similar_courses()."""

    def test_returns_similar(self, db_session, sample_courses, sample_similar):
        service = CourseService(db_session)
        results = service.get_similar_courses(sample_courses[0].id, top_k=10)
        assert len(results) == 2
        # Should be ordered by similarity descending
        assert results[0]["similarity_score"] >= results[1]["similarity_score"]

    def test_empty_when_none(self, db_session, sample_courses):
        service = CourseService(db_session)
        results = service.get_similar_courses(sample_courses[4].id)
        assert results == []

    def test_top_k_limits_results(self, db_session, sample_courses, sample_similar):
        service = CourseService(db_session)
        results = service.get_similar_courses(sample_courses[0].id, top_k=1)
        assert len(results) == 1
