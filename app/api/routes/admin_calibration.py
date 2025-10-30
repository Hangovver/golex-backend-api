from fastapi import APIRouter, Body, Query
from ...services import calibration as C

router = APIRouter(prefix="/admin/calibration", tags=["admin-calibration"])

@router.post("/log")
async def log(p: float = Body(...), y: int = Body(...), modelVersion: str = Body("1.0.0")):
    C.log(p, y, modelVersion)
    return {"ok": True}

@router.get("/summary")
async def summary(bins: int = Query(10), modelVersion: str | None = Query(None)):
    return C.summary(bins=bins, modelVersion=modelVersion)
