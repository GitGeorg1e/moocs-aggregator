from __future__ import annotations

import math
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_db
from backend.app.services.course_service import CourseService
from backend.app.models.course import Course
from backend.app.models.source import Source
from backend.app.schemas.course import (
    CourseResponse,
    CourseDetailResponse,
    CourseListResponse,
    SimilarCourseResponse,
    PaginationMeta,
)

router = APIRouter()


@router.get("/filters")
async def get_filter_options(db: Session = Depends(get_db)):
    """Get available filter options from database"""
    
    # Get unique languages
    languages_query = db.query(Course.language).filter(Course.language.isnot(None)).distinct().all()
    languages = [lang[0] for lang in languages_query if lang[0] and lang[0].strip()]
    
    # Get unique levels
    levels_query = db.query(Course.level).filter(Course.level.isnot(None)).distinct().all()
    levels = [level[0] for level in levels_query if level[0] and level[0].strip()]
    
    # Get unique sources
    sources_query = db.query(Source.name).distinct().all()
    sources = [source[0] for source in sources_query if source[0] and source[0].strip()]
    
    # Get unique topics
    topics_query = db.query(Course.topic).filter(Course.topic.isnot(None)).distinct().all()
    topics = [topic[0] for topic in topics_query if topic[0] and topic[0].strip()]
    
    return {
        "languages": sorted(languages),
        "levels": sorted(levels),
        "sources": sorted(sources),
        "topics": sorted(topics)
    }


@router.get(
    "",
    response_model=CourseListResponse,
    summary="Λίστα μαθημάτων με αναζήτηση και φίλτρα",
)
async def get_courses(
    q: Optional[str] = Query(None, description="Search query"),
    search: Optional[str] = Query(None, description="Search query (alias for q)"),
    language: Optional[str] = Query(None, description="Φίλτρο γλώσσας"),
    level: Optional[str] = Query(None, description="Φίλτρο επιπέδου"),
    source: Optional[str] = Query(None, description="Φίλτρο πηγής (coursera, mit_ocw)"),
    topic: Optional[str] = Query(None, description="Φίλτρο θεματικής περιοχής"),
    page: int = Query(1, ge=1, description="Αριθμός σελίδας"),
    per_page: int = Query(20, ge=1, le=100, description="Αποτελέσματα ανά σελίδα"),
    db: Session = Depends(get_db),
):
    """Ανάκτηση λίστας μαθημάτων."""
    # Use search if q is not provided
    search_query = q or search
    
    service = CourseService(db)
    courses, total = service.get_courses(
        q=search_query,
        language=language,
        level=level,
        source=source,
        topic=topic,
        page=page,
        per_page=per_page,
    )

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    course_responses = []
    for course in courses:
        source_name = service.get_source_name(course.source_id)
        course_responses.append(
            CourseResponse(
                id=course.id,
                source_id=course.source_id,
                source_name=source_name,
                source_course_id=course.source_course_id,
                title=course.title,
                short_description=course.short_description,
                topic=course.topic,
                language=course.language,
                level=course.level,
                course_url=course.course_url,
                image_url=course.image_url,
            )
        )

    return CourseListResponse(
        data=course_responses,
        meta=PaginationMeta(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/{course_id}",
    response_model=CourseDetailResponse,
    summary="Λεπτομέρειες μαθήματος",
)
async def get_course(
    course_id: int,
    db: Session = Depends(get_db),
):
    """Ανάκτηση πλήρων στοιχείων μαθήματος."""
    service = CourseService(db)
    course = service.get_course_by_id(course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    source_name = course.source.name if course.source else None
    cluster_id = service.get_course_cluster_id(course_id)

    return CourseDetailResponse(
        id=course.id,
        source_id=course.source_id,
        source_name=source_name,
        source_course_id=course.source_course_id,
        title=course.title,
        short_description=course.short_description,
        full_description=course.full_description,
        keywords=course.keywords,
        topic=course.topic,
        language=course.language,
        level=course.level,
        course_url=course.course_url,
        enrollment_url=course.enrollment_url,
        image_url=course.image_url,
        cluster_id=cluster_id,
        last_updated_at_source=course.last_updated_at_source,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )


@router.get(
    "/{course_id}/similar",
    response_model=List[SimilarCourseResponse],
    summary="Παρόμοια μαθήματα (Spark results)",
)
async def get_similar_courses(
    course_id: int,
    top_k: int = Query(10, ge=1, le=50, description="Αριθμός παρόμοιων"),
    db: Session = Depends(get_db),
):
    """Ανάκτηση παρόμοιων μαθημάτων από Spark TF-IDF analysis."""
    service = CourseService(db)

    course = service.get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    similar = service.get_similar_courses(course_id, top_k=top_k)

    return [SimilarCourseResponse(**c) for c in similar]