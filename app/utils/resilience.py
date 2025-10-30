import time, json, asyncio
import random
from typing import Optional
from .redis_pool import get_redis

# Defaults
RATE_LIMIT_KEY = "golex:rl:apifootball"
WINDOW_SEC = 60
WINDOW_LIMIT = 55   # conservative under 60/min vendor quota
CB_STATE_KEY = "golex:cb:apifootball"
CB_FAIL_WINDOW = 30
CB_FAIL_THRESHOLD = 8
CB_OPEN_SEC = 30

async def rate_limit_allow() -> bool:
    r = await get_redis()
    now = int(time.time())
    bucket = f"{RATE_LIMIT_KEY}:{now // WINDOW_SEC}"
    cnt = await r.incr(bucket)
    if cnt == 1:
        await r.expire(bucket, WINDOW_SEC + 5)
    return cnt <= WINDOW_LIMIT

async def cb_should_block() -> bool:
    r = await get_redis()
    state = await r.get(CB_STATE_KEY)
    if not state:
        return False
    s = json.loads(state)
    if s.get("open_until", 0) > time.time():
        return True
    return False

async def cb_report(success: bool):
    r = await get_redis()
    now = int(time.time())
    key = f"{CB_STATE_KEY}:fails:{now // CB_FAIL_WINDOW}"
    if success:
        # success: reset counter aggressively
        await r.delete(key)
        await r.set(CB_STATE_KEY, json.dumps({"open_until": 0}), ex=CB_FAIL_WINDOW)
        return
    fails = await r.incr(key)
    await r.expire(key, CB_FAIL_WINDOW + 5)
    if fails >= CB_FAIL_THRESHOLD:
        await r.set(CB_STATE_KEY, json.dumps({"open_until": time.time() + CB_OPEN_SEC}), ex=CB_OPEN_SEC)

async def backoff_delay(attempt: int) -> float:
    # jittered exponential backoff
    base = min(1.5 ** attempt, 8.0)
    return base + random.random()
