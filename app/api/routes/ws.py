"""
WebSocket Routes - EXACT COPY from SofaScore backend
Source: WebSocketController.java
Features: WebSocket endpoint, Topic-based subscriptions (fixture/league), Redis Pub/Sub integration
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..realtime.bus import subscribe
import json, threading

router = APIRouter(tags=["ws"], prefix="/ws")


@router.websocket("")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Expect a query param ?topic=fixture:<id> or league:<id>
    topic = websocket.query_params.get("topic")
    if not topic:
        await websocket.close(code=1008)
        return

    ps = subscribe(topic)
    try:
        for m in ps.listen():
            if m["type"] != "message":
                continue
            data = m["data"]
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            await websocket.send_text(data)
    except WebSocketDisconnect:
        pass
