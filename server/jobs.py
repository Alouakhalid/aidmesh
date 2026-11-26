"""In-memory job store. A full crew run can outlive a proxy timeout, so clients poll."""
import threading
import time
import uuid

TTL_SECONDS = 1800


class JobStore:
    def __init__(self, max_active: int = 3, clock=time.time):
        self.max_active, self._clock = max_active, clock
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self) -> str | None:
        """Create a queued job, or return None when too many jobs are active."""
        now = self._clock()
        with self._lock:
            for key in [k for k, j in self._jobs.items() if now - j["t"] > TTL_SECONDS]:
                del self._jobs[key]
            active = sum(1 for j in self._jobs.values() if j["status"] in ("queued", "running"))
            if active >= self.max_active:
                return None
            job_id = uuid.uuid4().hex[:12]
            self._jobs[job_id] = {"status": "queued", "t": now}
            return job_id

    def update(self, job_id: str, **fields) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(fields)

    def public(self, job_id: str) -> dict | None:
        """Job state without internal fields, or None if unknown."""
        with self._lock:
            job = self._jobs.get(job_id)
            return None if job is None else {k: v for k, v in job.items() if k != "t"}

    def clear(self) -> None:
        with self._lock:
            self._jobs.clear()
