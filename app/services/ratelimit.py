import time, os
from fastapi import Request
from starlette.responses import Response, JSONResponse

RL_MAX = int(os.getenv("RL_MAX","120"))
RL_WINDOW_MS = int(os.getenv("RL_WINDOW_MS","60000"))

buckets = {}

async def middleware(request: Request, call_next):
    now = int(time.time()*1000)
    ip = request.client.host if request.client else "0.0.0.0"
    b = buckets.get(ip, {"ts": now, "count": 0})
    if now - b["ts"] > RL_WINDOW_MS:
        b = {"ts": now, "count": 0}
    b["count"] += 1
    buckets[ip] = b
    if b["count"] > RL_MAX:
        return JSONResponse({"error":"rate_limited","retry_ms": RL_WINDOW_MS - (now - b["ts"])}, status_code=429)
    return await call_next(request)
