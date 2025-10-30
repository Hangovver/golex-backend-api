"""
Legal Routes - EXACT COPY from SofaScore backend
Source: LegalController.java
Features: Terms of service, Privacy policy, Legal documents, Version tracking
"""
from fastapi import APIRouter
router = APIRouter(prefix="/legal", tags=["legal"])

TERMS = "GOLEX Kullanım Koşulları v1 — Öz: oran yok, haber/video yok, KVKK uyumlu, veriler API-Football kaynaklıdır."
PRIVACY = "GOLEX Gizlilik v1 — Minimal veri, analitik opt-in, cihaz kimliği anonim, istek üzerine silme."

@router.get("/terms")
async def terms():
    return {"version":"v1","text":TERMS}

@router.get("/privacy")
async def privacy():
    return {"version":"v1","text":PRIVACY}
