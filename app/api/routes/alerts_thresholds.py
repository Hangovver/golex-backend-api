from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db

router = APIRouter(tags=['admin'], prefix='/admin/alerts')

DDL = """CREATE TABLE IF NOT EXISTS admin_alert_thresholds(
  rule_name TEXT PRIMARY KEY,
  metric TEXT,
  threshold DOUBLE PRECISION NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)"""

def ensure(db: Session):
    db.execute(text(DDL)); db.commit()

class ThresholdBody(BaseModel):
    metric: str | None = None
    threshold: float = Field(gt=0)

@router.get('/thresholds')
def list_thresholds(db: Session = Depends(get_db)):
    ensure(db)
    rows = db.execute(text("SELECT rule_name, metric, threshold, updated_at FROM admin_alert_thresholds ORDER BY updated_at DESC")).fetchall()
    return {'thresholds': [{'rule_name': r[0], 'metric': r[1], 'threshold': float(r[2]), 'updated_at': r[3].isoformat() if r[3] else None} for r in rows]}

@router.put('/thresholds/{rule_name}')
def upsert_threshold(rule_name: str, b: ThresholdBody, db: Session = Depends(get_db)):
    ensure(db)
    before = _row_of(db, rule_name)
    db.execute(text("""INSERT INTO admin_alert_thresholds(rule_name, metric, threshold, updated_at)
                       VALUES (:rn, :m, :t, NOW())
                       ON CONFLICT (rule_name) DO UPDATE SET metric=:m, threshold=:t, updated_at=NOW()"""),
               {'rn': rule_name, 'm': b.metric, 't': b.threshold})
    db.commit()
    audit(db, 'upsert', rule_name, before, _row_of(db, rule_name))
    return {'ok': True}


from fastapi import HTTPException
import json

@router.delete('/thresholds/{rule_name}')
def delete_threshold(rule_name: str, db: Session = Depends(get_db)):
    ensure(db)
    before = _row_of(db, rule_name)
    r = db.execute(text("DELETE FROM admin_alert_thresholds WHERE rule_name=:rn"), {'rn': rule_name})
    db.commit()
    if r.rowcount == 0:
        raise HTTPException(404, detail="not found")
    audit(db, 'delete', rule_name, before, None)
    return {'ok': True}

@router.post('/thresholds/load_defaults')
def load_defaults(db: Session = Depends(get_db)):
    ensure(db)
    defaults = [
        ('shadow_l1_gt', 'shadow_l1', 0.35),
        ('live_latency', 'seconds', 8.0),
        ('ingestion_error_rate', 'ratio', 0.02),
    ]
    for rn, m, t in defaults:
        db.execute(text("""INSERT INTO admin_alert_thresholds(rule_name, metric, threshold, updated_at)
                           VALUES (:rn, :m, :t, NOW())
                           ON CONFLICT (rule_name) DO UPDATE SET metric=:m, threshold=:t, updated_at=NOW()"""),
                   {'rn': rn, 'm': m, 't': t})
    db.commit()
    audit(db, 'load_defaults', None, None, {'count': len(defaults)})
    return {'ok': True, 'count': len(defaults)}


from pydantic import BaseModel
from typing import List, Optional

class ThresholdIn(BaseModel):
    rule_name: str
    metric: Optional[str] = None
    threshold: float

class ThresholdsImport(BaseModel):
    thresholds: List[ThresholdIn]

@router.get('/thresholds/export')
def export_thresholds(db: Session = Depends(get_db)):
    ensure(db)
    rows = db.execute(text("SELECT rule_name, metric, threshold, updated_at FROM admin_alert_thresholds ORDER BY rule_name ASC")).fetchall()
    return {'thresholds': [{'rule_name': r[0], 'metric': r[1], 'threshold': float(r[2]), 'updated_at': r[3].isoformat() if r[3] else None} for r in rows]}

@router.post('/thresholds/import')
def import_thresholds(body: ThresholdsImport, db: Session = Depends(get_db)):
    ensure(db)
    for t in body.thresholds:
        db.execute(text("""INSERT INTO admin_alert_thresholds(rule_name, metric, threshold, updated_at)
                           VALUES (:rn, :m, :th, NOW())
                           ON CONFLICT (rule_name) DO UPDATE SET metric=:m, threshold=:th, updated_at=NOW()"""),
                   {'rn': t.rule_name, 'm': t.metric, 'th': t.threshold})
    db.commit()
    try:
        for t in body.thresholds:
            audit(db, 'import_upsert', t.rule_name, None, _row_of(db, t.rule_name))
    except Exception:
        pass
    return {'ok': True, 'count': len(body.thresholds)}


from uuid import uuid4
from fastapi import HTTPException
import json

