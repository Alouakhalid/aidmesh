"""Thread-safe sliding-window rate limiter (per client and global)."""
import collections
import threading
import time


class RateLimiter:
    """Allow at most `per_ip` hits per hour per client and `per_day` hits per day overall."""

    def __init__(self, per_ip: int = 4, per_day: int = 150, clock=time.time):
        self.per_ip, self.per_day, self._clock = per_ip, per_day, clock
        self._hits: dict[str, collections.deque] = {}
        self._day: collections.deque = collections.deque()
        self._lock = threading.Lock()

    def allow(self, client: str) -> bool:
        """Record a hit and return True, or return False (recording nothing) when over a limit."""
        now = self._clock()
        with self._lock:
            while self._day and now - self._day[0] >= 86400:
                self._day.popleft()
            hits = self._hits.setdefault(client, collections.deque())
            while hits and now - hits[0] >= 3600:
                hits.popleft()
            if len(hits) >= self.per_ip or len(self._day) >= self.per_day:
                return False
            hits.append(now)
            self._day.append(now)
            self._forget_idle(now)
            return True

    def _forget_idle(self, now: float) -> None:
        """Drop clients with no recent hits so memory stays bounded."""
        if len(self._hits) > 1000:
            for key in [k for k, h in self._hits.items() if not h or now - h[-1] >= 3600]:
                del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
            self._day.clear()
