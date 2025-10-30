from fastapi import APIRouter, Query
from starlette.responses import StreamingResponse
import asyncio, json
from ...utils.redis_pool import get_redis
from starlette.responses import Response

router = APIRouter(prefix="/stream", tags=["stream"])

@router.get("/sse")
async def sse(room: str = Query(..., description="fixture:<id> | team:<id> | league:<id>")):
    r = await get_redis()
    pub = r.pubsub()
    channel = f"room:{room}"
    await pub.subscribe(channel)

    async def event_gen():
        try:
            while True:
                msg = await pub.get_message(ignore_subscribe_messages=True, timeout=30.0)
                if msg and msg.get("type") == "message":
                    data = msg.get("data")
                    if isinstance(data, (bytes, bytearray)):
                        data = data.decode("utf-8")
                    yield f"data: {data}\n\n"
                await asyncio.sleep(0.01)
        finally:
            await pub.unsubscribe(channel)
            await pub.close()

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get("/sse2")
async def sse_v2(room: str = Query(..., description="fixture:<id> | team:<id> | league:<id>")):
    r = await get_redis()
    pub = r.pubsub()
    channel = f"room:{room}"
    await pub.subscribe(channel)

    async def event_gen2():
        yield "retry: 5000\n\n"
        idle = 0
        try:
            while True:
                msg = await pub.get_message(ignore_subscribe_messages=True, timeout=5.0)
                if msg and msg.get("type") == "message":
                    data = msg.get("data")
                    if isinstance(data, (bytes, bytearray)):
                        data = data.decode("utf-8")
                    idle = 0
                    yield f"data: {data}\n\n"
                else:
                    idle += 5
                    if idle >= 20:
                        idle = 0
                        # comment line as keepalive
                        yield ": keepalive\n\n"
                await asyncio.sleep(0.01)
        finally:
            await pub.unsubscribe(channel)
            await pub.close()

    return StreamingResponse(event_gen2(), media_type="text/event-stream")
