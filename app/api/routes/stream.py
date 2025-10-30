"""
Stream Routes - EXACT COPY from SofaScore backend
Source: StreamController.java
Features: SSE streaming for fixtures, Realtime bus (Redis Pub/Sub), Event stream generator
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json, time
from ..realtime.bus import subscribe

router = APIRouter(tags=["stream"], prefix="/stream")

def _event_stream(topic: str):
    ps = subscribe(topic)
    # send initial comment to keep connection
    yield b":ok\n\n"
    for m in ps.listen():
        if m["type"] != "message":
            continue
        data = m["data"]
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        yield f"data: {data}\n\n".encode("utf-8")

@router.get("/fixtures/{fixture_id}")
def stream_fixture(fixture_id: str):
    topic = f"fixture:{fixture_id}"
    return StreamingResponse(_event_stream(topic), media_type="text/event-stream")
