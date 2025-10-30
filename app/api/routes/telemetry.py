
from fastapi import APIRouter, Request, Body, Query
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from ...services.telemetry_store import STORE
from ...services import cache_utils as CU

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

class Event(BaseModel):
    name: str
    params: Dict[str, Any] = {}
    ts: Optional[int] = None

@router.post("/events")
async def collect_events(events: List[Event], request: Request = None):
    STORE.add_many([e.dict() for e in events])
    return {"ok": True, "n": len(events)}

@router.get("/events")
async def fetch_events(limit: int = Query(50, ge=1, le=500), request: Request = None):
    data = {"items": STORE.last(limit)}
    resp = CU.respond_with_etag(request, data)

# add default cache header
try:
    resp.headers.setdefault('Cache-Control','public, max-age=15')
except Exception:
    pass

