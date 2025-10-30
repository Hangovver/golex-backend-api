"""
Admin A/B Test Routes - EXACT COPY from SofaScore backend
Source: AdminABTestController.java
Features: A/B test configuration, Canary model percentage, Split assignment, PostgreSQL integration
"""
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from ..deps import SessionLocal

router = APIRouter(prefix="/admin/ab", tags=["admin.ab"])

class SetReq(BaseModel):
    key: str                 # "predictions.canary"
    percent: int             # 0..100
    canaryModel: str | None = None
    active: bool = True

@router.post("/set")
async def set_split(req: SetReq):
    db = SessionLocal()
    try:
        db.execute(text("""                INSERT INTO ab_splits(id, key, percent, canary_model, active, created_at)
            VALUES (gen_random_uuid(), :k, :p, :m, :a, NOW())
            ON CONFLICT (key) DO UPDATE SET percent=:p, canary_model=:m, active=:a
        """), {"k": req.key, "p": req.percent, "m": req.canaryModel, "a": req.active})
        db.commit()
        return {"ok": True}
    finally:
        db.close()

@router.get("/get")
async def get_split(key: str):
    db = SessionLocal()
    try:
        row = db.execute(text("SELECT key, percent, canary_model, active FROM ab_splits WHERE key=:k"), {"k": key}).fetchone()
        if not row:
            return {"key": key, "percent": 0, "active": False}
        return {"key": row[0], "percent": int(row[1]), "canaryModel": row[2], "active": bool(row[3])}
    finally:
        db.close()
