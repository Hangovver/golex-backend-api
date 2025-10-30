from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db
import math

router = APIRouter(tags=['metrics'], prefix='/metrics/calibration')

class CalibEventBody(BaseModel):
    fixture_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    p_home: float = Field(ge=0.0, le=1.0)
    p_draw: float = Field(ge=0.0, le=1.0)
    p_away: float = Field(ge=0.0, le=1.0)
    outcome: str = Field(pattern="^[HDA]$")

def _safe_log(x: float) -> float:
    EPS = 1e-9
    return math.log(max(x, EPS))

@router.post('/record')
def record_event(body: CalibEventBody, db: Session = Depends(get_db)):
    s = body.p_home + body.p_draw + body.p_away
    if s <= 0:
        raise HTTPException(400, detail="probabilities sum must be > 0")
    # normalize
    p_home = body.p_home / s
    p_draw = body.p_draw / s
    p_away = body.p_away / s
    db.execute(text("""INSERT INTO calibration_events(fixture_id, model_version, p_home, p_draw, p_away, outcome)
                      VALUES (:f, :v, :ph, :pd, :pa, :o)"""),
               {'f': body.fixture_id, 'v': body.model_version, 'ph': p_home, 'pd': p_draw, 'pa': p_away, 'o': body.outcome})
    db.commit()
    return {'ok': True}

@router.get('/summary')
def summary(db: Session = Depends(get_db), version: str | None = Query(None), hours: int = Query(720, ge=1, le=720*6), bins: int = Query(10, ge=2, le=30)):
    # Fetch rows
    q = "SELECT p_home, p_draw, p_away, outcome FROM calibration_events WHERE created_at >= NOW() - (:h || ' hours')::interval"
    params = {'h': hours}
    if version:
        q += " AND model_version=:v"
        params['v'] = version
    rows = db.execute(text(q), params).fetchall()
    n = len(rows)
    if n == 0:
        return {'count': 0, 'brier': None, 'logloss': None, 'ece': None, 'bins': []}

    # Compute metrics
    brier = 0.0; logloss = 0.0
    # ECE on predicted class
    bin_sums = [0.0]*bins
    bin_hits = [0.0]*bins
    bin_counts = [0]*bins

    for r in rows:
        ph, pd, pa, o = float(r[0]), float(r[1]), float(r[2]), r[3]
        yH, yD, yA = (1.0 if o=='H' else 0.0), (1.0 if o=='D' else 0.0), (1.0 if o=='A' else 0.0)
        brier += (ph - yH)**2 + (pd - yD)**2 + (pa - yA)**2
        # logloss
        p_out = ph if o=='H' else (pd if o=='D' else pa)
        logloss += -_safe_log(p_out)

        # ece
        probs = {'H': ph, 'D': pd, 'A': pa}
        pred = max(probs, key=probs.get)
        conf = probs[pred]
        acc = 1.0 if pred==o else 0.0
        b = min(int(conf * bins), bins-1)
        bin_sums[b] += conf
        bin_hits[b] += acc
        bin_counts[b] += 1

    brier /= n
    logloss /= n
    ece = 0.0
    out_bins = []
    for i in range(bins):
        if bin_counts[i] == 0:
            out_bins.append({'bin': i, 'count': 0, 'conf': None, 'acc': None, 'gap': None})
            continue
        conf_i = bin_sums[i] / bin_counts[i]
        acc_i = bin_hits[i] / bin_counts[i]
        gap = abs(conf_i - acc_i)
        ece += (bin_counts[i]/n) * gap
        out_bins.append({'bin': i, 'count': bin_counts[i], 'conf': conf_i, 'acc': acc_i, 'gap': gap})

    return {'count': n, 'brier': brier, 'logloss': logloss, 'ece': ece, 'bins': out_bins}
