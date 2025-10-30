from fastapi import APIRouter, Body, Query
from typing import List, Dict
from ...services import metrics as M

router = APIRouter(prefix="/inapp", tags=["inapp-survey"])

LOG: List[Dict] = []

@router.post("/survey")
async def submit(rating: int = Body(...), comment: str = Body(""), screen: str = Body("unknown")):
    item = {"rating": int(rating), "comment": comment or "", "screen": screen}
    LOG.append(item)
    M.inc("survey_submissions_total")
    return {"ok": True}

@router.get("/surveys")
async def list_(limit: int = Query(50)):
    return {"items": LOG[-limit:]}
