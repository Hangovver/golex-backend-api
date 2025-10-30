from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db

router = APIRouter(tags=['admin'], prefix='/admin/alerts')

def _one(db: Session, q: str, args: dict = {}):
    row = db.execute(text(q), args).fetchone()
    return row

@router.get('/overview')
def overview(db: Session = Depends(get_db), hours: int = Query(24, ge=1, le=7*24)):
    # throttle cfg
    cfg = _one(db, "SELECT window_minutes, max_per_window, escalate_topic FROM admin_alert_cfg WHERE id=1")
    throttle = {
        "window_minutes": int(cfg[0]) if cfg else 60,
        "max_per_window": int(cfg[1]) if cfg else 3,
        "escalate_topic": cfg[2] if cfg else "admin_urgent",
    }
    # active mutes
    mutes = db.execute(text("SELECT id, rule_name, metric, until, reason FROM admin_alert_mutes WHERE until > NOW() ORDER BY until DESC")).fetchall()
    mutes_json = [{"id": r[0], "rule_name": r[1], "metric": r[2], "until": r[3].isoformat() if r[3] else None, "reason": r[4]} for r in mutes]
    # event summary
    cnt_all = _one(db, "SELECT COUNT(*) FROM admin_alert_events WHERE created_at >= NOW() - (:h || ' hours')::interval", {"h": hours})
    by_type = db.execute(text("SELECT type, COUNT(*) FROM admin_alert_events WHERE created_at >= NOW() - (:h || ' hours')::interval GROUP BY type ORDER BY 2 DESC"),
                         {"h": hours}).fetchall()
    return {
        "throttle": throttle,
        "mutes_active": mutes_json,
        "events_last_hours": {
            "hours": hours,
            "count": int(cnt_all[0]) if cnt_all and cnt_all[0] is not None else 0,
            "by_type": [{"type": r[0], "count": int(r[1])} for r in by_type]
        }
    }


from fastapi.responses import PlainTextResponse

@router.get('/overview/events')
def events_recent(db: Session = Depends(get_db), hours: int = Query(24, ge=1, le=7*24), limit: int = Query(200, ge=1, le=5000), format: str = Query("json"), dtfmt: str = Query("%Y-%m-%d %H:%M:%S"), bom: bool = Query(False)):
    rows = db.execute(text("""SELECT created_at, rule_name, type, message
                             FROM admin_alert_events
                             WHERE created_at >= NOW() - (:h || ' hours')::interval
                             ORDER BY created_at DESC
                             LIMIT :lim"""), {'h': hours, 'lim': limit}).fetchall()
    if format.lower() == 'csv':
        import csv, io, codecs, datetime
        buf = io.StringIO()
        w = csv.writer(buf)
        fmt = dtfmt
        w.writerow(['created_at','rule_name','type','message'])
        for r in rows:
            ts = r[0].strftime(fmt) if r[0] else ''
            w.writerow([ts, r[1], r[2], r[3]])
        out = buf.getvalue()
        if bom:
            out = '\ufeff' + out
        return PlainTextResponse(out, media_type='text/csv')
    return {'events': [{'created_at': r[0].isoformat() if r[0] else None, 'rule_name': r[1], 'type': r[2], 'message': r[3]} for r in rows]}
