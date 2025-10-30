from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..deps import get_db
import json

router = APIRouter(prefix="/admin/ux", tags=["admin.ux"])

def _ensure(db: Session):
    db.execute(text('''CREATE TABLE IF NOT EXISTS ux_survey(
        id SERIAL PRIMARY KEY,
        ts TIMESTAMP DEFAULT NOW(),
        user_id TEXT,
        rating INT CHECK (rating BETWEEN 1 AND 5),
        tags JSONB,
        comment TEXT,
        app_ver TEXT
    )'''))
    db.commit()

@router.post("/survey")
def submit(rating: int, tags: list[str] | None = None, comment: str | None = None, user_id: str | None = None, app_ver: str | None = None, db: Session = Depends(get_db)):
    _ensure(db)
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="invalid rating")
    db.execute(text("INSERT INTO ux_survey(user_id, rating, tags, comment, app_ver) VALUES(:u,:r,:t,:c,:v)"),
               {"u": user_id, "r": rating, "t": json.dumps(tags or []), "c": comment, "v": app_ver})
    db.commit()
    return {"ok": True}

@router.get("/survey")
def list_surveys(limit: int = 50, db: Session = Depends(get_db)):
    _ensure(db)
    rows = db.execute(text("SELECT id, ts, user_id, rating, tags, comment, app_ver FROM ux_survey ORDER BY id DESC LIMIT :lim"), {"lim": limit}).fetchall()
    return {"items": [{"id": r[0], "ts": r[1].isoformat() if r[1] else None, "user_id": r[2], "rating": r[3], "tags": r[4] or [], "comment": r[5], "app_ver": r[6]} for r in rows]}
