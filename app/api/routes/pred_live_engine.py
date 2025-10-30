from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=['predictions'], prefix='/predictions')

class LivePoint(BaseModel):
    minute: int
    home_goals: int
    away_goals: int
    red_home: int = 0
    red_away: int = 0
    xg_home: float = 0.0
    xg_away: float = 0.0

@router.post('/live/engine/{fixture_id}')
def engine(fixture_id: str, series: list[LivePoint], alpha: float = 0.25):
    h, d, a = 0.33, 0.34, 0.33
    out = []
    for p in sorted(series, key=lambda x: x.minute):
        # base adjustment by score
        lead = p.home_goals - p.away_goals
        m = max(0, min(90, p.minute)); w = m/90.0
        bh, bd, ba = h, d, a
        if lead > 0: bh += 0.22*w; ba -= 0.18*w; bd -= 0.04*w
        elif lead < 0: ba += 0.22*w; bh -= 0.18*w; bd -= 0.04*w
        else: bd += 0.12*w; bh -= 0.06*w; ba -= 0.06*w
        # red cards: one-red ~ 0.08 swing
        swing = 0.08 * (p.red_away - p.red_home)
        bh += swing; ba -= swing
        # xG momentum: differential scaled
        diff = p.xg_home - p.xg_away
        bh += 0.15*diff; ba -= 0.15*diff
        s = max(1e-6, bh+bd+ba); nh, nd, na = bh/s, bd/s, ba/s
        # EWMA
        h = alpha*nh + (1-alpha)*h
        d = alpha*nd + (1-alpha)*d
        a = alpha*na + (1-alpha)*a
        out.append({'minute': p.minute, 'home': round(h,4), 'draw': round(d,4), 'away': round(a,4)})
    return {'fixture_id': fixture_id, 'points': out}
