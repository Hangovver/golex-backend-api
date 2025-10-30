from fastapi import APIRouter, Header
from ..deps import SessionLocal
from sqlalchemy import text
from datetime import datetime, timezone
import hashlib

router = APIRouter(prefix="/mobile", tags=["mobile"])

DEFAULT_FLAGS = {
    "ui.enableCorners": True,
    "ui.enableCards": True,
    "pred.showHeuristicBadges": True,
    "net.sse.enabled": True,
    "prefetch.enabled": True
}

def _bucket(s: str, salt: str) -> int:
    h = hashlib.sha256((s + "::" + salt).encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 100

@router.get("/config")
async def mobile_config(x_device_id: str | None = Header(default=None)):
    db = SessionLocal()
    try:
        # load flags (optional table: mobile_flags)
        flags = dict(DEFAULT_FLAGS)
        try:
            rows = db.execute(text("SELECT key, value FROM mobile_flags WHERE active=TRUE")).fetchall()
            for k,v in rows:
                # supports boolean and string
                if v in ("true","false","1","0"):
                    flags[k] = v in ("true","1")
                else:
                    flags[k] = v
        except Exception:
            pass

        # A/B split for prefetch.policy
        ab = db.execute(text("SELECT percent, canary_model, active, salt FROM ab_splits WHERE key='prefetch.policy'")).fetchone()
        policy = "polite"
        salt = "golex-prefetch"
        pct = 0
        if ab:
            pct = int(ab[0] or 0)
            # store "canary_model" column as string variant name in this context (aggressive/polite)
            variant = ab[1] or "aggressive"
            active = bool(ab[2])
            salt = ab[3] or salt if len(ab) >= 4 else salt
            if active and x_device_id:
                b = _bucket(x_device_id, salt)
                if b < pct:
                    policy = variant
        res = {
            "version": datetime.now(timezone.utc).isoformat(),
            "flags": flags,
            "ab": {
                "prefetch.policy": {
                    "percent": pct,
                    "salt": salt,
                    "assigned": policy
                }
            }
        }
        return res
    finally:
        db.close()
