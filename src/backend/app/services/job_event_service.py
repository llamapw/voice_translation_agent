from queue import Empty, Queue
from threading import Lock
from typing import Dict, Optional

from app.models.job_event import JobEvent


class JobEventService:
    def __init__(self) -> None:
        self._queues: Dict[str, Queue] = {}
        self._lock = Lock()

    def _get_queue(self, job_id: str) -> Queue:
        with self._lock:
            if job_id not in self._queues:
                self._queues[job_id] = Queue()
            return self._queues[job_id]

    def publish(self, event: JobEvent) -> None:
        self._get_queue(event.job_id).put(event)

    def next_event(self, job_id: str, timeout: float = 15.0) -> Optional[JobEvent]:
        try:
            return self._get_queue(job_id).get(timeout=timeout)
        except Empty:
            return None

    def close(self, job_id: str) -> None:
        self.publish(JobEvent.closed(job_id))


job_event_service = JobEventService()
