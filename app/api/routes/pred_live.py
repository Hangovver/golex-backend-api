from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=['predictions'], prefix='/predictions')

class SeriesPoint(BaseModel):
    minute: int
    home_goals: int
    away_goals: int
    base_home: float | None = None
    base_draw: float | None = None
    base_away: float | None = None

def adjust(minute, hg, ag, h, d, a):
    lead = hg - ag
    m = max(0, min(90, minute))
    w = m/90.0
    if lead > 0:
        h = h + 0.25*w; a = max(0.01, a - 0.20*w); d = max(0.01, d - 0.05*w)
    elif lead < 0:
        a = a + 0.25*w; h = max(0.01, h - 0.20*w); d = max(0.01, d - 0.05*w)
    else:
        d = min(0.80, d + 0.15*w); h = max(0.01, h - 0.075*w); a = max(0.01, a - 0.075*w)
    s = h + d + a
    return h/s, d/s, a/s

@router.post('/live/{fixture_id}/series')
def live_series(fixture_id: str, series: list[SeriesPoint], alpha: float = 0.3):
    h, d, a = 0.33, 0.34, 0.33
    out = []
    for p in sorted(series, key=lambda x: x.minute):
        bh, bd, ba = p.base_home or h, p.base_draw or d, p.base_away or a
        nh, nd, na = adjust(p.minute, p.home_goals, p.away_goals, bh, bd, ba)
        # EWMA smoothing
        h = alpha*nh + (1-alpha)*h
        d = alpha*nd + (1-alpha)*d
        a = alpha*na + (1-alpha)*a
        out.append({ "minute": p.minute, "home": round(h,4), "draw": round(d,4), "away": round(a,4) })
    return { "fixture_id": fixture_id, "points": out }
