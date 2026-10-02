import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

from app.event_bus import event_bus


class TaskManager:
    def __init__(self, max_workers=3):
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="CyberNova"
        )
        self.tasks = {}
        self.lock = threading.Lock()

    def submit(self, name, function, *args, **kwargs):
        task_id = str(uuid.uuid4())

        with self.lock:
            self.tasks[task_id] = {
                "name": name,
                "status": "queued",
                "result": None,
                "error": None,
            }

        event_bus.task_started.emit(task_id)

        future = self.executor.submit(
            self._run_task,
            task_id,
            function,
            args,
            kwargs
        )

        return task_id, future

    def _run_task(self, task_id, function, args, kwargs):
        with self.lock:
            self.tasks[task_id]["status"] = "running"

        try:
            result = function(*args, **kwargs)

            with self.lock:
                self.tasks[task_id]["status"] = "completed"
                self.tasks[task_id]["result"] = result

            event_bus.task_finished.emit(
                task_id,
                "completed"
            )

            return result

        except Exception as error:
            with self.lock:
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["error"] = str(error)

            event_bus.task_finished.emit(
                task_id,
                "failed"
            )

            raise

    def get_tasks(self):
        with self.lock:
            return {
                task_id: task.copy()
                for task_id, task in self.tasks.items()
            }

    def shutdown(self):
        self.executor.shutdown(
            wait=False,
            cancel_futures=True
        )