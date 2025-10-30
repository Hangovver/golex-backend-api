from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from .config import settings

FORBIDDEN_PREFIXES = ("/api/v1/odds", "/api/v1/news", "/api/v1/video")

class ContentPolicyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        # Hard-block disallowed namespaces
        if path.startswith(FORBIDDEN_PREFIXES):
            return JSONResponse({"error":"content_forbidden","policy":"football_only,no_odds,no_news,no_video"}, status_code=403)
        resp = await call_next(request)
        return resp
