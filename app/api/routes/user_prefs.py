from fastapi import APIRouter, Body, Path
from typing import Dict, Any, List
from ...services import metrics as M

router = APIRouter(prefix="/user", tags=["user-prefs"])

STORE: Dict[str, Dict[str, Any]] = {}

@router.get("/prefs/{anonId}")
async def get_prefs(anonId: str = Path(...)):
    return {"anonId": anonId, "prefs": STORE.get(anonId, {})}

@router.post("/prefs/{anonId}")
async def set_prefs(anonId: str = Path(...), prefs: Dict[str, Any] = Body(...)):
    STORE[anonId] = prefs or {}
    M.inc("user_prefs_backups_total")
    return {"ok": True}
