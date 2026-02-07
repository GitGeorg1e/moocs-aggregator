"""
Quick Start Guide for Spark Jobs
Step-by-step setup and execution

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
   python -m sparkjobs.db_schema
   Or manually run the SQL in sparkjobs/db_schema.py using MySQL client.


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
   python -m sparkjobs similarity
   python -m sparkjobs clustering
   python -m sparkjobs analytics
   python -m sparkjobs all

B. Or programmatically:
   >>> from sparkjobs import run_all_jobs
   >>> run_all_jobs()


4. VERIFY RESULTS
=================

Check if results are saved in database:

mysql -u moocs_user -p -D moocs_db -e "SELECT * FROM similar_courses LIMIT 5;"
mysql -u moocs_user -p -D moocs_db -e "SELECT * FROM course_clusters LIMIT 5;"
mysql -u moocs_user -p -D moocs_db -e "SELECT * FROM analytics_by_source;"


5. EXAMPLE API CALLS
====================

# Get similar courses
curl "http://localhost:8000/api/v1/courses/1/similar?limit=5"

# Get courses in cluster
curl "http://localhost:8000/api/v1/spark/clusters/0/courses?limit=20"

# Get cluster statistics
curl "http://localhost:8000/api/v1/spark/clusters/stats"

# Get analytics overview
curl "http://localhost:8000/api/v1/spark/analytics/overview"

# Trigger similarity job
curl -X POST "http://localhost:8000/api/v1/spark/run-similarity-job?background=true"
"""

if __name__ == "__main__":
    print(__doc__)
