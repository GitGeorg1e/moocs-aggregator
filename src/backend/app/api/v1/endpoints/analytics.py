from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.db import get_db
from backend.app.models.course import Course
from backend.app.models.source import Source
from backend.app.schemas.analytics import AnalyticsResponse

router = APIRouter()


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """Get aggregated analytics for all courses"""
    
    # Total courses
    total_courses = db.query(func.count(Course.id)).scalar() or 0
    
    # Courses by source - convert to object format
    by_source_query = (
        db.query(Source.name, func.count(Course.id).label('count'))
        .join(Course, Course.source_id == Source.id)
        .group_by(Source.name)
        .all()
    )
    courses_by_source = {name: count for name, count in by_source_query}
    
    # Courses by language - convert to object format
    by_language_query = (
        db.query(Course.language, func.count(Course.id).label('count'))
        .filter(Course.language.isnot(None))
        .group_by(Course.language)
        .order_by(func.count(Course.id).desc())
        .limit(10)
        .all()
    )
    courses_by_language = {lang or "Unknown": count for lang, count in by_language_query}
    
    # Courses by level - convert to object format
    by_level_query = (
        db.query(Course.level, func.count(Course.id).label('count'))
        .filter(Course.level.isnot(None))
        .group_by(Course.level)
        .all()
    )
    courses_by_level = {level or "Unknown": count for level, count in by_level_query}
    
    return {
        "totalCourses": total_courses,
        "coursesBySource": courses_by_source,
        "coursesByLanguage": courses_by_language,
        "coursesByLevel": courses_by_level,
        "recentlyAdded": 0,
        "topRatedCourses": []
    }