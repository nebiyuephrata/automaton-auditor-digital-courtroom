from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets
import threading
from typing import Deque, Dict, Tuple


@dataclass(frozen=True)
class SecurityConfig:
    api_auth_key: str
    rate_limit_per_minute: int


class SlidingWindowRateLimiter:
    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = max(1, limit_per_minute)
        self._hits: Dict[str, Deque[datetime]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> Tuple[bool, int]:
        with self._lock:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(minutes=1)
            q = self._hits[key]

            while q and q[0] < window_start:
                q.popleft()

            if len(q) >= self.limit_per_minute:
                retry_after = max(1, int((q[0] + timedelta(minutes=1) - now).total_seconds()))
                return False, retry_after

            q.append(now)
            return True, 0


def is_api_key_valid(provided: str | None, expected: str) -> bool:
    if not expected:
        return False
    if not provided:
        return False
    return secrets.compare_digest(provided, expected)
