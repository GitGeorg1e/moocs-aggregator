"""
FastAPI Integration Example
Shows how to integrate Spark job results with FastAPI backend
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import logging

from backend.app.core.db import get_db

logger = logging.getLogger(__name__)

# This would be in your backend app/api/v1/endpoints/

router = APIRouter(prefix="/api/v1", tags=["spark-results"])


@router.get("/courses/{course_id}/similar")
async def get_similar_courses(
    course_id: int,
    limit: int = Query(5, ge=1, le=20),
    threshold: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    """
    Get similar courses for a given course using Spark similarity results.
    
    Args:
        course_id: Course ID
        limit: Number of similar courses to return (1-20)
        threshold: Minimum similarity score filter
        db: Database session
    
    Returns:
        List of similar courses with similarity scores
    """
    try:
        query = """
        SELECT 
            sc.similar_course_id,
            sc.similar_course_title,
            sc.similar_course_topic,
            sc.similarity,
            c.image_url,
            c.language,
            c.level
        FROM similar_courses sc
        LEFT JOIN courses c ON sc.similar_course_id = c.id
        WHERE sc.course_id = :course_id
        """
        
        if threshold:
            query += f" AND sc.similarity >= {threshold}"
        
        query += f" ORDER BY sc.similarity DESC LIMIT {limit}"
        
        result = db.execute(text(query), {"course_id": course_id})
        rows = result.fetchall()
        
        if not rows:
            return {"similar_courses": [], "message": "No similar courses found"}
        
        similar_courses = [
            {
                "id": row[0],
                "title": row[1],
                "topic": row[2],
                "similarity": float(row[3]),
                "image_url": row[4],
                "language": row[5],
                "level": row[6]
            }
            for row in rows
        ]
        
        return {
            "course_id": course_id,
            "similar_courses": similar_courses,
            "count": len(similar_courses)
        }
        
    except Exception as e:
        logger.error(f"Error fetching similar courses: {e}")
        raise HTTPException(status_code=500, detail="Error fetching similar courses")


@router.get("/clusters/{cluster_id}/courses")
async def get_cluster_courses(
    cluster_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Get all courses in a specific cluster.
    
    Args:
        cluster_id: Cluster ID
        limit: Maximum number of courses to return
        db: Database session
    
    Returns:
        List of courses in the cluster
    """
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
        
        result = db.execute(
            text(query),
            {"cluster_id": cluster_id, "limit": limit}
        )
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
                "source": row[6]
            }
            for row in rows
        ]
        
        return {
            "cluster_id": cluster_id,
            "courses": courses,
            "count": len(courses)
        }
        
    except Exception as e:
        logger.error(f"Error fetching cluster courses: {e}")
        raise HTTPException(status_code=500, detail="Error fetching cluster courses")


@router.get("/clusters/stats")
async def get_cluster_statistics(db: Session = Depends(get_db)):
    """
    Get statistics about all clusters.
    
    Returns:
        Cluster statistics
    """
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
        
        if not rows:
            return {"clusters": []}
        
        clusters = [
            {
                "cluster_id": row[0],
                "num_courses": row[1],
                "num_topics": row[2],
                "num_levels": row[3]
            }
            for row in rows
        ]
        
        return {
            "total_clusters": len(clusters),
            "clusters": clusters
        }
        
    except Exception as e:
        logger.error(f"Error fetching cluster stats: {e}")
        raise HTTPException(status_code=500, detail="Error fetching cluster statistics")


