from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..deps import get_db
from datetime import datetime

router = APIRouter(prefix="/sync", tags=["sync"])

def _ensure(db: Session):
    db.execute(text('''CREATE TABLE IF NOT EXISTS user_state(
        user_id TEXT PRIMARY KEY,
        payload JSONB,
        updated_at TIMESTAMP DEFAULT NOW()
    )'''))
    db.commit()

@router.get("/state")
def get_state(user_id: str, db: Session = Depends(get_db)):
    _ensure(db)
    row = db.execute(text("SELECT payload, updated_at FROM user_state WHERE user_id=:u"), {"u": user_id}).fetchone()
    if not row:
        return {"user_id": user_id, "payload": {}, "updated_at": None}
    return {"user_id": user_id, "payload": row[0], "updated_at": row[1].isoformat() if row[1] else None}

@router.put("/state")
def put_state(user_id: str, payload: dict, updated_at: str, db: Session = Depends(get_db)):
    _ensure(db)
    # simple LWW: accept if incoming updated_at >= existing
    row = db.execute(text("SELECT updated_at FROM user_state WHERE user_id=:u"), {"u": user_id}).fetchone()
    incoming = datetime.fromisoformat(updated_at.replace('Z',''))
    if row:
        cur = row[0]
        if cur and cur > incoming:
            raise HTTPException(status_code=409, detail="remote_newer")
        db.execute(text("UPDATE user_state SET payload=:p, updated_at=:t WHERE user_id=:u"), {"p": payload, "t": incoming, "u": user_id})
    else:
        db.execute(text("INSERT INTO user_state(user_id, payload, updated_at) VALUES(:u,:p,:t)"),
                   {"u": user_id, "p": payload, "t": incoming})
    db.commit()
    return {"ok": True}
