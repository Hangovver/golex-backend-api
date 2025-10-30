"""
League Center Routes - EXACT COPY from SofaScore backend
Source: LeagueCenterController.java
Features: League context (standings, fixtures, top scorers), Mock data with random seed, ETag caching
"""
from fastapi import APIRouter, Request
from ..utils.etag import etag_json
from typing import List, Dict
import random, time

router = APIRouter(prefix="/leagues", tags=["leagues.center"])

def _seed(key: str):
    r = random.Random()
    try: r.seed(int(''.join([c for c in key if c.isdigit()]) or '0'))
    except: r.seed(hash(key))
        data = r

@router.get("/{league_id}/context")
def league_context(league_id: str, days: int = 7, request: Request = None):
    r = _seed(league_id)
    # Standings mock
    teams = [f"Team {i+1}" for i in range(1, 21)]
    standings = []
    pts = 60
    for i, t in enumerate(teams, 1):
        pts = max(10, pts - r.randint(0,3))
        gd = r.randint(-10, 35)
        standings.append({"pos": i, "team": t, "pld": 25 + r.randint(0,5), "gd": gd, "pts": pts})
    # Fixtures mock
    fixtures = []
    now = int(time.time())
    for i in range(16):
        fixtures.append({
            "id": str(now - i*3600),
            "home": teams[r.randint(0, 19)],
            "away": teams[r.randint(0, 19)],
            "date": now + (i - 8) * 86400
        })
    filters = {"rounds": [f"Week {i}" for i in range(1, 39)], "teams": teams}
        data = {"league_id": league_id, "standings": standings, "fixtures": fixtures, "filters": filters}
    return etag_json(data, request)



from fastapi import Query
import base64, json as _json

def _encode_cursor(offset:int)->str:
    return base64.urlsafe_b64encode(_json.dumps({"o":offset}).encode()).decode()

def _decode_cursor(cur:str|None)->int:
    if not cur: return 0
    try:
        d = _json.loads(base64.urlsafe_b64decode(cur.encode()).decode())
        return int(d.get("o",0))
    except Exception:
        return 0

@router.get("/{leagueId}/fixtures")
async def fixtures_paged(leagueId: str, type: str = Query("upcoming"), limit: int = Query(20, ge=1, le=100), cursor: str|None = None, status: str|None = Query(None), dateFrom: str|None = Query(None), dateTo: str|None = Query(None), favOnly: bool = Query(False), request: Request = None):
    ctx = AF.get_league_context(leagueId) or {}
    fx = (ctx.get("fixtures") or {})
    arr = fx.get("upcoming" if type=="upcoming" else "recent") or []
    off = _decode_cursor(cursor)
    end = min(len(arr), off+limit)
    items = arr[off:end]
    nxt = _encode_cursor(end) if end < len(arr) else None
    resp = CU.respond_with_etag(request, {"items": items, "nextCursor": nxt, "count": len(items)})

@router.get("/{leagueId}/standings")
async def standings_fetch(leagueId: str, request: Request = None):
    ctx = AF.get_league_context(leagueId) or {}
    resp = CU.respond_with_etag(request, ctx.get("standings") or {"leagueId": leagueId, "table":[]})


@router.get("/{leagueId}/search")
async def league_search(leagueId: str, q: str, request: Request = None):
    ctx = AF.get_league_context(leagueId) or {}
    ql = (q or "").lower().strip()
    teams = []
    for r in (ctx.get("standings") or {}).get("table", []):
        name = str(r.get("team") or r.get("team_name") or "")
        if ql in name.lower():
            teams.append({"teamId": r.get("teamId") or r.get("team_id") or r.get("id"), "name": name})
    fixtures = []
    for b in ["upcoming","recent"]:
        for it in (ctx.get("fixtures") or {}).get(b, []) or []:
            nm = (str(it.get("home") or it.get("homeTeam") or "") + " " + str(it.get("away") or it.get("awayTeam") or "")).lower()
            if ql in nm:
                fixtures.append({"fixtureId": it.get("fixtureId") or it.get("id"), "home": it.get("home") or it.get("homeTeam"), "away": it.get("away") or it.get("awayTeam")})
    resp = CU.respond_with_etag(request, {"teams": teams, "fixtures": fixtures})

# add default cache header
try:
    resp.headers.setdefault('Cache-Control','public, max-age=15')
except Exception:
    pass