@router.get("/analytics/overview")
async def get_analytics_overview(db: Session = Depends(get_db)):
    """
    Get overall analytics summary.
    
    Returns:
        Analytics overview
    """
    try:
        # Get source stats
        sources_query = """
        SELECT COUNT(*) as num_sources, SUM(num_courses) as total_courses
        FROM analytics_by_source
        """
        sources_result = db.execute(text(sources_query))
        sources_row = sources_result.fetchone()
        
        # Get language stats
        languages_query = """
        SELECT COUNT(*) as num_languages
        FROM analytics_by_language
        """
        languages_result = db.execute(text(languages_query))
        languages_row = languages_result.fetchone()
        
        # Get topic stats
        topics_query = """
        SELECT COUNT(*) as num_topics
        FROM analytics_by_topic
        """
        topics_result = db.execute(text(topics_query))
        topics_row = topics_result.fetchone()
        
        return {
            "total_courses": sources_row[1] if sources_row else 0,
            "num_sources": sources_row[0] if sources_row else 0,
            "num_languages": languages_row[0] if languages_row else 0,
            "num_topics": topics_row[0] if topics_row else 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")


@router.get("/analytics/by-source")
async def get_analytics_by_source(db: Session = Depends(get_db)):
    """Get analytics breakdown by source."""
    try:
        query = "SELECT * FROM analytics_by_source ORDER BY num_courses DESC"
        result = db.execute(text(query))
        rows = result.fetchall()
        
        return [
            {
                "source": row[1],
                "num_courses": row[2],
                "num_languages": row[3],
                "num_topics": row[4],
                "num_levels": row[5]
            }
            for row in rows
        ]
        
    except Exception as e:
        logger.error(f"Error fetching source analytics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")


@router.get("/analytics/by-language")
async def get_analytics_by_language(db: Session = Depends(get_db)):
    """Get analytics breakdown by language."""
    try:
        query = "SELECT * FROM analytics_by_language ORDER BY num_courses DESC"
        result = db.execute(text(query))
        rows = result.fetchall()
        
        return [
            {
                "language": row[1],
                "num_courses": row[2],
                "num_sources": row[3],
                "num_topics": row[4]
            }
            for row in rows
        ]
        
    except Exception as e:
        logger.error(f"Error fetching language analytics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")


@router.get("/analytics/by-topic")
async def get_analytics_by_topic(db: Session = Depends(get_db)):
    """Get analytics breakdown by topic."""
    try:
        query = "SELECT * FROM analytics_by_topic ORDER BY num_courses DESC"
        result = db.execute(text(query))
        rows = result.fetchall()
        
        return [
            {
                "topic": row[1],
                "num_courses": row[2],
                "num_sources": row[3],
                "num_languages": row[4],
                "num_levels": row[5]
            }
            for row in rows
        ]
        
    except Exception as e:
        logger.error(f"Error fetching topic analytics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")


@router.post("/spark/run-similarity-job")
async def trigger_similarity_job(background: bool = True):
    """
    Trigger the Spark similarity job (admin endpoint).
    
    Args:
        background: Run in background if True
    
    Returns:
        Job status
    """
    try:
        from sparkjobs import run_similarity_job
        import threading
        
        if background:
            thread = threading.Thread(target=run_similarity_job, daemon=True)
            thread.start()
            return {"status": "started", "job": "similarity", "background": True}
        else:
            run_similarity_job()
            return {"status": "completed", "job": "similarity", "background": False}
            
    except Exception as e:
        logger.error(f"Error running similarity job: {e}")
        raise HTTPException(status_code=500, detail="Error running job")


@router.post("/spark/run-clustering-job")
async def trigger_clustering_job(background: bool = True):
    """Trigger the Spark clustering job."""
    try:
        from sparkjobs import run_clustering_job
        import threading
        
        if background:
            thread = threading.Thread(target=run_clustering_job, daemon=True)
            thread.start()
            return {"status": "started", "job": "clustering", "background": True}
        else:
            run_clustering_job()
            return {"status": "completed", "job": "clustering", "background": False}
            
    except Exception as e:
        logger.error(f"Error running clustering job: {e}")
        raise HTTPException(status_code=500, detail="Error running job")


@router.post("/spark/run-analytics-job")
async def trigger_analytics_job(background: bool = True):
    """Trigger the Spark analytics job."""
    try:
        from sparkjobs import run_analytics_job
        import threading
        
        if background:
            thread = threading.Thread(target=run_analytics_job, daemon=True)
            thread.start()
            return {"status": "started", "job": "analytics", "background": True}
        else:
            run_analytics_job()
            return {"status": "completed", "job": "analytics", "background": False}
            
    except Exception as e:
        logger.error(f"Error running analytics job: {e}")
        raise HTTPException(status_code=500, detail="Error running job")


# Include this router in your main app
# app.include_router(router)
