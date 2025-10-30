from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Set
import asyncio, json, time

router = APIRouter(prefix="/rt", tags=["realtime"])

ROOMS: Dict[str, Set[WebSocket]] = {}

async def _send(ws: WebSocket, data: dict):
    try:
        await ws.send_text(json.dumps(data))
    except Exception:
        pass

@router.websocket("/ws/{room}")
async def ws_room(ws: WebSocket, room: str):
    await ws.accept()
    ROOMS.setdefault(room, set()).add(ws)
    try:
        # Heartbeat loop
        while True:
            await _send(ws, {"type":"hb","ts": time.time(),"room":room})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    finally:
        try:
            ROOMS.get(room, set()).discard(ws)
        except Exception:
            pass

@router.get("/broadcast")
async def broadcast(room: str = Query(...), msg: str = Query("hi")):
    data = {"type":"msg","room":room,"msg":msg,"ts": time.time()}
    for ws in list(ROOMS.get(room, set())):
        await _send(ws, data)
    return {"ok": True, "room": room, "sent": len(ROOMS.get(room, set()))}
