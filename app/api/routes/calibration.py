from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..deps import get_db
from ..metrics import set_macro_ece
import json, math

router = APIRouter(prefix="/admin/calibration", tags=["admin.calibration"])

def _ensure(db: Session):
    db.execute(text('''CREATE TABLE IF NOT EXISTS calibration_samples(
        ts TIMESTAMP DEFAULT NOW(),
        fixture_id TEXT,
        model_version TEXT,
        p_home REAL, p_draw REAL, p_away REAL,
        outcome TEXT CHECK (outcome IN ('home','draw','away'))
    )'''))
    db.commit()

@router.post("/ingest")
def ingest(fixture_id: str, model_version: str, p_home: float, p_draw: float, p_away: float, outcome: str, db: Session = Depends(get_db)):
    _ensure(db)
    if outcome not in ("home","draw","away"):
        outcome = "home"
    db.execute(text("INSERT INTO calibration_samples(fixture_id, model_version, p_home, p_draw, p_away, outcome) VALUES(:f,:m,:ph,:pd,:pa,:o)"),
               {"f": fixture_id, "m": model_version, "ph": p_home, "pd": p_draw, "pa": p_away, "o": outcome})
    db.commit()
    return {"ok": True}

def _bins(vals, ys, k):
    # vals: list of predicted probabilities, ys: list of {0,1}
    n = len(vals)
    if n == 0:
        return [], 0.0
    bins = [{"lo": i/k, "hi": (i+1)/k, "sum_p":0.0, "sum_y":0.0, "cnt":0} for i in range(k)]
    for p,y in zip(vals, ys):
        idx = min(k-1, max(0, int(p * k)))
        bins[idx]["sum_p"] += p
        bins[idx]["sum_y"] += y
        bins[idx]["cnt"] += 1
    ece = 0.0
    out = []
    for b in bins:
        if b["cnt"] == 0:
            out.append({"range":[b["lo"], b["hi"]], "count":0, "mean_pred":None, "empirical":None})
            continue
        mp = b["sum_p"]/b["cnt"]
        emp = b["sum_y"]/b["cnt"]
        ece += abs(mp - emp) * (b["cnt"]/n)
        out.append({"range":[b["lo"], b["hi"]], "count":b["cnt"], "mean_pred":mp, "empirical":emp})
    return out, ece

@router.get("/curve")
def curve(bins: int = 10, model_version: str | None = None, db: Session = Depends(get_db)):
    _ensure(db)
    where = ""
    params = {}
    if model_version:
        where = "WHERE model_version=:m"
        params["m"] = model_version
    rows = db.execute(text(f"SELECT p_home,p_draw,p_away,outcome FROM calibration_samples {where}")), params
    # fetchall workaround:
    cur = db.execute(text(f"SELECT p_home,p_draw,p_away,outcome FROM calibration_samples {where}"), params)
    vals_h, ys_h = [], []
    vals_d, ys_d = [], []
    vals_a, ys_a = [], []
    for p_home,p_draw,p_away,outcome in cur.fetchall():
        vals_h.append(p_home); ys_h.append(1 if outcome=='home' else 0)
        vals_d.append(p_draw); ys_d.append(1 if outcome=='draw' else 0)
        vals_a.append(p_away); ys_a.append(1 if outcome=='away' else 0)
    bh, e_h = _bins(vals_h, ys_h, bins)
    bd, e_d = _bins(vals_d, ys_d, bins)
    ba, e_a = _bins(vals_a, ys_a, bins)
    macro_ece = (e_h + e_d + e_a) / 3.0
    set_macro_ece(macro_ece)
    return {"home": bh, "draw": bd, "away": ba, "ece": {"home": e_h, "draw": e_d, "away": e_a, "macro": macro_ece}}

@router.get("/compare")
def compare(model_a: str, model_b: str, bins: int = 10, db: Session = Depends(get_db)):
    _ensure(db)
    def get_ece(v):
        cur = db.execute(text("SELECT p_home,p_draw,p_away,outcome FROM calibration_samples WHERE model_version=:m"), {"m": v})
        vals_h, ys_h = [], []
        vals_d, ys_d = [], []
        vals_a, ys_a = [], []
        for p_home,p_draw,p_away,outcome in cur.fetchall():
            vals_h.append(p_home); ys_h.append(1 if outcome=='home' else 0)
            vals_d.append(p_draw); ys_d.append(1 if outcome=='draw' else 0)
            vals_a.append(p_away); ys_a.append(1 if outcome=='away' else 0)
        _, e_h = _bins(vals_h, ys_h, bins)
        _, e_d = _bins(vals_d, ys_d, bins)
        _, e_a = _bins(vals_a, ys_a, bins)
        return (e_h + e_d + e_a) / 3.0
    e_a = get_ece(model_a)
    e_b = get_ece(model_b)
    return {"model_a": model_a, "model_b": model_b, "ece_a": e_a, "ece_b": e_b, "delta": e_b - e_a}
