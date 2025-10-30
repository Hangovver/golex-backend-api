
from fastapi import APIRouter, Body, Query
from pydantic import BaseModel
from typing import Optional
from ...services.slo_store import STORE

router = APIRouter(prefix="/ops/slo", tags=["ops"])

class SloPoint(BaseModel):
    metric: str
    value: float

@router.post("/ingest")
async def slo_ingest(p: SloPoint):
    STORE.ingest(p.metric, p.value)
    return {"ok": True}

@router.get("/check")
async def slo_check():
    return STORE.check()
