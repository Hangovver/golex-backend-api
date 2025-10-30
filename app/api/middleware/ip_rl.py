from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from ..api.security.ip_rate_limit import allow

class IpRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else 'unknown'
        if not allow(ip):
            return JSONResponse({'detail':'rate limited'}, status_code=429)
        return await call_next(request)
