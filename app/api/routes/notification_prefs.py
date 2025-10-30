from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db

router = APIRouter(tags=['notify'], prefix='/notify/prefs')

class PrefsBody(BaseModel):
    device_id: str = Field(min_length=4)
    kickoff: bool | None = None
    goals: bool | None = None
    final: bool | None = None
    predictions: bool | None = None

@router.get('/{device_id}')
def get_prefs(device_id: str, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT kickoff, goals, final, predictions FROM user_notification_prefs WHERE device_id=:d"), {'d': device_id}).fetchone()
    if not row:
        # defaults
        return {"device_id": device_id, "kickoff": True, "goals": True, "final": True, "predictions": True}
    return {"device_id": device_id, "kickoff": row[0], "goals": row[1], "final": row[2], "predictions": row[3]}

@router.post('/set')
def set_prefs(b: PrefsBody, db: Session = Depends(get_db)):
    # upsert
    fields = []
    params = {'d': b.device_id}
    for k in ['kickoff','goals','final','predictions']:
        v = getattr(b, k)
        if v is not None:
            fields.append(f"{k}=:{k}")
            params[k] = v
    if not fields:
        raise HTTPException(400, detail="no fields provided")
    set_clause = ", ".join(fields) + ", updated_at=NOW()"
    db.execute(text(f"INSERT INTO user_notification_prefs(device_id) VALUES (:d) ON CONFLICT (device_id) DO NOTHING"), {'d': b.device_id})
    db.execute(text(f"UPDATE user_notification_prefs SET {set_clause} WHERE device_id=:d"), params)
    db.commit()
    return {"ok": True}
