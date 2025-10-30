from fastapi import APIRouter, Body
from ...services import sse_bridge as SB

router = APIRouter(prefix="/ops/sse-bridge", tags=["ops-sse-bridge"])

@router.post("/start")
async def start(room: str = Body("fixture:1001")):
    await SB.start(room)
    return {"ok": True, "state": SB.STATE}

@router.post("/stop")
async def stop():
    await SB.stop()
    return {"ok": True, "state": SB.STATE}

@router.get("/status")
async def status():
    return {"ok": True, "state": SB.STATE}

@router.post("/inject")
async def inject(event: dict = Body(...)):
    await SB.inject(event)
    return {"ok": True}
