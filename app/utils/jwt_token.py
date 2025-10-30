import os, time, json, base64, hmac, hashlib

# Minimal JWT (HS256) without external deps
def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

def _b64d(s: str) -> bytes:
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s.encode("ascii"))

def sign(payload: dict, exp_seconds: int = 3600, secret: str | None = None) -> str:
    secret = (secret or os.getenv("JWT_SECRET") or "dev-secret").encode("utf-8")
    header = {"alg": "HS256", "typ": "JWT"}
    payload = dict(payload)
    payload["exp"] = int(time.time()) + exp_seconds
    head_b64 = _b64e(json.dumps(header, separators=(",",":")).encode("utf-8"))
    pay_b64  = _b64e(json.dumps(payload, separators=(",",":")).encode("utf-8"))
    data = f"{head_b64}.{pay_b64}".encode("utf-8")
    sig = hmac.new(secret, data, hashlib.sha256).digest()
    return f"{head_b64}.{pay_b64}.{_b64e(sig)}"

def verify(token: str, secret: str | None = None) -> dict | None:
    secret = (secret or os.getenv("JWT_SECRET") or "dev-secret").encode("utf-8")
    try:
        head_b64, pay_b64, sig_b64 = token.split(".")
        data = f"{head_b64}.{pay_b64}".encode("utf-8")
        sig = _b64d(sig_b64)
        ok = hmac.compare_digest(sig, hmac.new(secret, data, hashlib.sha256).digest())
        if not ok: return None
        payload = json.loads(_b64d(pay_b64).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()): return None
        return payload
    except Exception:
        return None
