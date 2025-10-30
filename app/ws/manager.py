from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
from collections import defaultdict
import asyncio

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, room: str, websocket: WebSocket):
        await websocket.accept()
        self.rooms[room].add(websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        if websocket in self.rooms.get(room, set()):
            self.rooms[room].remove(websocket)
            if not self.rooms[room]:
                del self.rooms[room]

    async def send_room(self, room: str, message: str):
        conns = list(self.rooms.get(room, []))
        for ws in conns:
            try:
                await ws.send_text(message)
            except Exception:
                try:
                    ws.close()
                except: pass
                self.disconnect(room, ws)

manager = ConnectionManager()
