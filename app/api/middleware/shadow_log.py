import asyncio, time, uuid, json
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

class ShadowLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, ratio=0.1):
        super().__init__(app); self.ratio = ratio
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = request.headers.get('X-Request-Id') or str(uuid.uuid4())
        # pass through
        resp = await call_next(request)
        # shadow only predictions GET
        if request.url.path.startswith('/api/v1/predictions/') and request.method == 'GET':
            if (hash(rid) % 100) < int(self.ratio*100):
                asyncio.create_task(self._shadow(request, rid))
        return resp
    async def _shadow(self, request: Request, rid: str):
        # here we could call alt model endpoint and log
        log = {'rid': rid, 'path': str(request.url.path), 'ts': time.time(), 'note': 'shadowed'}
        # naive file log
        try:
            with open('/tmp/golex_shadow.log','a') as f: f.write(json.dumps(log)+'\n')
        except Exception:
            pass
