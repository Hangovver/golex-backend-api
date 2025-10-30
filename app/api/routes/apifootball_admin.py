from fastapi import APIRouter
from ..utils.redis_pool import get_redis
import time, json

router = APIRouter(prefix="/admin/apifootball", tags=["admin.apifootball"])

@router.get("/status")
async def status():
    r = await get_redis()
    # simple readouts
    now = int(time.time())
    bucket = f"golex:rl:apifootball:{now // 60}"
    cnt = await r.get(bucket)
    cb = await r.get("golex:cb:apifootball")
    return {"rate_window_count": int(cnt or 0), "circuit": json.loads(cb) if cb else {"open_until": 0}}