VERS_DDL = """CREATE TABLE IF NOT EXISTS admin_alert_threshold_versions(
  id UUID PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  snapshot JSONB NOT NULL
)"""

def ensure_versions(db: Session):
    db.execute(text(VERS_DDL)); db.commit()

@router.post('/thresholds/version/snapshot')
def thresholds_snapshot(db: Session = Depends(get_db)):
    ensure(db); ensure_versions(db)
    rows = db.execute(text("SELECT rule_name, metric, threshold FROM admin_alert_thresholds ORDER BY rule_name ASC")).fetchall()
    snap = [{'rule_name': r[0], 'metric': r[1], 'threshold': float(r[2])} for r in rows]
    vid = str(uuid4())
    db.execute(text("INSERT INTO admin_alert_threshold_versions(id, snapshot) VALUES (:id, :snap::jsonb)"),
               {'id': vid, 'snap': json.dumps(snap)})
    db.commit()
    return {'ok': True, 'version_id': vid, 'count': len(snap)}

@router.get('/thresholds/version/list')
def thresholds_versions(db: Session = Depends(get_db), limit: int = 20):
    ensure_versions(db)
    rows = db.execute(text("SELECT id, created_at, jsonb_array_length(snapshot) FROM admin_alert_threshold_versions ORDER BY created_at DESC LIMIT :lim"),
                      {'lim': limit}).fetchall()
    return {'versions': [{'id': str(r[0]), 'created_at': r[1].isoformat() if r[1] else None, 'count': int(r[2])} for r in rows]}

@router.post('/thresholds/version/restore/{version_id}')
def thresholds_restore(version_id: str, db: Session = Depends(get_db)):
    ensure(db); ensure_versions(db)
    row = db.execute(text("SELECT snapshot FROM admin_alert_threshold_versions WHERE id=:id"), {'id': version_id}).fetchone()
    if not row:
        raise HTTPException(404, detail="version not found")
    snap = row[0]
    # upsert all
    for t in snap:
        db.execute(text("""INSERT INTO admin_alert_thresholds(rule_name, metric, threshold, updated_at)
                           VALUES (:rn, :m, :th, NOW())
                           ON CONFLICT (rule_name) DO UPDATE SET metric=:m, threshold=:th, updated_at=NOW()"""),
                   {'rn': t['rule_name'], 'm': t.get('metric'), 'th': float(t['threshold'])})
    db.commit()
    try:
        for t in snap:
            audit(db, 'restore', t['rule_name'], None, _row_of(db, t['rule_name']))
    except Exception:
        pass
    return {'ok': True, 'restored': len(snap)}


@router.get('/thresholds/version/diff/{version_id}')
def thresholds_diff(version_id: str, db: Session = Depends(get_db)):
    ensure(db); ensure_versions(db)
    cur = db.execute(text("SELECT rule_name, metric, threshold FROM admin_alert_thresholds")).fetchall()
    cur_map = { r[0]: {'metric': r[1], 'threshold': float(r[2])} for r in cur }
    row = db.execute(text("SELECT snapshot FROM admin_alert_threshold_versions WHERE id=:id"), {'id': version_id}).fetchone()
    if not row:
        raise HTTPException(404, detail="version not found")
    snap = { t['rule_name']: {'metric': t.get('metric'), 'threshold': float(t['threshold'])} for t in row[0] }

    added = [ {'rule_name': k, **v} for k,v in snap.items() if k not in cur_map ]
    removed = [ {'rule_name': k, **v} for k,v in cur_map.items() if k not in snap ]
    changed = []
    for k in set(cur_map.keys()).intersection(snap.keys()):
        a = cur_map[k]; b = snap[k]
        if a['metric'] != b['metric'] or abs(a['threshold'] - b['threshold']) > 1e-9:
            changed.append({'rule_name': k, 'current': a, 'snapshot': b})
    return {'added': added, 'removed': removed, 'changed': changed}


AUDIT_DDL = """CREATE TABLE IF NOT EXISTS admin_alert_threshold_audit(
  ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  action TEXT NOT NULL,
  rule_name TEXT,
  before JSONB,
  after  JSONB
)"""

def ensure_audit(db: Session):
    db.execute(text(AUDIT_DDL)); db.commit()

def _row_of(db: Session, rn: str):
    r = db.execute(text("SELECT rule_name, metric, threshold FROM admin_alert_thresholds WHERE rule_name=:rn"), {'rn': rn}).fetchone()
    if not r: return None
    return {'rule_name': r[0], 'metric': r[1], 'threshold': float(r[2])}

