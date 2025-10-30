from fastapi import APIRouter, Body
router = APIRouter(prefix="/privacy", tags=["privacy"])

_CONSENTS = {}  # userId -> bool

@router.post("/consent")
async def set_consent(userId: str = Body(...), consent: bool = Body(...)):
    _CONSENTS[userId] = consent
    return {"ok": True, "userId": userId, "consent": consent}

@router.get("/consent/{user_id}")
async def get_consent(user_id: str):
    return {"userId": user_id, "consent": bool(_CONSENTS.get(user_id, False))}

@router.get("/policy")
async def policy():
    return {"version": "v1", "summary": "Minimal veri, opt-in analitik, KVKK/GDPR uyumu."}
