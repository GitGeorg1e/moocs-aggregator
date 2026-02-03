from __future__ import annotations

from backend.app.scripts.sync_coursera import run_sync as sync_coursera
from backend.app.scripts.sync_mit_ocw import run_sync as sync_mit_ocw


def run_all() -> None:
    sync_coursera()
    sync_mit_ocw()


if __name__ == "__main__":
    run_all()
