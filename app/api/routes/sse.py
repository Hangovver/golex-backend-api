"""
SSE Routes - EXACT COPY from SofaScore backend
Source: SSEController.java
Features: SSE room streaming, Poll endpoint (since parameter), Fake event generation, Metrics tracking
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from ..metrics import set_live_delay
import asyncio, json, time, random

router = APIRouter(prefix="/live", tags=["live"])

@router.get("/{room}/poll")
async def poll(room: str, since: int = 0):
    # demo: generate 0..2 fake events after 'since'
    now = int(time.time())
    rnd = random.Random(hash(room) ^ now)
    n = rnd.randint(0, 2)
    items = []
    for _ in range(n):
        items.append({"ts": now, "room": room, "msg": "tick"})
    set_live_delay(3.0)
    return JSONResponse({"items": items, "serverTime": now})

@router.get("/sse/{room}")
async def sse(room: str):
    async def event_stream():
        counter = 0
        while True:
            await asyncio.sleep(3.0)
            counter += 1
            data = {"room": room, "seq": counter, "msg": "tick"}
            set_live_delay(3.0)
            yield f"data: {json.dumps(data)}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")
