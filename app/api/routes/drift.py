from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..deps import get_db
import math, json

router = APIRouter(prefix="/admin/drift", tags=["admin.drift"])

def _ensure(db: Session):
    db.execute(text('''CREATE TABLE IF NOT EXISTS drift_baseline(
        id INT PRIMARY KEY DEFAULT 1,
        bins INT NOT NULL DEFAULT 10,
        home JSONB,
        draw JSONB,
        away JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    )'''))
    db.execute(text('''CREATE TABLE IF NOT EXISTS drift_alerts(
        id SERIAL PRIMARY KEY,
        psi_home REAL,
        psi_draw REAL,
        psi_away REAL,
        bins INT,
        created_at TIMESTAMP DEFAULT NOW(),
        severity TEXT
    )'''))
    db.commit()

def _bins(vals, k):
    buckets = [0]*k
    for v in vals:
        i = int(min(k-1, max(0, v * k)))
        buckets[i] += 1
    total = float(len(vals)) or 1.0
    return [c/total for c in buckets]

def _psi(expected, actual):
    eps = 1e-6
    s = 0.0
    for e,a in zip(expected, actual):
        e = max(e, eps); a = max(a, eps)
        s += (a - e) * math.log(a / e)
    return s

@router.post("/baseline")
def make_baseline(bins: int = 10, db: Session = Depends(get_db)):
    _ensure(db)
    cur = db.execute(text("SELECT p_home,p_draw,p_away FROM calibration_samples"))
    h = []; d = []; a = []
    for ph,pd,pa in cur.fetchall():
        h.append(ph); d.append(pd); a.append(pa)
    base = {"home": _bins(h, bins), "draw": _bins(d, bins), "away": _bins(a, bins)}
    db.execute(text("INSERT INTO drift_baseline(id,bins,home,draw,away) VALUES(1,:b,:h,:d,:a) ON CONFLICT (id) DO UPDATE SET bins=:b, home=:h, draw=:d, away=:a"),
               {"b": bins, "h": json.dumps(base['home']), "d": json.dumps(base['draw']), "a": json.dumps(base['away'])})
    db.commit()
    return {"ok": True, "bins": bins}

@router.post("/check")
def check(window_rows: int = 200, db: Session = Depends(get_db)):
    _ensure(db)
    base = db.execute(text("SELECT bins, home, draw, away FROM drift_baseline WHERE id=1")).fetchone()
    if not base:
        return {"error": "no baseline"}
    bins, bh, bd, ba = base[0], base[1], base[2], base[3]
    cur = db.execute(text("SELECT p_home,p_draw,p_away FROM calibration_samples ORDER BY ts DESC LIMIT :lim"), {"lim": window_rows})
    h = []; d = []; a = []
    for ph,pd,pa in cur.fetchall():
        h.append(ph); d.append(pd); a.append(pa)
    ah = _bins(h, bins); ad = _bins(d, bins); aa = _bins(a, bins)
    psi_h = _psi(bh, ah); psi_d = _psi(bd, ad); psi_a = _psi(ba, aa)
    macro = (psi_h + psi_d + psi_a)/3.0
    sev = "ok"
    if macro > 0.2: sev = "warn"
    if macro > 0.5: sev = "alert"
    db.execute(text("INSERT INTO drift_alerts(psi_home,psi_draw,psi_away,bins,severity) VALUES(:h,:d,:a,:b,:s)"),
               {"h": psi_h, "d": psi_d, "a": psi_a, "b": bins, "s": sev})
    db.commit()
    return {"psi": {"home": psi_h, "draw": psi_d, "away": psi_a, "macro": macro}, "severity": sev}
