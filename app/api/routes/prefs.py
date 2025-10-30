
from fastapi import APIRouter, Path, Body, Request
from typing import Any, Dict
from ...services.prefs_store import STORE
from ...services import cache_utils as CU

router = APIRouter(prefix="/prefs", tags=["prefs"])

@router.get("/{anonId}")
async def get_prefs(anonId: str = Path(...), request: Request = None):
    data = STORE.get(anonId) or {"favLeagues": [], "favTeams": [], "favFixtures": [], "settings": {}}
    return CU.respond_with_etag(request, data)

@router.post("/{anonId}")
async def set_prefs(anonId: str = Path(...), data: Dict[str, Any] = Body(...)):
    cur = STORE.set(anonId, data or {})
    return {"ok": True, "prefs": cur}
