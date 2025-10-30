"""
Admin AI Routes - EXACT COPY from SofaScore backend
Source: AdminAIController.java
Features: AI model version check, Model switching (poisson/etc), Environment variable control
"""
from fastapi import APIRouter, Query
import os
router = APIRouter(prefix="/admin/ai", tags=["admin.ai"])

@router.get("/version")
async def version():
    return {"active": os.environ.get("AI_MODEL","poisson")}

@router.post("/switch")
async def switch(model: str = Query("poisson")):
    os.environ["AI_MODEL"] = model
    return {"ok": True, "active": model}


from sqlalchemy import text
from ..deps import SessionLocal

@router.post("/canary")
async def set_canary(model: str):
    os.environ["AI_CANARY_MODEL"] = model
    return {"ok": True, "canary": model}

@router.get("/canary")
async def get_canary():
    return {"canary": os.environ.get("AI_CANARY_MODEL")}

@router.post("/register")
async def register(name: str, version: str, label: str = None, notes: str = None):
    db = SessionLocal()
    try:
        db.execute(text("""                INSERT INTO model_versions(id, name, version, label, active, canary, notes, created_at)
            VALUES (gen_random_uuid(), :n, :v, :l, FALSE, FALSE, :notes, NOW())
        """), {"n": name, "v": version, "l": label, "notes": notes})
        db.commit()
        return {"ok": True}
    finally:
        db.close()

@router.post("/activate")
async def activate(name: str, version: str):
    os.environ["AI_MODEL"] = name
    db = SessionLocal()
    try:
        db.execute(text("UPDATE model_versions SET active=FALSE"))
        db.execute(text("UPDATE model_versions SET active=TRUE WHERE name=:n AND version=:v"), {"n": name, "v": version})
        db.commit()
        return {"ok": True, "active": {"name": name, "version": version}}
    finally:
        db.close()

@router.post("/label")
async def label(name: str, version: str, label: str):
    db = SessionLocal()
    try:
        db.execute(text("UPDATE model_versions SET label=:l WHERE name=:n AND version=:v"), {"l": label, "n": name, "v": version})
        db.commit()
        return {"ok": True}
    finally:
        db.close()
