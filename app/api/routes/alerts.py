from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db
from ...utils.fcm_sender import send_to_topic
from .alerts_cfg import get_throttle
import asyncio, json

router = APIRouter(tags=['admin'], prefix='/admin/alerts')

# Ensure tables exist
DDL_RULES = """CREATE TABLE IF NOT EXISTS admin_alert_rules(
  name TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  threshold DOUBLE PRECISION NOT NULL,
  target_topic TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)"""
DDL_EVENTS = """CREATE TABLE IF NOT EXISTS admin_alert_events(
  id BIGSERIAL PRIMARY KEY,
  rule_name TEXT NOT NULL,
  type TEXT NOT NULL,
  message TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)"""

def ensure_tables(db: Session):
    db.execute(text(DDL_RULES)); db.execute(text(DDL_EVENTS)); db.commit()

class RuleBody(BaseModel):
    name: str
    type: str = Field(description="shadow_l1_gt | ece_gt | logloss_gt")
    threshold: float
    target_topic: str = Field(default="admin")

@router.post('/rules')
def upsert_rule(b: RuleBody, db: Session = Depends(get_db)):
    ensure_tables(db)
    db.execute(text("""INSERT INTO admin_alert_rules(name, type, threshold, target_topic, updated_at)
                      VALUES (:n,:t,:th,:tt,NOW())
                      ON CONFLICT (name) DO UPDATE SET type=:t, threshold=:th, target_topic=:tt, updated_at=NOW()"""),
               {'n': b.name, 't': b.type, 'th': b.threshold, 'tt': b.target_topic})
    db.commit()
    return {'ok': True}

@router.get('/rules')
def list_rules(db: Session = Depends(get_db)):
    ensure_tables(db)
    rows = db.execute(text("SELECT name, type, threshold, target_topic, updated_at FROM admin_alert_rules ORDER BY name"))
    return {'rules': [{'name':r[0],'type':r[1],'threshold':float(r[2]),'target_topic':r[3],'updated_at':r[4].isoformat() if r[4] else None} for r in rows]}

class EvalBody(BaseModel):
    hours: int = 24

async def _send_and_log(db: Session, rule_name: str, typ: str, title: str, body: str, data: dict, target_topic: str):
    # send
    await send_to_topic(target_topic, title, body, data)
    # log
    db.execute(text("INSERT INTO admin_alert_events(rule_name, type, message, payload) VALUES (:rn,:t,:m,:p)"),
               {'rn': rule_name, 't': typ, 'm': body, 'p': json.dumps({'title': title, 'data': data, 'topic': target_topic})})
    db.commit()

@router.post('/evaluate/shadow')
async def eval_shadow(b: EvalBody, db: Session = Depends(get_db)):
    ensure_tables(db)
    rules = list(db.execute(text("SELECT name, threshold, target_topic FROM admin_alert_rules WHERE type='shadow_l1_gt'")))
    if not rules:
        return {'evaluated': 0, 'alerts': 0}

    row = db.execute(text("""SELECT COALESCE(AVG(l1),0) FROM predictions_shadow_log
                           WHERE created_at >= NOW() - (:h || ' hours')::interval"""),
                     {'h': b.hours}).fetchone()
    avg_l1 = float(row[0]) if row and row[0] is not None else 0.0

    alerts = 0
    cfg = get_throttle(db)
    win = int(cfg.get('window_minutes',60))
    cap = int(cfg.get('max_per_window',3))
    esc = cfg.get('escalate_topic','admin_urgent')
    recent = db.execute(text("""SELECT COUNT(*) FROM admin_alert_events WHERE created_at >= NOW() - (:w || ' minutes')::interval"""), {'w': win}).fetchone()
    recent_count = int(recent[0]) if recent and recent[0] is not None else 0
    for name, th, tgt in rules:
        th = float(th)
        if avg_l1 > th:
            if _is_muted(db, name, 'shadow_l1'): continue
            title = "Model Alert: Shadow L1 yüksek"
            body = f"Son {b.hours}s AA L1={avg_l1:.3f} > eşik {th:.3f}"
            data = {"type":"admin_alert","metric":"shadow_l1","avg_l1":avg_l1}
            if recent_count < cap:
            await _send_and_log(db, name, "shadow_l1_gt", title, body, data, tgt)
            recent_count += 1
        else:
            await _send_and_log(db, name, "shadow_l1_gt", title+" (ESCALATE)", body, data, esc)
            alerts += 1
    return {'evaluated': len(rules), 'avg_l1': avg_l1, 'alerts': alerts}

@router.get('/events')

def _is_muted(db: Session, rule_name: str | None, metric: str | None) -> bool:
    cond = []
    if rule_name:
        cond.append("rule_name = :rn")
    if metric:
        cond.append("metric = :m")
    if not cond:
        return False
    where = " AND ".join(cond) + " AND until > NOW()"
    q = "SELECT 1 FROM admin_alert_mutes WHERE " + where + " LIMIT 1"
    row = db.execute(text(q), {'rn': rule_name, 'm': metric}).fetchone()
    return bool(row)
def events(db: Session = Depends(get_db), hours: int = Query(72, ge=1, le=24*14), limit: int = Query(200, ge=1, le=1000)):
    ensure_tables(db)
    rows = db.execute(text("""SELECT id, rule_name, type, message, payload, created_at
                             FROM admin_alert_events
                             WHERE created_at >= NOW() - (:h || ' hours')::interval
                             ORDER BY created_at DESC
                             LIMIT :lim"""), {'h': hours, 'lim': limit}).fetchall()
    return {'events': [{'id': r[0], 'rule': r[1], 'type': r[2], 'message': r[3],
                        'payload': r[4], 'created_at': r[5].isoformat() if r[5] else None} for r in rows]}
