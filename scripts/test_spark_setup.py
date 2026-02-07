"""
Test script to verify Spark setup and connections.
Run this before running actual jobs.

Usage:
    python scripts/test_spark_setup.py
"""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test if all required libraries are installed."""
    logger.info("Testing imports...")

    try:
        import pyspark
        logger.info(f"✓ PySpark {pyspark.__version__}")
    except ImportError as e:
        logger.error(f"✗ PySpark import failed: {e}")
        return False

    try:
        import pandas as pd
        logger.info(f"✓ Pandas {pd.__version__}")
    except ImportError as e:
        logger.error(f"✗ Pandas import failed: {e}")
        return False

    try:
        import sqlalchemy
        logger.info(f"✓ SQLAlchemy {sqlalchemy.__version__}")
    except ImportError as e:
        logger.error(f"✗ SQLAlchemy import failed: {e}")
        return False

    try:
        import pymysql
        logger.info("✓ pymysql installed")
    except ImportError as e:
        logger.error(f"✗ pymysql import failed: {e}")
        return False

    return True


def test_spark_session():
    """Test Spark session creation."""
    logger.info("\nTesting Spark session creation...")

    try:
        from sparkjobs.spark_utils import SparkSessionManager, setup_logging

        setup_logging()
        spark = SparkSessionManager.get_or_create_spark_session("test-app")
        logger.info(f"✓ Spark session created: {spark.version}")

        df = spark.createDataFrame([(1, "test"), (2, "data")], ["id", "value"])
        logger.info(f"✓ Created test DataFrame with {df.count()} rows")

        SparkSessionManager.stop_spark_session()
        logger.info("✓ Spark session closed")
        return True

    except Exception as e:
        logger.error(f"✗ Spark session test failed: {e}")
        return False


def test_database_connection():
    """Test database connection."""
    logger.info("\nTesting database connection...")

    try:
        from sparkjobs.config import SparkConfig
        from sqlalchemy import create_engine, text

        logger.info(f"Database URL: {SparkConfig.DB_URL}")
        engine = create_engine(SparkConfig.DB_URL)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"✓ Database connection successful: {result.fetchone()}")

            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_name='courses'"
                )
            )
            table_exists = result.fetchone()[0] > 0
            if table_exists:
                logger.info("✓ Courses table exists")
                result = conn.execute(text("SELECT COUNT(*) FROM courses"))
                count = result.fetchone()[0]
                logger.info(f"✓ Found {count} courses in database")
            else:
                logger.warning(
                    "⚠ Courses table does not exist – run the backend first"
                )

        return True

    except Exception as e:
        logger.error(f"✗ Database connection test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Spark Jobs – Verification Tests")
    logger.info("=" * 60)

    all_passed = True

    if not test_imports():
        all_passed = False
        logger.warning("\n⚠ Install missing packages: uv sync")

    if not test_spark_session():
        all_passed = False

    if not test_database_connection():
        all_passed = False
        logger.warning("\n⚠ Database connection failed. Check MySQL is running.")

    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✓ All tests passed! You can now run Spark jobs.")
        logger.info("\nRun with: python -m sparkjobs all")
    else:
        logger.error("✗ Some tests failed. See above for details.")
        sys.exit(1)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
