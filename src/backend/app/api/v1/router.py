from fastapi import APIRouter

from backend.app.api.v1.endpoints import courses, sync, analytics, spark

api_router = APIRouter()

api_router.include_router(
    courses.router,
    prefix="/courses",
    tags=["courses"],
)

api_router.include_router(
    sync.router,
    prefix="/sync",
    tags=["sync"],
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"],
)

api_router.include_router(
    spark.router,
    prefix="/spark",
    tags=["spark-ml"],
)
