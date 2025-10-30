from fastapi import APIRouter
import os, httpx

router = APIRouter(tags=["uat"], prefix="/uat")

@router.get("/readiness")
async def readiness():
    # simple readiness: AI reachable?, DB url/env set?, redis url set?
    ai = os.getenv('AI_ENGINE_URL', '')
    db = os.getenv('DATABASE_URL', '')
    redis = os.getenv('REDIS_URL', '')
    ok = True; details = {}
    # AI ping
    if ai:
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(ai + "/meta")
                details['ai'] = (r.status_code == 200)
                ok = ok and details['ai']
        except Exception:
            details['ai'] = False; ok = False
    else:
        details['ai'] = False; ok = False
    # Env checks
    details['db_env'] = bool(db)
    details['redis_env'] = bool(redis)
    ok = ok and details['db_env'] and details['redis_env']
    return {"ok": ok, "details": details}
