from __future__ import annotations

import asyncio
import uuid
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# In-memory task storage
_tasks: Dict[str, dict] = {}


class SyncService:
    """Service για sync με external sources (Coursera, MIT OCW)."""

    @classmethod
    async def start_coursera_sync(cls, max_courses: Optional[int] = None) -> dict:
        """Εκκίνηση Coursera sync σε background."""
        task_id = str(uuid.uuid4())

        _tasks[task_id] = {
            "task_id": task_id,
            "source": "coursera",
            "status": "running",
            "message": "Coursera sync started in background",
        }

        # Run in background
        asyncio.create_task(cls._run_coursera_sync(task_id, max_courses))

        return _tasks[task_id]

    @classmethod
    async def _run_coursera_sync(cls, task_id: str, max_courses: Optional[int]):
        """Background task για Coursera sync."""
        try:
            logger.info(f"Starting Coursera sync (task: {task_id})")

            # Import και εκτέλεση του sync script
            from backend.app.scripts.sync_coursera import run_sync
            
            # Run σε executor για να μην μπλοκάρει
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_sync)

            _tasks[task_id]["status"] = "completed"
            _tasks[task_id]["message"] = "Coursera sync completed successfully"
            logger.info(f"Coursera sync completed (task: {task_id})")

        except Exception as e:
            logger.error(f"Coursera sync failed: {e}")
            _tasks[task_id]["status"] = "failed"
            _tasks[task_id]["message"] = f"Sync failed: {str(e)}"

    @classmethod
    async def start_mit_ocw_sync(cls, max_courses: Optional[int] = None) -> dict:
        """Εκκίνηση MIT OpenCourseWare sync σε background."""
        task_id = str(uuid.uuid4())

        _tasks[task_id] = {
            "task_id": task_id,
            "source": "mit_ocw",
            "status": "running",
            "message": "MIT OpenCourseWare sync started in background",
        }

        asyncio.create_task(cls._run_mit_ocw_sync(task_id, max_courses))

        return _tasks[task_id]

    @classmethod
    async def _run_mit_ocw_sync(cls, task_id: str, max_courses: Optional[int]):
        """Background task για MIT OpenCourseWare sync."""
        try:
            logger.info(f"Starting MIT OpenCourseWare sync (task: {task_id})")

            from backend.app.scripts.sync_mit_ocw import run_sync

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_sync)

            _tasks[task_id]["status"] = "completed"
            _tasks[task_id]["message"] = "MIT OpenCourseWare sync completed successfully"
            logger.info(f"MIT OpenCourseWare sync completed (task: {task_id})")

        except Exception as e:
            logger.error(f"MIT OpenCourseWare sync failed: {e}")
            _tasks[task_id]["status"] = "failed"
            _tasks[task_id]["message"] = f"Sync failed: {str(e)}"

    @classmethod
    def get_task_status(cls, task_id: str) -> Optional[dict]:
        """Ανάκτηση status ενός sync task."""
        return _tasks.get(task_id)