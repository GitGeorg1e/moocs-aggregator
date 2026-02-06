"""
Unit tests for connector parsing / normalisation helpers.

These tests exercise pure functions and static methods — no network calls
are made.
"""

import pytest
from datetime import datetime

from backend.app.connectors.coursera import CourseraConnector
from backend.app.connectors.mit_ocw import MitOcwConnector


# ======================================================================
# CourseraConnector
# ======================================================================

class TestCourseraSlug:
    """Tests for CourseraConnector._slug_from_url()."""

    def test_standard_url(self):
        assert CourseraConnector._slug_from_url(
            "https://www.coursera.org/learn/machine-learning"
        ) == "machine-learning"

    def test_url_with_trailing_slash(self):
        # urlparse preserves trailing slash; regex still captures slug
        slug = CourseraConnector._slug_from_url(
            "https://www.coursera.org/learn/python-for-everybody/"
        )
        assert slug == "python-for-everybody"

    def test_no_learn_segment(self):
        assert CourseraConnector._slug_from_url(
            "https://www.coursera.org/browse/data-science"
        ) == ""


class TestCourseraParseDt:
    """Tests for CourseraConnector._parse_dt()."""

    def test_iso_datetime(self):
        dt = CourseraConnector._parse_dt("2024-06-15T10:30:00Z")
        assert isinstance(dt, datetime)
        assert dt.year == 2024

    def test_none_input(self):
        assert CourseraConnector._parse_dt(None) is None

    def test_invalid_string(self):
        assert CourseraConnector._parse_dt("not-a-date") is None


class TestCourseraNormalizeLanguage:
    """Tests for CourseraConnector._normalize_language()."""

    def test_english_string(self):
        assert CourseraConnector._normalize_language("English") == "en"

    def test_language_code(self):
        assert CourseraConnector._normalize_language("en") == "en"

    def test_language_with_region(self):
        result = CourseraConnector._normalize_language("en-US")
        assert result is not None
        assert result.startswith("en")

    def test_none_input(self):
        assert CourseraConnector._normalize_language(None) is None

    def test_empty_string(self):
        assert CourseraConnector._normalize_language("") is None

    def test_list_input(self):
        result = CourseraConnector._normalize_language(["English", "Spanish"])
        assert result == "en"

    def test_dict_input(self):
        result = CourseraConnector._normalize_language({"name": "French"})
        assert result == "fr"


class TestCourseraNormalizeLevel:
    """Tests for CourseraConnector._normalize_level()."""

    def test_beginner(self):
        assert CourseraConnector._normalize_level("Beginner") == "Beginner"

    def test_intermediate(self):
        assert CourseraConnector._normalize_level("Intermediate Level") == "Intermediate"

    def test_advanced(self):
        assert CourseraConnector._normalize_level("Advanced") == "Advanced"

    def test_none(self):
        assert CourseraConnector._normalize_level(None) is None

    def test_list_input(self):
        assert CourseraConnector._normalize_level(["Beginner"]) == "Beginner"

    def test_unrecognised_value(self):
        assert CourseraConnector._normalize_level("something_else") is None


class TestCourseraNormalizeKeywords:
    """Tests for CourseraConnector._normalize_keywords()."""

    def test_string_passthrough(self):
        assert CourseraConnector._normalize_keywords("python,ml") == "python,ml"

    def test_list_of_strings(self):
        result = CourseraConnector._normalize_keywords(["Python", "Machine Learning"])
        assert result == "Python,Machine Learning"

    def test_list_of_dicts(self):
        result = CourseraConnector._normalize_keywords(
            [{"name": "AI"}, {"name": "ML"}]
        )
        assert result == "AI,ML"

    def test_none(self):
        assert CourseraConnector._normalize_keywords(None) is None


