from __future__ import annotations

import time
import threading
from collections import defaultdict, deque


class InMemoryRateLimit:
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        with self._lock:
            now = time.monotonic()
            if key not in self._events and len(self._events) >= 4096:
                expired = [k for k, v in self._events.items() if not v or now - v[-1] > self.window_seconds]
                for old_key in expired:
                    del self._events[old_key]
                if len(self._events) >= 4096:
                    return False
            bucket = self._events[key]
            while bucket and now - bucket[0] > self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                return False
            bucket.append(now)
            return True


auth_rate_limit = InMemoryRateLimit(max_requests=30, window_seconds=60)
