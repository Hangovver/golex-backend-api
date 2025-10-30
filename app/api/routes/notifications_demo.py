from fastapi import APIRouter, Body
from typing import Dict, List

router = APIRouter(prefix="/notifications/demo", tags=["notifications-demo"])

LOG: List[Dict] = []

@router.post("/goal")
async def goal(fixtureId: str = Body(...), msg: str = Body("GOL!")):
    deeplink = f"golex://match/{fixtureId}"
    item = {"fixtureId": fixtureId, "msg": msg, "deeplink": deeplink}
    LOG.append(item)
    return {"ok": True, "item": item}

@router.get("/log")
async def log():
    return {"items": LOG[-100:]}
