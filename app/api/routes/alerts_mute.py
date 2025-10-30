from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db

router = APIRouter(tags=['admin'], prefix='/admin/alerts')

DDL = """CREATE TABLE IF NOT EXISTS admin_alert_mutes(
  id BIGSERIAL PRIMARY KEY,
  rule_name TEXT,
  metric TEXT,
  until TIMESTAMPTZ NOT NULL,
  reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)"""

def ensure(db: Session):
    db.execute(text(DDL)); db.commit()

class MuteBody(BaseModel):
    rule_name: str | None = Field(default=None)
    metric: str | None = Field(default=None)
    minutes: int = Field(default=120, ge=5, le=7*24*60)
    reason: str | None = None

@router.post('/mute')
def mute(b: MuteBody, db: Session = Depends(get_db)):
    ensure(db)
    if not b.rule_name and not b.metric:
        raise HTTPException(400, detail='rule_name or metric required')
    db.execute(text("INSERT INTO admin_alert_mutes(rule_name, metric, until, reason) VALUES (:rn, :m, NOW() + (:mins || ' minutes')::interval, :r)"),
               {'rn': b.rule_name, 'm': b.metric, 'mins': b.minutes, 'r': b.reason})
    db.commit()
    return {'ok': True}

@router.get('/mute')
def list_mutes(db: Session = Depends(get_db), active_only: bool = Query(True), q: str | None = Query(None), sort: str = Query('until'), order: str = Query('desc')):
    ensure(db)
    
    where = "WHERE 1=1 "
    if active_only:
        where += "AND until > NOW() "
    params = {}
    if q:
        where += "AND (COALESCE(rule_name,'') ILIKE :qq OR COALESCE(metric,'') ILIKE :qq) "
        params['qq'] = f"%{q}%"
    sort_col = 'until' if sort not in ('created_at','until','rule_name','metric') else sort
    ord_dir = 'DESC' if order.lower()!='asc' else 'ASC'
    qsql = f"SELECT id, rule_name, metric, until, reason FROM admin_alert_mutes {where} ORDER BY {sort_col} {ord_dir}"
    rows = db.execute(text(qsql), params).fetchall()
    return {'mutes': [{'id': r[0], 'rule_name': r[1], 'metric': r[2], 'until': r[3].isoformat() if r[3] else None, 'reason': r[4]} for r in rows]}


class ExtendBody(BaseModel):
    id: int
    minutes: int = Field(ge=1, le=7*24*60)

@router.post('/mute/extend')
def extend(b: ExtendBody, db: Session = Depends(get_db)):
    ensure(db)
    db.execute(text("UPDATE admin_alert_mutes SET until = GREATEST(until, NOW()) + (:mins || ' minutes')::interval WHERE id=:i"),
               {'i': b.id, 'mins': b.minutes})
    db.commit()
    return {'ok': True}

@router.delete('/mute/{id}')
def delete_mute(id: int, db: Session = Depends(get_db)):
    ensure(db)
    db.execute(text("DELETE FROM admin_alert_mutes WHERE id=:i"), {'i': id})
    db.commit()
    return {'ok': True}
