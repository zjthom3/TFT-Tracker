from __future__ import annotations

import time
from collections import defaultdict
from typing import DefaultDict, Tuple

from fastapi import HTTPException, Request, status

from app.config import get_settings

RateBucket = Tuple[int, int]


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self._max_requests = max_requests
        self.window_seconds = window_seconds
        self.counters: DefaultDict[str, RateBucket] = defaultdict(lambda: (0, 0))

    @property
    def max_requests(self) -> int:
        return self._max_requests

    @max_requests.setter
    def max_requests(self, value: int) -> None:
        self._max_requests = value

    def check(self, key: str) -> None:
        now = int(time.time())
        window = now // self.window_seconds
        count, stored_window = self.counters[key]
        if window != stored_window:
            count = 0
        count += 1
        self.counters[key] = (count, window)
        if count > self._max_requests:
            reset_in = (stored_window + 1) * self.window_seconds - now
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {max(reset_in, 1)}s.",
            )


settings = get_settings()
rate_limiter = InMemoryRateLimiter(max_requests=settings.requests_per_minute)


def enforce_rate_limit(request: Request) -> None:
    client_host = request.client.host if request.client else "anonymous"
    rate_limiter.check(client_host)
