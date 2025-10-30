import uuid, time, json, logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request

log = logging.getLogger("golex")

class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get('X-Request-Id') or str(uuid.uuid4())
        t0 = time.time()
        response = await call_next(request)
        dt = time.time()-t0
        try:
            log.info(json.dumps({'rid': rid, 'path': request.url.path, 'ms': int(dt*1000), 'status': response.status_code}))
        except Exception:
            pass
        response.headers['X-Request-Id'] = rid
        return response
