from fastapi import Request, HTTPException
import os, aioredis, time

async def rate_limit(request: Request, key_prefix: str = 'ip', limit: int = 60, window: int = 60):
    ip = request.client.host if request.client else 'unknown'
    key = f"rate:{key_prefix}:{ip}"
    url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis = await aioredis.from_url(url, decode_responses=True)
    cnt = await redis.incr(key)
    if cnt == 1:
        await redis.expire(key, window)
    await redis.close()
    if cnt > limit:
        raise HTTPException(429, detail='rate limit exceeded')
