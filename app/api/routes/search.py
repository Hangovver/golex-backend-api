
from fastapi import APIRouter, Query, Request
from typing import Optional
from ...services import apifootball_adapter as AF
from ...services import cache_utils as CU
from ...services.search_utils import filter_rank

router = APIRouter(prefix="/search", tags=["search"])

@router.get("")
async def search(q: str, type: Optional[str] = Query(None), country: Optional[str] = Query(None), leagueId: Optional[str] = Query(None), fuzzy: bool = Query(True), limit: int = Query(20)):
    q = (q or "").strip()
    leagues = AF.list_leagues()
    teams = AF.list_teams(leagueId=leagueId)
    players = []  # optional
    if country:
        leagues = [l for l in leagues if str(l.get("country","")).lower()==country.lower()]
        teams = [t for t in teams if str(t.get("country","")).lower()==country.lower()]
    out = {}
    if not type or type=="league":
        out["leagues"] = filter_rank(q, leagues, "name")[:limit] if fuzzy else [l for l in leagues if q.lower() in str(l.get("name","")).lower()][:limit]
    if not type or type=="team":
        out["teams"] = filter_rank(q, teams, "name")[:limit] if fuzzy else [t for t in teams if q.lower() in str(t.get("name","")).lower()][:limit]
    if not type or type=="player":
        out["players"] = filter_rank(q, players, "name")[:limit] if fuzzy else [p for p in players if q.lower() in str(p.get("name","")).lower()][:limit]
    return CU.respond_with_etag(None, out)

# add default cache header
try:
    resp.headers.setdefault('Cache-Control','public, max-age=15')
except Exception:
    pass

