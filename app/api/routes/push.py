from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..deps import get_db  # assumes existing deps module
import re

router = APIRouter(prefix="/push", tags=["push"])

TOPIC_RE = re.compile(r"^(team|league):[0-9A-Za-z_-]+$")

def _ensure_tables(db: Session):
    db.execute(text('''CREATE TABLE IF NOT EXISTS push_tokens(
        token TEXT PRIMARY KEY,
        platform TEXT,
        device_id TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )'''))
    db.execute(text('''CREATE TABLE IF NOT EXISTS push_subs(
        token TEXT,
        topic TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )'''))
    db.commit()

@router.post("/register")
def register_token(token: str, platform: str = "android", device_id: str | None = None, db: Session = Depends(get_db)):
    _ensure_tables(db)
    if not token:
        raise HTTPException(status_code=400, detail="token required")
    db.execute(text("INSERT INTO push_tokens(token, platform, device_id) VALUES(:t,:p,:d) ON CONFLICT (token) DO UPDATE SET platform=:p, device_id=:d"), {"t": token, "p": platform, "d": device_id})
    db.commit()
    return {"ok": True}

@router.post("/subscribe")
def subscribe(token: str, topic: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    if not TOPIC_RE.match(topic):
        raise HTTPException(status_code=400, detail="invalid topic")
    db.execute(text("INSERT INTO push_subs(token, topic) VALUES(:t,:c)"), {"t": token, "c": topic})
    db.commit()
    return {"ok": True, "topic": topic}

@router.post("/unsubscribe")
def unsubscribe(token: str, topic: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    db.execute(text("DELETE FROM push_subs WHERE token=:t AND topic=:c"), {"t": token, "c": topic})
    db.commit()
    return {"ok": True}

@router.get("/my-topics")
def my_topics(token: str, db: Session = Depends(get_db)):
    _ensure_tables(db)
    rows = db.execute(text("SELECT topic FROM push_subs WHERE token=:t"), {"t": token}).fetchall()
    return {"topics": [r[0] for r in rows]}
