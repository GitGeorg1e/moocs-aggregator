"""
Quick Start Guide for Spark Jobs
Step-by-step setup and execution
"""

# ============== QUICK START GUIDE ==============

"""
1. INSTALLATION
================

A. Install dependencies:
   cd /path/to/moocs-aggregator
   uv sync
   # or: pip install -e .

B. Ensure MySQL is running:
   - Database: moocs_db
   - User: moocs_user
   - Password: 123456789
   - Host: localhost
   - Port: 3306

C. Create database tables:
   python db_schema.py
   
   Or manually run the SQL in db_schema.py using MySQL client.


2. ENVIRONMENT SETUP
====================

A. Set environment variables (Windows):
   set DB_HOST=localhost
   set DB_PORT=3306
   set DB_USER=moocs_user
   set DB_PASSWORD=123456789
   set DB_NAME=moocs_db
   set SPARK_MASTER=local[*]

B. Or create .env file in repo root:
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=moocs_user
   DB_PASSWORD=123456789
   DB_NAME=moocs_db
   SPARK_MASTER=local[*]
   NUM_CLUSTERS=10
   SIMILARITY_THRESHOLD=0.3


3. RUNNING SPARK JOBS
=====================

A. Run individual job:
   python __init__.py similarity      # Course similarity
   python __init__.py clustering      # Course clustering
   python __init__.py analytics       # Analytics
   python __init__.py all            # All jobs

B. Or using spark-submit (JDBC only):
   spark-submit --packages com.mysql:mysql-connector-j:8.4.0 course_similarity_job.py
   spark-submit --packages com.mysql:mysql-connector-j:8.4.0 clustering_job.py
   spark-submit --packages com.mysql:mysql-connector-j:8.4.0 analytics_job.py

C. Or programmatically:
   python
   >>> from sparkjobs import run_all_jobs
   >>> run_all_jobs()


4. VERIFY RESULTS
=================

Check if results are saved in database:

mysql -u moocs_user -p -D moocs_db -e "SELECT * FROM similar_courses LIMIT 5;"
mysql -u moocs_user -p -D moocs_db -e "SELECT * FROM course_clusters LIMIT 5;"
mysql -u moocs_user -p -D moocs_db -e "SELECT * FROM analytics_by_source;"


5. INTEGRATE WITH FASTAPI
==========================

A. Copy fastapi_integration.py to:
   backend/app/api/v1/endpoints/spark_analytics.py

B. Add to your main.py:
   from backend.app.api.v1.endpoints import spark_analytics
   app.include_router(spark_analytics.router)

C. Test endpoints:
   GET http://localhost:8000/api/v1/courses/1/similar
   GET http://localhost:8000/api/v1/clusters/0/courses
   GET http://localhost:8000/api/v1/analytics/overview
   POST http://localhost:8000/api/v1/spark/run-similarity-job


6. SCHEDULE JOBS (OPTIONAL)
===========================

Run periodic jobs:

   python job_scheduler.py

Or in your main app:
   from sparkjobs.job_scheduler import SparkJobScheduler
   from sparkjobs import run_similarity_job, run_clustering_job, run_analytics_job
   
   scheduler = SparkJobScheduler()
   scheduler.add_job(run_similarity_job, 6, "hours", "similarity")
   scheduler.add_job(run_clustering_job, 12, "hours", "clustering")
   scheduler.add_job(run_analytics_job, 1, "hours", "analytics")
   scheduler.start(background=True)


7. TROUBLESHOOTING
==================

A. "No module named 'pyspark'":
   pip install "pyspark>=4.0.1"

B. "Connection refused" (database):
   - Check MySQL is running
   - Verify DB_HOST, DB_PORT settings
   - Create database: mysql -u root -p -e "CREATE DATABASE moocs_db;"

C. "Out of memory":
   spark-submit --driver-memory 2g --executor-memory 4g course_similarity_job.py

D. "Table already exists":
   - First run creates tables, subsequent runs use 'overwrite' mode
   - To reset: DROP TABLE IF EXISTS similar_courses CASCADE;

E. Slow performance:
   - Increase NUM_CLUSTERS for clustering
   - Increase SIMILARITY_THRESHOLD to reduce pairs
   - Use Parquet format instead of CSV


8. OUTPUT FILES
===============

Results saved to:
- /tmp/spark_output/similarity_results/     (CSV)
- /tmp/spark_output/clustering_results/     (CSV + models)
- /tmp/spark_output/analytics_results/      (CSV)
- /tmp/spark_output/tfidf_model/           (Trained TF-IDF model)

Configure with:
   export SPARK_OUTPUT_DIR=/path/to/output


9. DATABASE SCHEMA
==================

similar_courses:
  - course_id (FK to courses)
  - similar_course_id (FK to courses)
  - similarity (0.0-1.0)
  - similar_course_title
  - similar_course_topic

course_clusters:
  - course_id (FK to courses)
  - cluster_id (0 to NUM_CLUSTERS-1)
  - title
  - topic
  - level

analytics_by_*:
  - Various aggregations by source, language, level, topic


10. MONITORING
==============

Check logs:
   tail -f /tmp/spark_output/logs/*.log

Monitor Spark UI:
   - Similarity: http://localhost:4040
   - Clustering: http://localhost:4041
   - Analytics: http://localhost:4042

Check database size:
   mysql -u moocs_user -p -D moocs_db -e "
   SELECT table_name,
          ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
   FROM information_schema.tables
   WHERE table_schema = 'moocs_db'
   ORDER BY size_mb DESC;"


11. PERFORMANCE TIPS
====================

For large datasets (>100k courses):

A. Partitioning:
   # In spark_utils.py, modify read_courses_from_db:
   .option("numPartitions", 20)
   .option("partitionColumn", "id")
   .option("lowerBound", 1)
   .option("upperBound", 1000000)

B. Use Parquet format:
   saver.save_to_parquet(df, path)

C. Enable adaptive execution:
   Already configured in config.py

D. Increase heap:
   spark-submit --driver-memory 4g --executor-memory 8g

E. Reduce TF-IDF features:
   export MIN_TF_IDF_FEATURES=50


12. EXAMPLE API CALLS
====================

# Get similar courses
curl "http://localhost:8000/api/v1/courses/1/similar?limit=5"

# Get courses in cluster
curl "http://localhost:8000/api/v1/clusters/0/courses?limit=20"

# Get cluster statistics
curl "http://localhost:8000/api/v1/clusters/stats"

# Get analytics overview
curl "http://localhost:8000/api/v1/analytics/overview"

# Get analytics by source
curl "http://localhost:8000/api/v1/analytics/by-source"

# Trigger similarity job
curl -X POST "http://localhost:8000/api/v1/spark/run-similarity-job?background=true"

"""

# ============== EXAMPLE: MANUAL SETUP ==============

def manual_setup_example():
    """
    Example of manual setup without using __init__.py
    """
    import logging
    from config import SparkConfig
    from .spark_utils import SparkSessionManager, DataFrameLoader, DataFrameSaver
    from .course_similarity_job import CourseSimilarityJob
    
    # Setup
    logging.basicConfig(level=logging.INFO)
    
    # Option 1: Run similarity job
    print("Option 1: Running Similarity Job")
    similarity_job = CourseSimilarityJob()
    similarity_job.run()
    
    # Option 2: Manual Spark operations
    print("Option 2: Manual Spark Operations")
    spark = SparkSessionManager.get_or_create_spark_session()
    
    # Load courses
    courses_df = DataFrameLoader.read_courses_from_db(spark)
    print(f"Loaded {courses_df.count()} courses")
    
    # Show schema
    courses_df.printSchema()
    
    # Show sample data
    courses_df.show(5)
    
    # Save to CSV
    saver = DataFrameSaver()
    saver.save_to_csv(courses_df, "/tmp/courses_sample")
    
    # Cleanup
    SparkSessionManager.stop_spark_session()


if __name__ == "__main__":
    print(__doc__)
