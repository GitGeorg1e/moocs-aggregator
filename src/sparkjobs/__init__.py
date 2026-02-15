"""
PySpark Jobs Package
Main module for running Spark jobs on course data.
"""
from .course_similarity_job import CourseSimilarityJob
from .clustering_job import CourseClusteringJob
from .analytics_job import AnalyticsJob
from .spark_utils import SparkSessionManager, setup_logging
import logging

logger = logging.getLogger(__name__)


def run_similarity_job(stop_session: bool = True):
    """Run course similarity job."""
    setup_logging()
    try:
        job = CourseSimilarityJob()
        job.run()
    except Exception as e:
        logger.error(f"Similarity job failed: {e}")
        raise
    finally:
        if stop_session:
            SparkSessionManager.stop_spark_session()


def run_clustering_job(stop_session: bool = True):
    """Run course clustering job."""
    setup_logging()
    try:
        job = CourseClusteringJob()
        job.run()
    except Exception as e:
        logger.error(f"Clustering job failed: {e}")
        raise
    finally:
        if stop_session:
            SparkSessionManager.stop_spark_session()


def run_analytics_job(stop_session: bool = True):
    """Run analytics job."""
    setup_logging()
    try:
        job = AnalyticsJob()
        job.run()
    except Exception as e:
        logger.error(f"Analytics job failed: {e}")
        raise
    finally:
        if stop_session:
            SparkSessionManager.stop_spark_session()


def run_all_jobs():
    """Run all Spark jobs in sequence."""
    setup_logging()
    logger.info("Starting all Spark jobs")
    
    try:
        logger.info("=" * 50)
        logger.info("Running Similarity Job")
        logger.info("=" * 50)
        run_similarity_job(stop_session=False)
        
        logger.info("=" * 50)
        logger.info("Running Clustering Job")
        logger.info("=" * 50)
        run_clustering_job(stop_session=False)
        
        logger.info("=" * 50)
        logger.info("Running Analytics Job")
        logger.info("=" * 50)
        run_analytics_job(stop_session=False)
        
        logger.info("=" * 50)
        logger.info("All jobs completed successfully!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Job pipeline failed: {e}")
        raise
    finally:
        SparkSessionManager.stop_spark_session()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        job_name = sys.argv[1].lower()
        if job_name == "similarity":
            run_similarity_job()
        elif job_name == "clustering":
            run_clustering_job()
        elif job_name == "analytics":
            run_analytics_job()
        elif job_name == "all":
            run_all_jobs()
        else:
            print(f"Unknown job: {job_name}")
            print("Available jobs: similarity, clustering, analytics, all")
    else:
        print("Usage: python __init__.py [similarity|clustering|analytics|all]")
        print("Running all jobs by default...")
        run_all_jobs()
