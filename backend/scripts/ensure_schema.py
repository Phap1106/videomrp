"""Run simple, idempotent schema adjustments against the configured database.

Useful when Alembic migrations haven't been run (development/demo environments).
Usage:
    python scripts/ensure_schema.py
"""

from app.database import ensure_video_jobs_columns


if __name__ == "__main__":
    print("Ensuring video_jobs columns...")
    ensure_video_jobs_columns()
    print("Done.")
