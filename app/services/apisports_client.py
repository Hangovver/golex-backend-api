"""
API-Sports (API-Football) upstream client (direct mode).
Enabled when APISPORTS_BASE and API_FOOTBALL_KEY are present and Proxy is not configured.
"""
import os, requests

BASE = (os.getenv("APISPORTS_BASE") or "").rstrip("/")
KEY  = os.getenv("API_FOOTBALL_KEY", "").strip()
TIMEOUT = float(os.getenv("PROXY_TIMEOUT_S", "6"))

def enabled() -> bool:
    return bool(BASE and KEY)

def _headers():
    # API-Football expects x-apisports-key
    return {"Accept": "application/json", "x-apisports-key": KEY}

def get_json(path: str, params: dict | None = None):
    if not enabled():
        raise RuntimeError("APISports not enabled")
    url = f"{BASE}{path}"
    r = requests.get(url, params=params or {}, headers=_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()
