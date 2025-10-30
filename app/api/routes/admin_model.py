"""
Admin Model Routes - EXACT COPY from SofaScore backend
Source: AdminModelController.java
Features: Model registry (register/activate/list), Version management, PostgreSQL integration
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db

router = APIRouter(tags=["admin"], prefix="/admin")


@router.post("/model/register")
def register_model(version: str, db: Session = Depends(get_db)):
    db.execute(text("INSERT INTO model_registry(version,is_active) VALUES (:v,false) ON CONFLICT (version) DO NOTHING"), {"v": version})
    db.commit()
    return {"ok": True, "version": version}


@router.post("/model/activate")
def activate_model(version: str, db: Session = Depends(get_db)):
    db.execute(text("UPDATE model_registry SET is_active=false"))
    n = db.execute(text("UPDATE model_registry SET is_active=true WHERE version=:v"), {"v": version}).rowcount
    db.commit()
    if n == 0:
        raise HTTPException(404, detail="version not found")
    # persist active version in settings (for AI routing decisions if needed)
    db.execute(text("INSERT INTO settings(key,value) VALUES ('ai_active_model', :v) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value"), {"v": version})
    db.commit()
    return {"ok": True, "active": version}


@router.get("/model/active")
def active_model(db: Session = Depends(get_db)):
    row = db.execute(text("SELECT value FROM settings WHERE key='ai_active_model'" )).fetchone()
    return {"active": row[0] if row else None}


@router.get("/thresholds/check")
def thresholds_check(db: Session = Depends(get_db)):
    # simple last-7 days check vs thresholds
    floor = float(db.execute(text("SELECT value FROM settings WHERE key='accuracy_floor'" )).scalar() or 0.5)
    ceil = float(db.execute(text("SELECT value FROM settings WHERE key='ece_ceil'" )).scalar() or 0.12)
    rows = list(db.execute(text("SELECT day, served, correct, COALESCE(ece,0) FROM model_metrics_daily ORDER BY day DESC LIMIT 7")))
    if not rows:
        return {"ok": False, "reason": "no-metrics"}
    accs = [ (float(c)/float(s)) for _, s, c, _ in rows if s ]
    eces = [ float(e) for *_, e in rows ]
    latest_ok = (accs[0] if accs else 0.0) >= floor and (eces[0] if eces else 0.0) <= ceil
    return {"ok": latest_ok, "accuracy_floor": floor, "ece_ceil": ceil, "latest": {"accuracy": (accs[0] if accs else None), "ece": (eces[0] if eces else None)}}
