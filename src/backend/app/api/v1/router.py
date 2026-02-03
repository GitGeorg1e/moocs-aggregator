from fastapi import APIRouter

from backend.app.api.v1.endpoints import courses, sync, analytics, spark

# Import Spark integration router
import sys
sys.path.append("../../sparkjobs")
try:
    from sparkjobs.fastapi_integration import router as spark_router
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False

api_router = APIRouter()

api_router.include_router(
    courses.router,
    prefix="/courses",
    tags=["courses"]
)

api_router.include_router(
    sync.router,
    prefix="/sync",
    tags=["sync"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

# Add Spark endpoints if available
if SPARK_AVAILABLE:
    api_router.include_router(
        spark_router,
        prefix="/spark",
        tags=["spark-ml"]
    )