from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
from backend.app.connectors.mit_ocw import MitOcwConnector
from backend.app.core.db import SessionLocal
from backend.app.services.course_import import upsert_courses
from backend.app.services.source_service import get_or_create_source


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    return int(v) if v else default


def _env_str(name: str, default: str) -> str:
    return os.getenv(name) or default


def _parse_since(v: Optional[str]) -> Optional[datetime]:
    if not v:
        return None
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


def _parse_sitemap_list(v: str) -> list[str]:
    return [item.strip() for item in v.split(",") if item.strip()]


def run_sync(since: Optional[str] = None) -> None:
    since_dt = _parse_since(since)

    db = SessionLocal()
    try:
        src = get_or_create_source(
            db, name="MIT OpenCourseWare", base_url="https://ocw.mit.edu"
        )

        connector = MitOcwConnector(
            source_id=src.id,
            sitemap_index_url=_env_str("MIT_OCW_SITEMAP_INDEX", "https://ocw.mit.edu/sitemap.xml"),
            sitemap_urls=_parse_sitemap_list(
                _env_str("MIT_OCW_SITEMAPS", "https://ocw.mit.edu/sitemap-www.xml")
            ),
            max_urls=_env_int("MIT_OCW_MAX_URLS", 5000),
            timeout_s=_env_int("HTTP_TIMEOUT_S", 30),
            sleep_ms=_env_int("HTTP_SLEEP_MS", 200),
            max_retries=_env_int("HTTP_MAX_RETRIES", 5),
        )

        courses = list(connector.fetch_courses(since=since_dt))
        upsert_courses(db, courses, since=since_dt)
        print(f"MIT OpenCourseWare sync: {len(courses)} courses processed.")
    finally:
        db.close()


if __name__ == "__main__":
    run_sync()
