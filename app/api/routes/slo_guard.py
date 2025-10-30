from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..deps import get_db
from ..metrics import set_macro_ece, PRED_ECE, REQ_LATENCY, LIVE_DELAY
from typing import Optional

router = APIRouter(prefix="/admin/slo", tags=["admin.slo"])

POLICY = {
    "p95_latency_seconds": 0.5,
    "macro_ece": 0.06,
    "live_delay_seconds": 15.0
}

@router.get("/policy")
def get_policy():
    return POLICY

@router.post("/check")
def check(sample_p95: Optional[float] = None, sample_ece: Optional[float] = None, sample_live_delay: Optional[float] = None):
    # If samples provided, use them; otherwise read known gauges (ece/live delay); p95 is Prometheus-side usually.
    ece = float(sample_ece) if sample_ece is not None else float(getattr(PRED_ECE, '_value', 0.0)._value if hasattr(PRED_ECE, '_value') else 0.0)
    ldelay = float(sample_live_delay) if sample_live_delay is not None else float(getattr(LIVE_DELAY, '_value', 0.0)._value if hasattr(LIVE_DELAY, '_value') else 0.0)
    p95 = float(sample_p95) if sample_p95 is not None else 0.0  # advise using Prometheus alert for p95

    sev = "ok"
    breached = []
    if p95 > POLICY["p95_latency_seconds"]:
        sev = "warn"; breached.append(("p95_latency_seconds", p95))
    if ece > POLICY["macro_ece"]:
        sev = "warn"; breached.append(("macro_ece", ece))
    if ldelay > POLICY["live_delay_seconds"]:
        sev = "warn"; breached.append(("live_delay_seconds", ldelay))

    if any(name == "macro_ece" for name, _ in breached) and ece > (POLICY["macro_ece"] * 1.5):
        sev = "alert"
    if any(name == "p95_latency_seconds" for name, _ in breached) and p95 > (POLICY["p95_latency_seconds"] * 2):
        sev = "alert"
    if any(name == "live_delay_seconds" for name, _ in breached) and ldelay > (POLICY["live_delay_seconds"] * 2):
        sev = "alert"

    return {"severity": sev, "breaches": [{"name": n, "value": v} for n, v in breached]}
