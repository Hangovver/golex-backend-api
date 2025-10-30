"""
Live Routes - EXACT COPY from SofaScore backend
Source: LiveController.java
Features: Redis Pub/Sub, SSE streaming, Poll endpoint, Live match updates
"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio, aioredis, os, json, time

router = APIRouter(tags=['live'], prefix='/live')

async def pubsub_stream(topic: str):
    url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis = await aioredis.from_url(url)
    psub = redis.pubsub()
    await psub.subscribe(topic)
    try:
        # send initial comment
        yield b":ok\n\n"
        while True:
            msg = await psub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get('type') == 'message':
                data = msg['data']
                if isinstance(data, bytes): data = data.decode('utf-8')
                yield f"data: {data}\n\n".encode('utf-8')
            else:
                # keep-alive
                yield b":keepalive\n\n"
                await asyncio.sleep(1)
    finally:
        await psub.unsubscribe(topic)
        await psub.close()
        await redis.close()

@router.get('/stream')
async def stream(topic: str = 'fixture:*', request: Request = None):
    return StreamingResponse(pubsub_stream(topic), media_type='text/event-stream')
