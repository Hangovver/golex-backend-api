from fastapi import APIRouter, Body
from ...services import slo_guard as SG

router = APIRouter(prefix="/admin/slo", tags=["admin-slo"])

@router.post("/ingest")
async def ingest(latency_ms: float | None = Body(None), ece: float | None = Body(None), live_delay_s: float | None = Body(None)):
    SG.ingest(latency_ms=latency_ms, ece=ece, live_delay_s=live_delay_s)
    return {"ok": True}

@router.post("/thresholds")
async def thresholds(p95_ms: float | None = Body(None), ece: float | None = Body(None), live_delay_s: float | None = Body(None)):
    return SG.set_thresholds(p95_ms, ece, live_delay_s)

@router.get("/report")
async def report():
    return SG.report()

@router.post("/check")
async def check():
    return SG.check_and_alert()
