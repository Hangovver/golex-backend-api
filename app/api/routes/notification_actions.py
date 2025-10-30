from fastapi import APIRouter, Body
from typing import Literal, Dict, List
from ...services import metrics as M

router = APIRouter(prefix="/notifications", tags=["notifications-actions"])

LOG: List[Dict] = []

@router.post("/action")
async def action(action: Literal["snooze","unfollow","open"], fixtureId: str | None = Body(None), teamId: str | None = Body(None)):
    item = {"action": action, "fixtureId": fixtureId, "teamId": teamId}
    LOG.append(item)
    M.inc("notification_action_total", {"action": action})
    return {"ok": True, "logged": item}

@router.get("/actions")
async def actions(limit: int = 50):
    return {"items": LOG[-limit:]}
