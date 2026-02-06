"""
Integration tests for the FastAPI REST endpoints.

Each test uses an in-memory SQLite database (via the ``client`` fixture)
so no live MySQL server is needed.
"""

import pytest


# ======================================================================
# Root & health endpoints
# ======================================================================

class TestRootEndpoints:
    """Tests for / and /health."""

    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert data["version"] == "1.0.0"

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


# ======================================================================
# Course list endpoint  GET /api/v1/courses
# ======================================================================

class TestCourseListEndpoint:
    """Tests for the paginated course listing."""

    def test_empty_list(self, client):
        """No courses in DB → empty list with total=0."""
        resp = client.get("/api/v1/courses")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []
        assert body["meta"]["total"] == 0

    def test_returns_seeded_courses(self, client, sample_courses):
        """Seeded courses appear in the response."""
        resp = client.get("/api/v1/courses")
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 5
        assert len(body["data"]) == 5

    def test_search_by_title(self, client, sample_courses):
        """?q= filters by title (ILIKE)."""
        resp = client.get("/api/v1/courses", params={"q": "Python 0"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] >= 1
        titles = [c["title"] for c in body["data"]]
        assert any("Python 0" in t for t in titles)

    def test_filter_language(self, client, sample_courses):
        """?language=en returns only English courses."""
        resp = client.get("/api/v1/courses", params={"language": "en"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 5  # all sample courses are 'en'

    def test_filter_language_no_match(self, client, sample_courses):
        """?language=fr returns nothing when no French courses exist."""
        resp = client.get("/api/v1/courses", params={"language": "fr"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 0

    def test_filter_level(self, client, sample_courses):
        """?level=Beginner returns sample courses."""
        resp = client.get("/api/v1/courses", params={"level": "Beginner"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 5

    def test_filter_topic(self, client, sample_courses):
        """?topic=Computer Science returns sample courses."""
        resp = client.get("/api/v1/courses", params={"topic": "Computer Science"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 5

    def test_pagination_page_size(self, client, sample_courses):
        """per_page limits the returned items."""
        resp = client.get("/api/v1/courses", params={"per_page": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 2
        assert body["meta"]["total"] == 5
        assert body["meta"]["per_page"] == 2
        assert body["meta"]["total_pages"] == 3

    def test_pagination_second_page(self, client, sample_courses):
        """page=2 returns a different slice."""
        resp = client.get("/api/v1/courses", params={"page": 2, "per_page": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 2
        assert body["meta"]["page"] == 2

    def test_pagination_last_page(self, client, sample_courses):
        """Last page may have fewer items than per_page."""
        resp = client.get("/api/v1/courses", params={"page": 3, "per_page": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1  # 5 total, page 3 with per_page=2 → 1 item


# ======================================================================
# Course detail endpoint  GET /api/v1/courses/{id}
# ======================================================================

class TestCourseDetailEndpoint:
    """Tests for fetching a single course by ID."""

    def test_get_existing_course(self, client, sample_courses):
        course_id = sample_courses[0].id
        resp = client.get(f"/api/v1/courses/{course_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == course_id
        assert "Introduction to Python" in body["title"]

    def test_course_not_found(self, client):
        resp = client.get("/api/v1/courses/99999")
        assert resp.status_code == 404

    def test_detail_includes_full_description(self, client, sample_courses):
        course_id = sample_courses[0].id
        resp = client.get(f"/api/v1/courses/{course_id}")
        body = resp.json()
        assert body.get("full_description") is not None
        assert "comprehensive" in body["full_description"]


# ======================================================================
# Similar courses endpoint  GET /api/v1/courses/{id}/similar
# ======================================================================

class TestSimilarCoursesEndpoint:
    """Tests for the similar-courses sub-resource."""

    def test_similar_courses_found(self, client, sample_courses, sample_similar):
        course_id = sample_courses[0].id
        resp = client.get(f"/api/v1/courses/{course_id}/similar")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2  # course 0 has two similar entries

    def test_similar_courses_empty(self, client, sample_courses):
        """A course with no similarity entries returns an empty list."""
        course_id = sample_courses[4].id
        resp = client.get(f"/api/v1/courses/{course_id}/similar")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_similar_course_not_found(self, client):
        """Requesting similar courses for a non-existent course → 404."""
        resp = client.get("/api/v1/courses/99999/similar")
        assert resp.status_code == 404


# ======================================================================
# Analytics endpoint  GET /api/v1/analytics
# ======================================================================

class TestAnalyticsEndpoint:
    """Tests for the analytics aggregation endpoint."""

    def test_analytics_empty_db(self, client):
        resp = client.get("/api/v1/analytics")
        assert resp.status_code == 200
        body = resp.json()
        assert body["totalCourses"] == 0

    def test_analytics_with_data(self, client, sample_courses):
        resp = client.get("/api/v1/analytics")
        assert resp.status_code == 200
        body = resp.json()
        assert body["totalCourses"] == 5
        assert "coursesByLanguage" in body
        assert "coursesByLevel" in body
        assert "coursesBySource" in body
