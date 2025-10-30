from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid, time, logging

logger = logging.getLogger("golex")

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        start = time.time()
        response: Response = await call_next(request)
        took = int((time.time() - start)*1000)
        response.headers['X-Request-Id'] = rid
        logger.info(f"rid={rid} path={request.url.path} status={response.status_code} took_ms={took}")
        return response
