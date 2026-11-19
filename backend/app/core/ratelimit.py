"""Small in-memory sliding-window rate limiter (per process).

For multi-instance deployments put a shared limiter (Redis / API gateway / reverse proxy) in front;
this still protects each worker against brute force.
"""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

from app.core.config import settings


class RateLimiter:
    def __init__(self):
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str, window: int) -> deque:
        q = self._hits[key]
        cutoff = time.monotonic() - window
        while q and q[0] < cutoff:
            q.popleft()
        return q

    def count(self, key: str, window: int) -> int:
        with self._lock:
            return len(self._prune(key, window))

    def add(self, key: str) -> None:
        with self._lock:
            self._hits[key].append(time.monotonic())

    def allow(self, key: str, limit: int, window: int) -> bool:
        with self._lock:
            q = self._prune(key, window)
            if len(q) >= limit:
                return False
            q.append(time.monotonic())
            return True

    def clear(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def too_many(window: int) -> HTTPException:
    return HTTPException(429, "Too many requests. Please try again later.", headers={"Retry-After": str(window)})


def rate_limit(name: str, limit: int, window: int):
    """Dependency: allow `limit` calls per `window` seconds per client IP."""

    def dependency(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return
        ip = request.client.host if request.client else "unknown"
        if not limiter.allow(f"{name}:{ip}", limit, window):
            raise too_many(window)

    return dependency
