from fastapi import APIRouter, Body, Query
from typing import Dict
from ...services import data_drift as DD

router = APIRouter(prefix="/admin/drift", tags=["admin-data-drift"])

@router.post("/baseline")
async def baseline(vec: Dict[str,float] = Body(...)):
    DD.set_baseline(vec); return {"ok": True}

@router.post("/log")
async def log(vec: Dict[str,float] = Body(...), to_current: bool = Query(True)):
    DD.log_sample(vec, to_current=to_current); return {"ok": True}

@router.get("/summary")
async def summary():
    return DD.summary()

@router.post("/check")
async def check():
    return DD.check_and_alert()
