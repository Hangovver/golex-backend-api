from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..deps import get_db

router = APIRouter(prefix="/ai", tags=["ai"])

def _ensure_table(db: Session):
    db.execute(text('''CREATE TABLE IF NOT EXISTS ai_model_bundle(
        id INT PRIMARY KEY DEFAULT 1,
        version TEXT NOT NULL,
        min_supported TEXT NOT NULL,
        force_refresh BOOLEAN NOT NULL DEFAULT FALSE,
        updated_at TIMESTAMP DEFAULT NOW()
    )'''))
    # seed row if empty
    row = db.execute(text("SELECT COUNT(*) FROM ai_model_bundle")).scalar()
    if row == 0:
        db.execute(text("INSERT INTO ai_model_bundle(id,version,min_supported,force_refresh) VALUES(1,'1.0.0','1.0.0',FALSE)"))
    db.commit()

@router.get("/model-bundle")
def get_model_bundle(db: Session = Depends(get_db)):
    _ensure_table(db)
    row = db.execute(text("SELECT version, min_supported, force_refresh FROM ai_model_bundle WHERE id=1")).fetchone()
    return {"version": row[0], "min_supported": row[1], "force_refresh": bool(row[2])}

@router.put("/model-bundle")
def update_model_bundle(version: str, min_supported: str, force_refresh: bool = False, db: Session = Depends(get_db)):
    _ensure_table(db)
    db.execute(text("UPDATE ai_model_bundle SET version=:v, min_supported=:m, force_refresh=:f, updated_at=NOW() WHERE id=1"),
               {"v": version, "m": min_supported, "f": force_refresh})
    db.commit()
    return {"ok": True}
