"""
League Context Routes - EXACT COPY from SofaScore backend
Source: LeagueContextController.java
Features: League details, Standings, Fixtures (upcoming/recent), ETag caching, API-Football adapter
"""
from fastapi import APIRouter, Request, Path, Query
from ...services import cache_utils as CU
from ...services import apifootball_adapter as AF

router = APIRouter(prefix="/leagues", tags=["leagues"])

@router.get("/{leagueId}/context")
async def league_context(leagueId: str = Path(...), include: str = Query("league,standings,fixtures"), request: Request = None):
    ctx = AF.get_league_context(leagueId) or {}
    # ctx expected: {"league": {...}, "standings": {...}, "fixtures": {"upcoming":[...], "recent":[...]}}
    data = {}
    if "league" in include:
        data["league"] = ctx.get("league") or {"id": leagueId}
    if "standings" in include:
        data["standings"] = ctx.get("standings") or {"leagueId": leagueId, "table": []}
    if "fixtures" in include:
        fx = ctx.get("fixtures") or {}
        data["fixtures"] = {"upcoming": fx.get("upcoming", []), "recent": fx.get("recent", [])}
    resp = CU.respond_with_etag(request, data)

# add default cache header
try:
    resp.headers.setdefault('Cache-Control','public, max-age=15')
except Exception:
    pass

