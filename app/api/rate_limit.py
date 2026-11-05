"""A simple in-memory, per-IP rate limiter, used as a FastAPI dependency."""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.config import TRUSTED_PROXY_HOPS


def client_ip(request: Request) -> str:
    # Behind proxies, request.client is the nearest proxy, not the visitor.
    # Each proxy appends the IP it received the request from to X-Forwarded-For,
    # so with N trusted proxies the visitor is the Nth entry from the end.
    # Entries further left can be faked by the client, so we never use them.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",")]
        return ips[-min(TRUSTED_PROXY_HOPS, len(ips))]
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """Allow at most `max_requests` per IP in any `window_seconds` (sliding window)."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)  # ip -> request times

    def __call__(self, request: Request) -> None:
        now = time.monotonic()
        hits = self.hits[client_ip(request)]

        # Forget requests that are older than the window.
        while hits and hits[0] <= now - self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests",
                headers={"Retry-After": str(int(self.window_seconds))},
            )
        hits.append(now)
