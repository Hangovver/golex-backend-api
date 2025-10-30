from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from ..cache.redis import redis_client
import time, os

RATE_LIMIT_PER_MIN = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "120"))

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        key = f"rl:{ip}"
        # simple fixed window
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, 60)
        if count > RATE_LIMIT_PER_MIN:
            return PlainTextResponse("Too Many Requests", status_code=429)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_PER_MIN)
        response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT_PER_MIN - count))
        return response
