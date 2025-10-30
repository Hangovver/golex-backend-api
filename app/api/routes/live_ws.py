from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio, os, aioredis, json

router = APIRouter(tags=['live'], prefix='/live')

@router.websocket('/ws')
async def live_ws(ws: WebSocket, topic: str = 'fixture:*'):
    await ws.accept()
    url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis = await aioredis.from_url(url)
    psub = redis.pubsub()
    await psub.subscribe(topic)
    try:
        while True:
            msg = await psub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get('type') == 'message':
                data = msg['data']
                if isinstance(data, bytes): data = data.decode('utf-8')
                await ws.send_text(data)
            else:
                await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        await psub.unsubscribe(topic)
        await psub.close()
        await redis.close()
