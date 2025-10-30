import time
from fastapi import Request, Response
from typing import Dict

# Very simple in-memory rate limiter: N requests per window per IP
class RateLimiter:
    def __init__(self, limit: int = 120, window_sec: int = 60):
        self.limit = limit
        self.window = window_sec
        self.bucket: Dict[str, tuple[int, float]] = {}

    def allow(self, ip: str) -> bool:
        now = time.time()
        count, start = self.bucket.get(ip, (0, now))
        if now - start > self.window:
            count, start = 0, now
        count += 1
        self.bucket[ip] = (count, start)
        return count <= self.limit

limiter = RateLimiter()
