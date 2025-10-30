"""
Minimal HTTP client targeting Railway proxy endpoints.
Env:
  PROXY_BASE_URL   -> e.g. https://golex-proxy.up.railway.app
  PROXY_AUTH_HEADER (optional) -> e.g. "Authorization"
  PROXY_AUTH_TOKEN  (optional) -> e.g. "Bearer abc..."
  PROXY_TIMEOUT_S   (optional) -> default 6
"""
import os, requests

BASE = (os.getenv("PROXY_BASE_URL") or os.getenv("GATEWAY_BASE_URL") or os.getenv("RAILWAY_GATEWAY_URL") or "").rstrip("/")
AUTH_HEADER = (os.getenv("PROXY_AUTH_HEADER") or os.getenv("X_PROXY_AUTH_HEADER") or "").strip()
AUTH_TOKEN  = (os.getenv("PROXY_AUTH_TOKEN") or os.getenv("APP_CLIENT_TOKEN") or "").strip()
TIMEOUT = float(os.getenv("PROXY_TIMEOUT_S", "6"))
QUERY_TOKEN_KEY = (os.getenv("PROXY_QUERY_TOKEN_KEY") or "token")
QUERY_TOKEN_VAL = (os.getenv("ALLOW_QUERY_TOKEN") or "")

def enabled() -> bool:
    return bool(BASE)

def _headers():
    h = {"Accept":"application/json"}
    if AUTH_HEADER and AUTH_TOKEN:
        h[AUTH_HEADER] = AUTH_TOKEN
    return h

def get_json(path: str, params: dict | None = None):
    if not enabled():
        raise RuntimeError("PROXY_BASE_URL not set")
    url = f"{BASE}{path}"
    q = dict(params or {})
        if QUERY_TOKEN_VAL:
            q[QUERY_TOKEN_KEY] = QUERY_TOKEN_VAL
        r = requests.get(url, params=q, headers=_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()
