"""
Spark ML endpoints — trigger jobs and query Spark-generated results.
"""
from __future__ import annotations

import logging
import threading

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Spark job triggers ────────────────────────────────────────────────


@router.post("/run-similarity-job")
async def trigger_similarity_job(background: bool = True):
    """Trigger the Spark course-similarity job."""
    try:
        from sparkjobs import run_similarity_job

        if background:
            threading.Thread(target=run_similarity_job, daemon=True).start()
            return {"status": "started", "job": "similarity", "background": True}
        run_similarity_job()
        return {"status": "completed", "job": "similarity", "background": False}
    except Exception as e:
        logger.error(f"Error running similarity job: {e}")
        raise HTTPException(status_code=500, detail="Error running job")


@router.post("/run-clustering-job")
async def trigger_clustering_job(background: bool = True):
    """Trigger the Spark clustering job."""
    try:
        from sparkjobs import run_clustering_job

        if background:
            threading.Thread(target=run_clustering_job, daemon=True).start()
            return {"status": "started", "job": "clustering", "background": True}
        run_clustering_job()
        return {"status": "completed", "job": "clustering", "background": False}
    except Exception as e:
        logger.error(f"Error running clustering job: {e}")
        raise HTTPException(status_code=500, detail="Error running job")


@router.post("/run-analytics-job")
async def trigger_analytics_job(background: bool = True):
    """Trigger the Spark analytics job."""
    try:
        from sparkjobs import run_analytics_job

        if background:
            threading.Thread(target=run_analytics_job, daemon=True).start()
            return {"status": "started", "job": "analytics", "background": True}
        run_analytics_job()
        return {"status": "completed", "job": "analytics", "background": False}
    except Exception as e:
        logger.error(f"Error running analytics job: {e}")
        raise HTTPException(status_code=500, detail="Error running job")


# ── Cluster queries (read Spark results) ──────────────────────────────


@router.get("/clusters/{cluster_id}/courses")
async def get_cluster_courses(
    cluster_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get all courses belonging to a specific cluster."""
    try:
        query = """
        SELECT
            cc.course_id,
            cc.title,
            cc.topic,
            cc.level,
            c.image_url,
            c.language,
            s.name AS source_name
        FROM course_clusters cc
        LEFT JOIN courses c ON cc.course_id = c.id
        LEFT JOIN sources s ON c.source_id = s.id
        WHERE cc.cluster_id = :cluster_id
        LIMIT :limit
        """
        result = db.execute(text(query), {"cluster_id": cluster_id, "limit": limit})
        rows = result.fetchall()

        if not rows:
            return {"courses": [], "message": "Cluster not found"}

        courses = [
            {
                "id": row[0],
                "title": row[1],
                "topic": row[2],
                "level": row[3],
                "image_url": row[4],
                "language": row[5],
                "source": row[6],
            }
            for row in rows
        ]
        return {"cluster_id": cluster_id, "courses": courses, "count": len(courses)}

    except Exception as e:
        logger.error(f"Error fetching cluster courses: {e}")
        raise HTTPException(status_code=500, detail="Error fetching cluster courses")


@router.get("/clusters/stats")
async def get_cluster_statistics(db: Session = Depends(get_db)):
    """Get summary statistics for every cluster."""
    try:
        query = """
        SELECT
            cluster_id,
            COUNT(*) as num_courses,
            COUNT(DISTINCT topic) as num_topics,
            COUNT(DISTINCT level) as num_levels
        FROM course_clusters
        GROUP BY cluster_id
        ORDER BY num_courses DESC
        """
        result = db.execute(text(query))
        rows = result.fetchall()

        clusters = [
            {
                "cluster_id": row[0],
                "num_courses": row[1],
                "num_topics": row[2],
                "num_levels": row[3],
            }
            for row in rows
        ]
        return {"total_clusters": len(clusters), "clusters": clusters}

    except Exception as e:
        logger.error(f"Error fetching cluster stats: {e}")
        raise HTTPException(status_code=500, detail="Error fetching cluster statistics")


# ── Spark analytics queries ───────────────────────────────────────────


@router.get("/analytics/overview")
async def get_analytics_overview(db: Session = Depends(get_db)):
    """Overall analytics summary from Spark batch results."""
    try:
        sources = db.execute(
            text("SELECT COUNT(*), SUM(num_courses) FROM analytics_by_source")
        ).fetchone()
        languages = db.execute(
            text("SELECT COUNT(*) FROM analytics_by_language")
        ).fetchone()
        topics = db.execute(
            text("SELECT COUNT(*) FROM analytics_by_topic")
        ).fetchone()

        return {
            "total_courses": sources[1] if sources else 0,
            "num_sources": sources[0] if sources else 0,
            "num_languages": languages[0] if languages else 0,
            "num_topics": topics[0] if topics else 0,
        }
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")


@router.get("/analytics/by-source")
async def get_analytics_by_source(db: Session = Depends(get_db)):
    """Analytics breakdown by source."""
    try:
        query = """
        SELECT source_name, num_courses, num_languages, num_topics, num_levels
        FROM analytics_by_source
        ORDER BY num_courses DESC
        """
        rows = db.execute(text(query)).fetchall()
        return [
            {
                "source": row[0],
                "num_courses": row[1],
                "num_languages": row[2],
                "num_topics": row[3],
                "num_levels": row[4],
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error fetching source analytics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")


@router.get("/analytics/by-language")
async def get_analytics_by_language(db: Session = Depends(get_db)):
    """Analytics breakdown by language."""
    try:
        rows = db.execute(
            text("SELECT * FROM analytics_by_language ORDER BY num_courses DESC")
        ).fetchall()
        return [
            {
                "language": row[1],
                "num_courses": row[2],
                "num_sources": row[3],
                "num_topics": row[4],
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error fetching language analytics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")


@router.get("/analytics/by-topic")
async def get_analytics_by_topic(db: Session = Depends(get_db)):
    """Analytics breakdown by topic."""
    try:
        rows = db.execute(
            text("SELECT * FROM analytics_by_topic ORDER BY num_courses DESC")
        ).fetchall()
        return [
            {
                "topic": row[1],
                "num_courses": row[2],
                "num_sources": row[3],
                "num_languages": row[4],
                "num_levels": row[5],
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error fetching topic analytics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")
