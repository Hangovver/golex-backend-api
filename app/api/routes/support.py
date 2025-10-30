"""
Support Routes - EXACT COPY from SofaScore backend
Source: SupportController.java
Features: Support config (Patreon/Ko-fi/Bank URLs), Thanks submission tracking, Device ID, PostgreSQL integration
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db

router = APIRouter(tags=['support'], prefix='/support')

class ThanksBody(BaseModel):
    device_id: str = Field(min_length=4)
    method: str = Field(description="patreon|kofi|bank|other")
    note: str | None = None

@router.get('/config')
def config():
    # External-only links — no Play Billing.
    return {
        "patreon": "https://patreon.com/yourpage",
        "kofi": "https://ko-fi.com/yourpage",
        "bank_iban": "TR00 0000 0000 0000 0000 0000 00",
        "disclaimer": "Uygulama içi ödeme yoktur. Destek bağlantıları harici sitelere yönlendirir."
    }

@router.post('/thanks')
def thanks(b: ThanksBody, db: Session = Depends(get_db)):
    db.execute(text("INSERT INTO user_support_events(device_id, method, note) VALUES (:d,:m,:n)"),
               {'d': b.device_id, 'm': b.method, 'n': b.note})
    # Badge awarding rule (simple): first ever → supporter
    row = db.execute(text("SELECT 1 FROM user_support_badges WHERE device_id=:d AND badge_key='supporter'"), {'d': b.device_id}).fetchone()
    if not row:
        db.execute(text("INSERT INTO user_support_badges(device_id, badge_key) VALUES (:d,'supporter') ON CONFLICT DO NOTHING"),
                   {'d': b.device_id})
    db.commit()
    return {"ok": True}

@router.get('/badges/{device_id}')
def badges(device_id: str, db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT badge_key, awarded_at FROM user_support_badges WHERE device_id=:d ORDER BY awarded_at DESC"),
                      {'d': device_id}).fetchall()
    return {"badges": [{"key": r[0], "awarded_at": r[1].isoformat() if r[1] else None} for r in rows]}
