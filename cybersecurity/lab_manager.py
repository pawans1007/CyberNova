import ipaddress
import sqlite3
from contextlib import closing

from config import DATABASE_PATH


class LabManager:
    """Manage authorized cybersecurity lab targets with SQLite persistence."""

    def __init__(self, database_path=None):
        self.database_path = str(database_path or DATABASE_PATH)
        self._initialize_database()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _initialize_database(self):
        with closing(self._connect()) as connection:
            with connection:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS lab_targets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target TEXT NOT NULL UNIQUE,
                        description TEXT DEFAULT '',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

    @staticmethod
    def _normalize_target(target):
        """Validate and normalize a private or loopback IPv4/IPv6 target."""
        if not isinstance(target, str) or not target.strip():
            raise ValueError("Target cannot be empty.")

        try:
            parsed = ipaddress.ip_network(target.strip(), strict=False)
        except ValueError as exc:
            raise ValueError(
                "Enter a valid IP address or network."
            ) from exc

        if not (parsed.is_private or parsed.is_loopback):
            raise ValueError(
                "Only private or loopback lab targets are allowed."
            )

        if parsed.version == 4 and parsed.prefixlen < 24:
            raise ValueError(
                "IPv4 networks must use /24 or a narrower scope."
            )

        if parsed.version == 6 and parsed.prefixlen < 120:
            raise ValueError(
                "IPv6 networks must use /120 or a narrower scope."
            )

        return str(parsed)

    def add_target(self, target, description=""):
        """Register a target and save it permanently."""
        normalized = self._normalize_target(target)
        clean_description = str(description or "").strip()

        with closing(self._connect()) as connection:
            with connection:
                try:
                    connection.execute(
                        """
                        INSERT INTO lab_targets (target, description)
                        VALUES (?, ?)
                        """,
                        (normalized, clean_description),
                    )
                except sqlite3.IntegrityError as exc:
                    raise ValueError(
                        "This target is already registered."
                    ) from exc

        return normalized

    def list_targets(self):
        """Return registered targets as strings for UI compatibility."""
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT target FROM lab_targets ORDER BY target"
            ).fetchall()

        return [row[0] for row in rows]

    def list_target_details(self):
        """Return target details for displays that need descriptions."""
        with closing(self._connect()) as connection:
            rows = connection.execute("""
                SELECT target, description, created_at
                FROM lab_targets
                ORDER BY target
            """).fetchall()

        return [
            {
                "target": row[0],
                "description": row[1],
                "created_at": row[2],
            }
            for row in rows
        ]

    def is_authorized(self, target):
        """Check whether a target is contained within a registered scope."""
        try:
            requested = ipaddress.ip_network(
                target.strip(), strict=False
            )
        except (ValueError, AttributeError):
            return False

        if not (requested.is_private or requested.is_loopback):
            return False

        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT target FROM lab_targets"
            ).fetchall()

        for (registered_target,) in rows:
            try:
                registered = ipaddress.ip_network(
                    registered_target, strict=False
                )

                if (
                    requested.version == registered.version
                    and requested.subnet_of(registered)
                ):
                    return True

            except ValueError:
                continue

        return False

    def remove_target(self, target):
        """Remove a registered target."""
        normalized = self._normalize_target(target)

        with closing(self._connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM lab_targets WHERE target = ?",
                    (normalized,),
                )
                return cursor.rowcount > 0
