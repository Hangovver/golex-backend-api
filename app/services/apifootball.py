import httpx, asyncio
from ..config import settings
from ..utils.resilience import rate_limit_allow, cb_should_block, cb_report, backoff_delay

class ApiFootball:
    def __init__(self, timeout=10.0):
        self.base = str(settings.API_FOOTBALL_BASE_URL).rstrip("/") + "/"
        self.key = settings.API_FOOTBALL_KEY
        self.client = httpx.AsyncClient(timeout=timeout)

    async def get(self, path: str, params: dict | None = None):
        if not self.key:
            raise RuntimeError("API_FOOTBALL_KEY not configured")
        if await cb_should_block():
            raise RuntimeError("circuit_open")
        if not await rate_limit_allow():
            raise RuntimeError("rate_limited")

        url = self.base + path.lstrip("/")
        headers = {"x-apisports-key": self.key, "Accept": "application/json"}
        last_exc = None
        for attempt in range(4):  # 1 + 3 retries
            try:
                r = await self.client.get(url, params=params or {}, headers=headers)
                if r.status_code in (429, 503, 500):
                    raise httpx.HTTPError(f"upstream {r.status_code}")
                r.raise_for_status()
                await cb_report(True)
                return r.json()
            except Exception as e:
                last_exc = e
                await cb_report(False)
                if attempt < 3:
                    await asyncio.sleep(await backoff_delay(attempt+1))
                else:
                    break
        raise last_exc
