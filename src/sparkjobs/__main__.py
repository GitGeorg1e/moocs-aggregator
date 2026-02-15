"""
CLI entry point for Spark jobs.
Usage: python -m sparkjobs [similarity|clustering|analytics|all]
"""
from __future__ import annotations

import sys

from sparkjobs import (
    run_analytics_job,
    run_all_jobs,
    run_clustering_job,
    run_similarity_job,
)


def main() -> None:
    if len(sys.argv) > 1:
        job_name = sys.argv[1].lower()
        if job_name == "similarity":
            run_similarity_job()
        elif job_name == "clustering":
            run_clustering_job()
        elif job_name == "analytics":
            run_analytics_job()
        elif job_name == "all":
            run_all_jobs()
        else:
            print(f"Unknown job: {job_name}")
            print("Available jobs: similarity, clustering, analytics, all")
    else:
        print("Usage: python -m sparkjobs [similarity|clustering|analytics|all]")
        print("Running all jobs by default...")
        run_all_jobs()


if __name__ == "__main__":
    main()
