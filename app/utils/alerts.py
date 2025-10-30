import os, json, aiohttp, asyncio
from .redis_pool import get_redis

async def send_alert(severity: str, title: str, body: dict | None = None):
    payload = {"severity": severity, "title": title, "body": body or {}}
    # Redis fallback
    r = await get_redis()
    await r.lpush("golex:alerts", json.dumps(payload))
    # Optional webhook
    url = os.getenv("ALERT_WEBHOOK_URL")
    if url:
        try:
            async with aiohttp.ClientSession() as s:
                await s.post(url, json=payload, timeout=4)
        except Exception:
            pass
