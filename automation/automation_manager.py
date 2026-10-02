import logging

from automation.scheduler import CyberNovaScheduler
from memory.database import Database


logger = logging.getLogger(__name__)


class AutomationManager:
    def __init__(
        self,
        run_callback=None,
        database=None,
        scheduler=None,
    ):
        self.database = database or Database()
        self.scheduler = scheduler or CyberNovaScheduler()
        self.run_callback = run_callback

    def _execute(self, automation_id, name, prompt):
        logger.info(
            "Running automation %s (%s)",
            name,
            automation_id,
        )

        if self.run_callback is None:
            logger.warning(
                "No automation callback is configured."
            )
            return

        try:
            self.run_callback(
                automation_id,
                name,
                prompt,
            )
        except Exception:
            logger.exception(
                "Automation %s failed.",
                automation_id,
            )

    def create(
        self,
        name,
        prompt,
        interval_minutes,
        enabled=True,
    ):
        name = str(name).strip()
        prompt = str(prompt).strip()
        interval_minutes = int(interval_minutes)

        if not name or not prompt:
            return {
                "success": False,
                "error": "Name and prompt are required.",
            }

        if interval_minutes < 1:
            return {
                "success": False,
                "error": "Interval must be at least one minute.",
            }

        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO automations
                    (name, prompt, schedule, enabled)
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    prompt,
                    str(interval_minutes),
                    int(bool(enabled)),
                ),
            )

            automation_id = cursor.lastrowid

        if enabled:
            try:
                self._schedule(
                    automation_id,
                    name,
                    prompt,
                    interval_minutes,
                )
            except Exception as error:
                with self.database.connection() as connection:
                    connection.execute(
                        """
                        DELETE FROM automations
                        WHERE id = ?
                        """,
                        (automation_id,),
                    )

                return {
                    "success": False,
                    "error": str(error),
                }

        return {
            "success": True,
            "id": automation_id,
            "name": name,
            "interval_minutes": interval_minutes,
            "enabled": bool(enabled),
        }

    def _schedule(
        self,
        automation_id,
        name,
        prompt,
        interval_minutes,
    ):
        self.scheduler.add_interval_job(
            job_id=f"automation_{automation_id}",
            callback=self._execute,
            minutes=interval_minutes,
            args=[
                automation_id,
                name,
                prompt,
            ],
        )

    def list_automations(self):
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, name, prompt, schedule,
                       enabled, created_at
                FROM automations
                ORDER BY id DESC
                """
            ).fetchall()

        return [
            {
                **dict(row),
                "enabled": bool(row["enabled"]),
                "interval_minutes": int(row["schedule"]),
            }
            for row in rows
        ]

    def enable(self, automation_id):
        automation = self._get(automation_id)

        if automation is None:
            return False

        try:
            self._schedule(
                automation["id"],
                automation["name"],
                automation["prompt"],
                int(automation["schedule"]),
            )
        except Exception:
            logger.exception(
                "Could not enable automation %s",
                automation_id,
            )
            return False

        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE automations
                SET enabled = 1
                WHERE id = ?
                """,
                (int(automation_id),),
            )

        return True

    def disable(self, automation_id):
        automation_id = int(automation_id)

        self.scheduler.remove_job(
            f"automation_{automation_id}"
        )

        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE automations
                SET enabled = 0
                WHERE id = ?
                """,
                (automation_id,),
            )

        return cursor.rowcount > 0

    def delete(self, automation_id):
        automation_id = int(automation_id)

        self.scheduler.remove_job(
            f"automation_{automation_id}"
        )

        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                DELETE FROM automations
                WHERE id = ?
                """,
                (automation_id,),
            )

        return cursor.rowcount > 0

    def _get(self, automation_id):
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT id, name, prompt, schedule, enabled
                FROM automations
                WHERE id = ?
                """,
                (int(automation_id),),
            ).fetchone()

        return dict(row) if row else None

    def restore_enabled(self):
        automations = self.list_automations()
        restored = 0

        for item in automations:
            if not item["enabled"]:
                continue

            try:
                self._schedule(
                    item["id"],
                    item["name"],
                    item["prompt"],
                    item["interval_minutes"],
                )
                restored += 1
            except Exception:
                logger.exception(
                    "Could not restore automation %s",
                    item["id"],
                )

        return restored

    def shutdown(self):
        self.scheduler.shutdown(wait=False)