def audit(db: Session, action: str, rule_name: str | None, before: dict | None, after: dict | None):
    ensure_audit(db)
    db.execute(text("INSERT INTO admin_alert_threshold_audit(action, rule_name, before, after) VALUES (:a,:r,:b::jsonb,:f::jsonb)"),
               {'a': action, 'r': rule_name, 'b': json.dumps(before) if before is not None else None, 'f': json.dumps(after) if after is not None else None})
    db.commit()

@router.get('/thresholds/audit')
def audit_list(db: Session = Depends(get_db), limit: int = 200, action: str | None = None, rule_name: str | None = None, start_ts: str | None = None, end_ts: str | None = None, cursor: str | None = None):
    ensure_audit(db)
    qry = "SELECT ts, action, rule_name, before, after FROM admin_alert_threshold_audit"
    conds = []
    params = {"lim": limit}
    if action:
        conds.append("action = :a"); params["a"] = action
    if rule_name:
        conds.append("rule_name = :r"); params["r"] = rule_name
    if start_ts:
        conds.append("ts >= :st"); params["st"] = start_ts
    if end_ts:
        conds.append("ts <= :et"); params["et"] = end_ts
    if cursor:
        conds.append("ts < :cursor"); params["cursor"] = cursor
    if conds:
        qry += " WHERE " + " AND ".join(conds)
    qry += " ORDER BY ts DESC LIMIT :lim"
    rows = db.execute(text(qry), params).fetchall()
    def to_py(v): 
        try: 
            return json.loads(v) if isinstance(v, str) else v 
        except Exception: 
            return None
    next_cursor = rows[-1][0].isoformat() if len(rows)==limit and rows[-1][0] is not None else None
    return {'audit': [{'ts': r[0].isoformat() if r[0] else None, 'action': r[1], 'rule_name': r[2], 'before': to_py(r[3]), 'after': to_py(r[4])} for r in rows], 'next_cursor': next_cursor}


from fastapi import Response

@router.get('/thresholds/audit/export.csv')
def audit_export_csv(db: Session = Depends(get_db), limit: int = 1000, action: str | None = None, rule_name: str | None = None):
    # Reuse filters like audit_list
    qry = "SELECT ts, action, rule_name, before, after FROM admin_alert_threshold_audit"
    conds = []
    params = {"lim": limit}
    if action:
        conds.append("action = :a"); params["a"] = action
    if rule_name:
        conds.append("rule_name = :r"); params["r"] = rule_name
    if start_ts:
        conds.append("ts >= :st"); params["st"] = start_ts
    if end_ts:
        conds.append("ts <= :et"); params["et"] = end_ts
    if conds:
        qry += " WHERE " + " AND ".join(conds)
    qry += " ORDER BY ts DESC LIMIT :lim"
    rows = db.execute(text(qry), params).fetchall()
    # Build CSV
    import csv, io, json as _json
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ts","action","rule_name","before","after"])
    for r in rows:
        w.writerow([r[0].isoformat() if r[0] else "", r[1] or "", r[2] or "", (r[3] if isinstance(r[3], str) else _json.dumps(r[3]) if r[3] is not None else ""), (r[4] if isinstance(r[4], str) else _json.dumps(r[4]) if r[4] is not None else "")])
    return Response(content=buf.getvalue(), media_type='text/csv')


from fastapi import Response

@router.get('/thresholds/audit/export.jsonl')
def audit_export_jsonl(db: Session = Depends(get_db), limit: int = 1000, action: str | None = None, rule_name: str | None = None, start_ts: str | None = None, end_ts: str | None = None, cursor: str | None = None):
    qry = "SELECT ts, action, rule_name, before, after FROM admin_alert_threshold_audit"
    conds = []
    params = {"lim": limit}
    if action:
        conds.append("action = :a"); params["a"] = action
    if rule_name:
        conds.append("rule_name = :r"); params["r"] = rule_name
    if start_ts:
        conds.append("ts >= :st"); params["st"] = start_ts
    if end_ts:
        conds.append("ts <= :et"); params["et"] = end_ts
    if cursor:
        conds.append("ts < :cursor"); params["cursor"] = cursor
    if conds:
        qry += " WHERE " + " AND ".join(conds)
    qry += " ORDER BY ts DESC LIMIT :lim"
    rows = db.execute(text(qry), params).fetchall()
    import json as _json
    buf = io.StringIO()
    for r in rows:
        obj = {
            "ts": r[0].isoformat() if r[0] else None,
            "action": r[1], "rule_name": r[2],
            "before": r[3] if isinstance(r[3], str) else _json.dumps(r[3]) if r[3] is not None else None,
            "after":  r[4] if isinstance(r[4], str) else _json.dumps(r[4]) if r[4] is not None else None,
        }
        buf.write(_json.dumps(obj) + "\n")
    return Response(content=buf.getvalue(), media_type='application/x-ndjson')
