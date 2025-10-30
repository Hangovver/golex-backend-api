import json, asyncio
from typing import Any, Optional
from .redis_pool import get_redis

async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    v = await r.get(key)
    if v is None:
        return None
    try:
        return json.loads(v)
    except Exception:
        return v

async def cache_set(key: str, value: Any, ttl: int = 60):
    r = await get_redis()
    data = json.dumps(value, ensure_ascii=False)
    await r.set(key, data, ex=ttl)

async def cache_invalidate(pattern: str):
    r = await get_redis()
    # Caution: SCAN + DEL
    cursor = "0"
    while True:
        cursor, keys = await r.scan(cursor=cursor, match=pattern, count=200)
        if keys:
            await r.delete(*keys)
        if cursor == "0":
            break
