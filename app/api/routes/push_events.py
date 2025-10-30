from fastapi import APIRouter
from ..utils.redis_pool import get_redis
import json

router = APIRouter(prefix="/admin/push", tags=["admin.push"])

@router.get("/peek")
async def peek(limit: int = 10):
    r = await get_redis()
    vals = await r.lrange("golex:push:events", 0, max(0, limit-1))
    return [json.loads(v) for v in vals]

@router.post("/pop")
async def pop():
    r = await get_redis()
    val = await r.lpop("golex:push:events")
    return json.loads(val) if val else None
