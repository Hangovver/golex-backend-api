from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db
import math

router = APIRouter(tags=['quality'], prefix='/quality')

def ece_for_probs(rows, bins=10):
    # rows: [(p_home, p_draw, p_away, outcome_str)]
    # take max prob as predicted class prob
    buckets = [ {'sum_p':0.0, 'sum_y':0.0, 'n':0} for _ in range(bins) ]
    for ph, pd, pa, out in rows:
        predp = max(ph, pd, pa)
        predc = 'home' if ph >= pd and ph >= pa else 'draw' if pd >= ph and pd >= pa else 'away'
        y = 1.0 if out == predc else 0.0
        b = min(bins-1, int(predp * bins))
        buckets[b]['sum_p'] += float(predp)
        buckets[b]['sum_y'] += y
        buckets[b]['n'] += 1
    ece = 0.0
    curve = []
    for i, b in enumerate(buckets):
        if b['n'] == 0:
            curve.append(( (i+0.5)/bins, None ))
            continue
        p_hat = b['sum_p']/b['n']
        acc = b['sum_y']/b['n']
        ece += (b['n']/max(1,sum(bb['n'] for bb in buckets))) * abs(acc - p_hat)
        curve.append(( p_hat, acc ))
    return round(ece,4), curve

@router.get('/metrics')
def metrics(model_version: str | None = Query(None), limit: int = 2000, db: Session = Depends(get_db)):
    sql = """SELECT home_prob, draw_prob, away_prob, outcome FROM predictions_log
             {where}
             ORDER BY created_at DESC LIMIT :l"""
    where = ""
    params = {'l': limit}
    if model_version:
        where = "WHERE model_version=:v"
        params['v'] = model_version
    rows = db.execute(text(sql.format(where=where)), params).fetchall()
    if not rows:
        return {'acc': [], 'ece': [], 'bins': []}
    # accuracy rolling (last 30)
    last30 = rows[:30]
    acc = sum(1 for r in last30 if max(r[0],r[1],r[2]) == (r[0] if r[0]>=r[1] and r[0]>=r[2] else r[1] if r[1]>=r[0] and r[1]>=r[2] else r[2]))
    acc_series = [round(acc/len(last30),3)]
    ece, curve = ece_for_probs(rows)
    bins = [ {'p': round(p,3), 'acc': (round(a,3) if a is not None else None)} for p,a in curve ]
    return {'acc': acc_series, 'ece': [ece], 'bins': bins}
