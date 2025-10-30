
from fastapi import APIRouter, Path, Request
from sse_starlette.sse import EventSourceResponse
import asyncio, json, time
from ...services import apifootball_adapter as AF

router = APIRouter(prefix="/realtime", tags=["realtime"])

async def _gen(league_id: str):
    # Demo: periodically emit heartbeat + scoreboard snapshot (if available)
    while True:
        ctx = AF.get_league_context(league_id) or {}
        payload = {"t": int(time.time()), "leagueId": league_id, "live": (ctx.get("fixtures") or {}).get("upcoming", [])[:3]}
        yield {"event": "league", "data": json.dumps(payload)}
        await asyncio.sleep(5)

@router.get("/league/{leagueId}/sse")
async def league_sse(leagueId: str = Path(...)):
    return EventSourceResponse(_gen(leagueId))
