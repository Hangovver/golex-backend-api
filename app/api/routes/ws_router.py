from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from . import fixtures_analytics as fa
from ..ws.manager import manager

router = APIRouter()

@router.websocket("/ws/{room_name}")
async def websocket_endpoint(websocket: WebSocket, room_name: str):
    # room_name examples: fixture:12345, team:678
    await manager.connect(room_name, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo for demo; in prod process join/leave/ping etc.
            await manager.send_room(room_name, data)
    except WebSocketDisconnect:
        manager.disconnect(room_name, websocket)
