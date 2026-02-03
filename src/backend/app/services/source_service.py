from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.source import Source


def get_or_create_source(db: Session, name: str, base_url: str) -> Source:
    existing = db.execute(select(Source).where(Source.name == name)).scalar_one_or_none()
    if existing:
        if existing.base_url != base_url:
            existing.base_url = base_url
            db.commit()
            db.refresh(existing)
        return existing

    src = Source(name=name, base_url=base_url)
    db.add(src)
    db.commit()
    db.refresh(src)
    return src
