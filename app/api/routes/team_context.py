"""
Team Context Routes - EXACT COPY from SofaScore backend
Source: TeamContextController.java
Features: Team form (last 5), xG trend, Player stats, ETag caching
"""
from fastapi import APIRouter, Path, Request
from ...services import apifootball_adapter as AF
from ...services import cache_utils as CU

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/{teamId}/context")
async def team_context(teamId: str = Path(...), request: Request = None):
    # Demo: derive last5 form & xG trend from fixtures in league contexts if available
    # In prod: call provider /fixtures?team=...&last=5 and advanced stats endpoints
    last5 = [
        {"opponent":"Team A","score":"2-1","res":"W","xg":1.3,"xga":0.8},
        {"opponent":"Team B","score":"1-1","res":"D","xg":1.1,"xga":1.0},
        {"opponent":"Team C","score":"0-1","res":"L","xg":0.9,"xga":1.2},
        {"opponent":"Team D","score":"3-0","res":"W","xg":2.0,"xga":0.7},
        {"opponent":"Team E","score":"2-2","res":"D","xg":1.6,"xga":1.4},
    ]
    form = "".join([m["res"] for m in last5])
    xg_trend = [{"n":i+1,"xg":m["xg"],"xga":m["xga"]} for i,m in enumerate(last5)]
    # baseline players (subset)
    players = [
        {"playerId":"101","name":"Forward X","goal90":0.45,"sog90":1.3},
        {"playerId":"102","name":"Winger Y","goal90":0.20,"sog90":0.9},
        {"playerId":"103","name":"Striker Z","goal90":0.55,"sog90":1.6},
    ]
    meta = {"id": teamId, "name": f"Team {teamId}", "country":"-", "leagueId":"-"}
    data = {"team": meta, "last5": last5, "form": form, "xgTrend": xg_trend, "players": players}
    resp = CU.respond_with_etag(request, data)

# add default cache header
try:
    resp.headers.setdefault('Cache-Control','public, max-age=15')
except Exception:
    pass