class TestCourseraHelpers:
    """Miscellaneous Coursera helper tests."""

    def test_split_keywords(self):
        result = CourseraConnector._split_keywords("python, ML, AI")
        assert result == ["python", "ML", "AI"]

    def test_split_keywords_none(self):
        assert CourseraConnector._split_keywords(None) == []

    def test_dedupe_preserve(self):
        result = CourseraConnector._dedupe_preserve(["A", "b", "a", "B", "C"])
        assert result == ["A", "b", "C"]

    def test_join_keywords_max_len(self):
        kws = ["a" * 100, "b" * 100, "c" * 100, "d" * 100, "e" * 100, "f" * 100]
        result = CourseraConnector._join_keywords(kws, max_len=250)
        assert result is not None
        assert len(result) <= 250

    def test_pick_first_keyword(self):
        assert CourseraConnector._pick_first_keyword("AI, ML, DL") == "AI"

    def test_pick_first_keyword_none(self):
        assert CourseraConnector._pick_first_keyword(None) is None

    def test_normalize_image_url_string(self):
        url = "https://img.example.com/pic.jpg"
        assert CourseraConnector._normalize_image_url(url) == url

    def test_normalize_image_url_dict(self):
        assert CourseraConnector._normalize_image_url(
            {"url": "https://img.example.com/pic.jpg"}
        ) == "https://img.example.com/pic.jpg"

    def test_normalize_image_url_none(self):
        assert CourseraConnector._normalize_image_url(None) is None


# ======================================================================
# MitOcwConnector
# ======================================================================

class TestMitOcwSlug:
    """Tests for MitOcwConnector._slug_from_url()."""

    def test_standard_url(self):
        assert MitOcwConnector._slug_from_url(
            "https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-fall-2010"
        ) == "6-042j-mathematics-for-computer-science-fall-2010"

    def test_non_course_url(self):
        assert MitOcwConnector._slug_from_url("https://ocw.mit.edu/about") == ""


class TestMitOcwIsCourseUrl:
    """Tests for MitOcwConnector._is_course_url()."""

    def test_valid_course_url(self):
        assert MitOcwConnector._is_course_url(
            "https://ocw.mit.edu/courses/6-042j-mathematics"
        ) is True

    def test_nested_path_rejected(self):
        assert MitOcwConnector._is_course_url(
            "https://ocw.mit.edu/courses/6-042j-mathematics/pages/syllabus"
        ) is False

    def test_wrong_host(self):
        assert MitOcwConnector._is_course_url(
            "https://example.com/courses/something"
        ) is False

    def test_root_courses_path(self):
        # Just "/courses/" with nothing after it
        assert MitOcwConnector._is_course_url(
            "https://ocw.mit.edu/courses/"
        ) is False


class TestMitOcwNormalizeLevel:
    """Tests for MitOcwConnector._normalize_level_value()."""

    def test_undergraduate(self):
        assert MitOcwConnector._normalize_level_value("Undergraduate") == "Beginner"

    def test_graduate(self):
        assert MitOcwConnector._normalize_level_value("Graduate") == "Advanced"

    def test_high_school(self):
        assert MitOcwConnector._normalize_level_value("High School") == "Beginner"

    def test_empty_string(self):
        assert MitOcwConnector._normalize_level_value("") is None

    def test_unrecognised(self):
        assert MitOcwConnector._normalize_level_value("something random") is None


class TestMitOcwNormalizeLanguage:
    """Tests for MitOcwConnector._normalize_language()."""

    def test_lowercase(self):
        assert MitOcwConnector._normalize_language("EN") == "en"

    def test_none(self):
        assert MitOcwConnector._normalize_language(None) is None

    def test_empty(self):
        assert MitOcwConnector._normalize_language("") is None


class TestMitOcwHelpers:
    """Miscellaneous MIT OCW helper tests."""

    def test_parse_dt_iso(self):
        dt = MitOcwConnector._parse_dt("2023-01-15T08:00:00Z")
        assert isinstance(dt, datetime)
        assert dt.year == 2023

    def test_parse_dt_none(self):
        assert MitOcwConnector._parse_dt(None) is None

    def test_normalize_keywords_list(self):
        result = MitOcwConnector._normalize_keywords(["Math", "Science"])
        assert result == "Math,Science"

    def test_normalize_keywords_dict(self):
        result = MitOcwConnector._normalize_keywords({"name": "Physics"})
        assert result == "Physics"

    def test_normalize_image_url_list(self):
        result = MitOcwConnector._normalize_image_url(
            ["https://img.example.com/a.jpg", "https://img.example.com/b.jpg"]
        )
        assert result == "https://img.example.com/a.jpg"

    def test_split_keywords(self):
        assert MitOcwConnector._split_keywords("a, b, c") == ["a", "b", "c"]

    def test_dedupe_preserve(self):
        assert MitOcwConnector._dedupe_preserve(["X", "x", "Y"]) == ["X", "Y"]
