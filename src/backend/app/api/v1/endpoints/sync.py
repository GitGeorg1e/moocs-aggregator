from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.schemas.course import SyncSource, SyncRequest, SyncResponse
from backend.app.services.sync_service import SyncService

router = APIRouter()


@router.post(
    "/{source}",
    response_model=SyncResponse,
    summary="Εκκίνηση sync με external source",
    description="""
    Ξεκινά background harvesting από την επιλεγμένη πηγή.
    Επιστρέφει task_id για tracking του status.
    """,
)
async def start_sync(
    source: SyncSource,
    request: SyncRequest = SyncRequest(),
):
    """Εκκίνηση sync με Coursera ή MIT OpenCourseWare."""
    try:
        if source == SyncSource.coursera:
            result = await SyncService.start_coursera_sync(
                max_courses=request.max_courses
            )
        elif source == SyncSource.mit_ocw:
            result = await SyncService.start_mit_ocw_sync(
                max_courses=request.max_courses
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown source: {source}")

        return SyncResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status/{task_id}",
    summary="Status sync task",
)
async def get_sync_status(task_id: str):
    """Ανάκτηση status ενός sync task."""
    status = SyncService.get_task_status(task_id)

    if not status:
        raise HTTPException(status_code=404, detail="Task not found")

    return status