from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db

router = APIRouter(tags=['admin'], prefix='/admin/alerts')

class ThrottleCfg(BaseModel):
    window_minutes: int = Field(default=60, ge=5, le=24*60)
    max_per_window: int = Field(default=3, ge=1, le=1000)
    escalate_topic: str = Field(default='admin_urgent')

@router.post('/throttle')
def set_throttle(b: ThrottleCfg, db: Session = Depends(get_db)):
    db.execute(text("""CREATE TABLE IF NOT EXISTS admin_alert_cfg(
        id INT PRIMARY KEY DEFAULT 1,
        window_minutes INT NOT NULL,
        max_per_window INT NOT NULL,
        escalate_topic TEXT NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )"""))
    db.execute(text("""INSERT INTO admin_alert_cfg(id, window_minutes, max_per_window, escalate_topic, updated_at)
                      VALUES (1, :w, :m, :t, NOW())
                      ON CONFLICT (id) DO UPDATE SET window_minutes=:w, max_per_window=:m, escalate_topic=:t, updated_at=NOW()"""),
               {'w': b.window_minutes, 'm': b.max_per_window, 't': b.escalate_topic})
    db.commit()
    return {'ok': True}

@router.get('/throttle')
def get_throttle(db: Session = Depends(get_db)):
    row = db.execute(text("SELECT window_minutes, max_per_window, escalate_topic FROM admin_alert_cfg WHERE id=1")).fetchone()
    if not row:
        return ThrottleCfg().dict()
    return {'window_minutes': int(row[0]), 'max_per_window': int(row[1]), 'escalate_topic': row[2]}
