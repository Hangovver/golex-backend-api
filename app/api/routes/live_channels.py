from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import asyncio, time

router = APIRouter(tags=['live'], prefix='/live')

# Simple in-memory rooms
rooms: dict[str, set[WebSocket]] = {}

async def broadcast(room: str, msg: str):
    for ws in list(rooms.get(room, set())):
        try: await ws.send_text(msg)
        except Exception: rooms.get(room,set()).discard(ws)

@router.websocket('/ws/{room}')
async def ws_room(ws: WebSocket, room: str):
    await ws.accept()
    rooms.setdefault(room, set()).add(ws)
    try:
        while True:
            await ws.receive_text()  # ignore client pings
    except WebSocketDisconnect:
        rooms[room].discard(ws)

@router.get('/sse/{room}')
def sse_room(room: str):
    async def gen():
        i = 0
        while True:
            i += 1
            yield f"data: tick {i} room={room}\n\n"
            await asyncio.sleep(5)
    return StreamingResponse(gen(), media_type='text/event-stream')


from pydantic import BaseModel
from fastapi import HTTPException

class BroadcastBody(BaseModel):
    room: str
    message: str

@router.post('/broadcast')
async def http_broadcast(body: BroadcastBody):
    # Dev/testing amaçlı basit yayın
    if not body.room or not body.message:
        raise HTTPException(400, detail='room and message required')
    await broadcast(body.room, body.message)
    return {'ok': True}
