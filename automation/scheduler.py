import logging

from apscheduler.schedulers.background import BackgroundScheduler


logger = logging.getLogger(__name__)


class CyberNovaScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            daemon=True,
            timezone="Asia/Kolkata",
        )

        self._started = False

    def start(self):
        if not self._started:
            self.scheduler.start()
            self._started = True

    def add_interval_job(
        self,
        job_id,
        callback,
        minutes,
        args=None,
    ):
        minutes = int(minutes)

        if minutes < 1:
            raise ValueError(
                "Interval must be at least one minute."
            )

        if not self._started:
            self.start()

        self.scheduler.add_job(
            callback,
            trigger="interval",
            minutes=minutes,
            args=args or [],
            id=str(job_id),
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
        )

        return True

    def remove_job(self, job_id):
        try:
            self.scheduler.remove_job(str(job_id))
            return True
        except Exception:
            return False

    def pause_job(self, job_id):
        try:
            self.scheduler.pause_job(str(job_id))
            return True
        except Exception:
            return False

    def resume_job(self, job_id):
        try:
            self.scheduler.resume_job(str(job_id))
            return True
        except Exception:
            return False

    def list_jobs(self):
        return [
            {
                "id": job.id,
                "next_run_time": (
                    job.next_run_time.isoformat()
                    if job.next_run_time
                    else None
                ),
            }
            for job in self.scheduler.get_jobs()
        ]

    def shutdown(self, wait=False):
        if self._started:
            self.scheduler.shutdown(wait=wait)
            self._started = False