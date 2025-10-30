from fastapi import APIRouter, Query
from typing import Optional
from fastapi import Request, Response
from ...utils.etag import with_http_caching
from datetime import datetime, timezone

router = APIRouter(prefix="/fixtures", tags=["fixtures"])

_FIX = [
    {"id":"1001","home":"Galatasaray","away":"Fenerbahçe","status":"LIVE","minute":"12'","score":"0-0","updated_at":"2025-10-26T10:00:00Z"},
    {"id":"1002","home":"Barcelona","away":"Real Madrid","status":"LIVE","minute":"34'","score":"1-0","updated_at":"2025-10-26T10:05:00Z"},
    {"id":"1003","home":"Man City","away":"Arsenal","status":"HT","minute":"HT","score":"0-0","updated_at":"2025-10-26T10:07:00Z"},
    {"id":"1004","home":"Napoli","away":"Inter","status":"SCHEDULED","minute":"-","score":"-:-","updated_at":"2025-10-26T09:00:00Z"},
]

_DETAIL = {
    "1001": {
        "id":"1001","home":"Galatasaray","away":"Fenerbahçe","status":"LIVE","minute":"14'","score":"0-0",
        "events":[{"m":5,"t":"yellow","team":"home","player":"Torreira"}],
        "lineups":{"home":[[0.15,0.8],[0.25,0.7],[0.4,0.6]],"away":[[0.85,0.8],[0.75,0.7],[0.6,0.6]]},
        "stats":{"shots": {"home":4,"away":3}, "xg_timeline":{"home":[0.02,0.05,0.01],"away":[0.01,0.03,0.02]}}
    }
}

@router.get("")
async def list_fixtures(date: Optional[str] = None, status: Optional[str] = None):
    items = _FIX
    if status:
        items = [x for x in items if x["status"] == status]
    return {"items": items}

@router.get("/{fixture_id}")
async def fixture_detail(fixture_id: str, expand: Optional[str] = None):
    return _DETAIL.get(fixture_id, {"id":fixture_id,"status":"SCHEDULED","home":"TBD","away":"TBD","score":"-:-","minute":"-"})


@router.get("/updates")
async def updates(request: Request, response: Response, since: str):
    # Return fixtures updated after `since` (ISO8601)
    # For demo, filter by updated_at string compare
    items = [x for x in _FIX if x.get("updated_at","") > since]
    payload = {"items": items, "since": since}
    res = with_http_caching(request, response, payload)
    return res if res is not None else Response(status_code=304)
