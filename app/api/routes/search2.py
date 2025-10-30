from fastapi import APIRouter, Request, Query
from typing import List, Dict
import difflib
from ...services import apifootball_adapter as AF
from ...services import cache_utils as CU
from ...services import cache_utils as CU

router = APIRouter(prefix="/search2", tags=["search"])

# demo minimal index
DATA = {
    "team": [
        {"id":"GS","name":"Galatasaray","country":"TR","leagueId":"TR1"},
        {"id":"FB","name":"Fenerbahçe","country":"TR","leagueId":"TR1"},
        {"id":"BJK","name":"Beşiktaş","country":"TR","leagueId":"TR1"},
        {"id":"RMA","name":"Real Madrid","country":"ES","leagueId":"ES1"},
        {"id":"BAR","name":"Barcelona","country":"ES","leagueId":"ES1"},
    ],
    "league": [
        {"id":"TR1","name":"Süper Lig","country":"TR"},
        {"id":"ES1","name":"LaLiga","country":"ES"},
        {"id":"GB1","name":"Premier League","country":"GB"},
    ],
    "player": [
        {"id":"p1","name":"Mauro Icardi","teamId":"GS","country":"AR"},
        {"id":"p2","name":"Vinícius Júnior","teamId":"RMA","country":"BR"},
    ]
}

@router.get("")
async def search2(q: str = Query(...), type: str = Query("team"), country: str | None = Query(None), leagueId: str | None = Query(None), limit: int = Query(10), request: Request):
    items = DATA.get(type, [])
    if country:
        items = [x for x in items if x.get("country")==country]
    if leagueId:
        items = [x for x in items if x.get("leagueId")==leagueId]
    names = [x["name"] for x in items]
    hits = difflib.get_close_matches(q, names, n=limit, cutoff=0.3)
    res = [x for x in items if x["name"] in hits]
    # simple scoring
    out = [{"id":x["id"], "name":x["name"], "score": round(difflib.SequenceMatcher(None, q.lower(), x["name"].lower()).ratio(),3)} for x in res]
    out.sort(key=lambda r: r["score"], reverse=True)
    return CU.respond_with_etag(request, {"items": out})
