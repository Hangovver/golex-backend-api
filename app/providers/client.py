import os, time, json, logging
from typing import Dict, Any
import http.client
from urllib.parse import urlencode
from .rate_limiter import RateLimiter
from .breaker import CircuitBreaker

logger = logging.getLogger("api_football")

class ApiFootballClient:
    BASE_HOST = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")
    API_KEY = os.getenv("API_FOOTBALL_KEY", "")
    # default 120 req/min (adjust via env)
    RATE_PER_MIN = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "120"))

    def __init__(self):
        self.limiter = RateLimiter(rate=self.RATE_PER_MIN, per=60.0)
        self.breaker = CircuitBreaker(failure_threshold=5, recovery_time=30)

    def _headers(self) -> Dict[str,str]:
        return {
            "x-apisports-key": self.API_KEY,
            "Accept": "application/json",
        }

    def get(self, path: str, params: Dict[str, Any]|None=None) -> Dict[str, Any]:
        # Circuit breaker
        self.breaker.before_call()

        # Rate limit
        self.limiter.consume()

        query = f"{path}"
        if params:
            query += "?" + urlencode(params, doseq=True)

        conn = http.client.HTTPSConnection(self.BASE_HOST, timeout=15)
        try:
            conn.request("GET", query, headers=self._headers())
            resp = conn.getresponse()
            data = resp.read().decode("utf-8")
            if resp.status >= 500:
                # server error → trigger retry via breaker
                raise RuntimeError(f"API server error {resp.status}")
            if resp.status == 429:
                # rate limited; sleep and raise to allow caller retry policy
                time.sleep(1.0)
                raise RuntimeError("Rate limited 429")
            self.breaker.success()
            try:
                return json.loads(data)
            except Exception:
                return {"raw": data, "status": resp.status}
        except Exception as e:
            self.breaker.failure(e)
            raise
        finally:
            conn.close()
