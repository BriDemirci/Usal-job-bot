import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

class StorageRepository:
    def __init__(self, db_path: str | Path = "data/job_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    fit_score INTEGER NOT NULL,
                    recommendation TEXT NOT NULL,
                    reason TEXT,
                    status TEXT NOT NULL,
                    evaluated_at TEXT NOT NULL,
                    applied_at TEXT
                );
            """)
            conn.commit()

    def is_job_seen(self, job_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,))
            return cursor.fetchone() is not None

    def record_job_evaluation(
        self,
        job_id: str,
        title: str,
        company: str,
        score: int,
        recommendation: str,
        reason: str
    ) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO jobs 
                (job_id, title, company, fit_score, recommendation, reason, status, evaluated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                title,
                company,
                score,
                recommendation,
                reason,
                "EVALUATED",
                datetime.now().isoformat()
            ))
            conn.commit()

    def mark_as_applied(self, job_id: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET status = 'APPLIED', applied_at = ?
                WHERE job_id = ?
            """, (datetime.now().isoformat(), job_id))
            conn.commit()

    def mark_as_rejected(self, job_id: str, reason: str = "User skipped") -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET status = 'SKIPPED_BY_USER', reason = ?
                WHERE job_id = ?
            """, (reason, job_id))
            conn.commit()

    def get_applied_jobs_count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'APPLIED'")
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]
