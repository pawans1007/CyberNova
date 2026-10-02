import sqlite3
from contextlib import closing
from pathlib import Path

from config import DATABASE_PATH


class ScanHistory:
    """Store and retrieve cybersecurity scan history."""

    def __init__(self, database_path=None):
        self.database_path = str(database_path or DATABASE_PATH)
        self._initialize_database()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _initialize_database(self):
        with closing(self._connect()) as connection:
            with connection:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS scan_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target TEXT NOT NULL,
                        status TEXT NOT NULL,
                        started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        finished_at TEXT,
                        summary TEXT DEFAULT '',
                        json_report TEXT DEFAULT '',
                        text_report TEXT DEFAULT '',
                        error TEXT DEFAULT ''
                    )
                """)

    def start_scan(self, target):
        """Create a record when a scan begins and return its ID."""
        with closing(self._connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO scan_history (target, status)
                    VALUES (?, 'running')
                    """,
                    (target,),
                )
                return cursor.lastrowid

    def complete_scan(
        self,
        scan_id,
        summary="",
        json_report="",
        text_report="",
    ):
        """Mark a scan successful and store its report paths."""
        with closing(self._connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE scan_history
                    SET status = 'completed',
                        finished_at = CURRENT_TIMESTAMP,
                        summary = ?,
                        json_report = ?,
                        text_report = ?,
                        error = ''
                    WHERE id = ?
                    """,
                    (
                        summary,
                        str(json_report),
                        str(text_report),
                        scan_id,
                    ),
                )
                return cursor.rowcount > 0

    def fail_scan(self, scan_id, error):
        """Mark a scan as failed."""
        with closing(self._connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE scan_history
                    SET status = 'failed',
                        finished_at = CURRENT_TIMESTAMP,
                        error = ?
                    WHERE id = ?
                    """,
                    (str(error), scan_id),
                )
                return cursor.rowcount > 0

    def list_scans(self, limit=100):
        """Return recent scan records, newest first."""
        limit = max(1, min(int(limit), 500))

        with closing(self._connect()) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT *
                FROM scan_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_scan(self, scan_id):
        """Return one scan record, or None if it does not exist."""
        with closing(self._connect()) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT *
                FROM scan_history
                WHERE id = ?
                """,
                (scan_id,),
            ).fetchone()

        return dict(row) if row else None

    def delete_scan(self, scan_id):
        """Delete a history record without deleting its report files."""
        with closing(self._connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM scan_history WHERE id = ?",
                    (scan_id,),
                )
                return cursor.rowcount > 0

    @staticmethod
    def report_exists(path):
        """Check whether a saved report path still exists."""
        return bool(path) and Path(path).is_file()
