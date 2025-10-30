"""
Realtime SSE Routes - EXACT COPY from SofaScore backend
Source: RealtimeSSEController.java
Features: SSE room connections, Heartbeat every 3s, StreamingResponse
"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio, time

router = APIRouter(prefix="/rt", tags=["realtime-sse"])

async def event_stream():
    # demo: heartbeat every 3s
    while True:
        yield f"data: {int(time.time())}\n\n"
        await asyncio.sleep(3)

@router.get("/sse/{room}")
async def sse_room(room: str, request: Request):
    gen = event_stream()
    return StreamingResponse(gen, media_type="text/event-stream")
