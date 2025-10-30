from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json, asyncio
from ...utils.redis_pool import get_redis

router = APIRouter(prefix="/stream", tags=["stream"])

@router.websocket("/ws")
async def ws(websocket: WebSocket, room: str = Query(...)):
    await websocket.accept()
    r = await get_redis()
    pub = r.pubsub()
    channel = f"room:{room}"
    await pub.subscribe(channel)
    try:
        while True:
            msg = await pub.get_message(ignore_subscribe_messages=True, timeout=30.0)
            if msg and msg.get("type") == "message":
                data = msg.get("data")
                if isinstance(data, (bytes, bytearray)):
                    data = data.decode("utf-8")
                await websocket.send_text(data)
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        pass
    finally:
        await pub.unsubscribe(channel)
        await pub.close()
        await websocket.close()
