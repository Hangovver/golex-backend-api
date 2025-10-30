from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib, math, random

from ...security.deps import get_db

router = APIRouter(tags=['fixtures'], prefix='/fixtures')

def _rng(fid: str):
    seed = int.from_bytes(hashlib.sha256(fid.encode()).digest()[:4], 'big')
    r = random.Random(seed)
    return r

@router.get('/{fid}/xg-mini')
def xg_mini(fid: str, buckets: int = 12):
    r = _rng(fid)
    home = []; away = []; ts = []
    h = 0.0; a = 0.0
    for i in range(buckets):
        inc_h = max(0.0, r.gauss(0.12, 0.08))
        inc_a = max(0.0, r.gauss(0.10, 0.07))
        h += inc_h; a += inc_a
        home.append(round(h, 2)); away.append(round(a, 2)); ts.append(i*7)  # her bucket ~7 dk
    return {'home': home, 'away': away, 't': ts, 'unit': 'minute'}

@router.get('/{fid}/form')
def form(fid: str, n: int = 5):
    r = _rng(fid)
    def gen():
        out = []
        for _ in range(n):
            x = r.random()
            out.append(1 if x>0.55 else (0 if x>0.25 else -1))
        return out
    return {'home': gen(), 'away': gen()}


@router.get('/{fid}/micro-stats')
def micro_stats(fid: str):
    r = _rng(fid)
    # plausible demo numbers
    sh_home = max(3, int(r.random()*14))
    sh_away = max(2, int(r.random()*12))
    xg_home = round(max(0.2, r.random()*2.4), 2)
    xg_away = round(max(0.2, r.random()*2.2), 2)
    return {'shots': {'home': sh_home, 'away': sh_away}, 'xg': {'home': xg_home, 'away': xg_away}}


@router.get('/{fid}/zone-heat')
def zone_heat(fid: str, rows: int = 6, cols: int = 5):
    r = _rng(fid)
    def grid():
        g = []
        for i in range(rows):
            row = []
            base = r.random()*0.6 + 0.2
            for j in range(cols):
                v = max(0.0, min(1.0, base + r.gauss(0.0, 0.15)))
                row.append(round(v, 3))
            g.append(row)
        return g
    return {'rows': rows, 'cols': cols, 'home': grid(), 'away': grid(), 'scale': [0.0, 1.0]}


@router.get('/{fid}/conditions')
def conditions(fid: str):
    r = _rng(fid)
    weathers = [('Güneşli','☀️'), ('Parçalı Bulutlu','⛅'), ('Bulutlu','☁️'), ('Yağmurlu','🌧️')]
    grounds = ['Kuru', 'Nemli', 'Islak', 'Ağır']
    w = weathers[int(r.random()*len(weathers))]
    g = grounds[int(r.random()*len(grounds))]
    temp = int(8 + r.random()*18)  # 8..26
    wind = int(r.random()*30)      # km/h
    return {'weather': {'desc': w[0], 'icon': w[1], 'temp_c': temp, 'wind_kmh': wind}, 'ground': g}

@router.get('/{fid}/card-foul-heat')
def card_foul_heat(fid: str, rows: int = 6, cols: int = 5):
    r = _rng(fid)
    def grid(scale):
        g = []
        for i in range(rows):
            row = []
            for j in range(cols):
                v = max(0.0, min(1.0, r.random()*scale + r.random()*0.2))
                row.append(round(v, 3))
            g.append(row)
        return g
    return {'rows': rows, 'cols': cols, 'fouls': grid(0.6), 'cards': grid(0.4), 'scale': [0.0, 1.0]}


@router.get('/{fid}/pressing-mini')
def pressing_mini(fid: str, buckets: int = 12):
    r = _rng(fid)
    def series():
        vals = []
        v = r.random()*0.3 + 0.2
        for _ in range(buckets):
            v = max(0.0, min(1.0, v + r.gauss(0.0, 0.08)))
            vals.append(round(v,3))
        return vals
    return {'home': series(), 'away': series(), 'unit': 'intensity'}


@router.get('/{fid}/possession-mini')
def possession_mini(fid: str):
    r = _rng(fid)
    h = max(0.35, min(0.65, r.random()*0.5 + 0.25))  # 35%..65%
    a = max(0.0, min(1.0, 1.0 - h))
    return {'home': round(h,3), 'away': round(a,3)}


@router.get('/{fid}/shot-map')
def shot_map(fid: str, n_home: int = 8, n_away: int = 7):
    r = _rng(fid)
    def shots(n):
        out = []
        for _ in range(n):
            x = min(1.0, max(0.0, r.random()))
            y = min(1.0, max(0.0, r.random()))
            goal = r.random() > 0.72
            xg = round(max(0.02, r.random()*0.45), 2)
            out.append({'x': x, 'y': y, 'goal': goal, 'xg': xg})
        return out
    return {'home': shots(n_home), 'away': shots(n_away)}


@router.get('/{fid}/attack-speed')
def attack_speed(fid: str, buckets: int = 10):
    r = _rng(fid)
    def series():
        vals = []
        v = r.random()*8 + 6
        for _ in range(buckets):
            v = max(0.0, v + r.gauss(0.0, 1.5))
            vals.append(int(v))
        return vals
    h = series(); a = series()
    return {'window_min': buckets, 'home': h, 'away': a, 'last10': {'home': h[-1], 'away': a[-1]}}


@router.get('/{fid}/pass-network-mini')
def pass_network_mini(fid: str, size: int = 6):
    r = _rng(fid)
    def grid():
        g = []
        for i in range(size):
            row = []
            for j in range(size):
                base = 0.2 if i==j else 0.0
                v = max(0.0, min(1.0, base + r.random()*0.9))
                row.append(round(v, 3))
            g.append(row)
        return g
    return {'size': size, 'home': grid(), 'away': grid(), 'scale': [0.0, 1.0]}


@router.get('/{fid}/momentum-mini')
def momentum_mini(fid: str, buckets: int = 16):
    r = _rng(fid)
    vals = []
    v = r.random()*0.4 - 0.2  # start between -0.2..0.2
    for _ in range(buckets):
        v = max(-1.0, min(1.0, v + r.gauss(0.0, 0.12)))
        vals.append(round(v, 3))
    return {'vals': vals, 'desc': 'home positive, away negative'}


@router.get('/{fid}/shot-type-distribution')
def shot_type_distribution(fid: str):
    r = _rng(fid)
    types = ['open_play','set_piece','counter','penalty','head']
    def distro():
        base = [int(r.random()*10+6), int(r.random()*4+2), int(r.random()*3+1), int(r.random()*2), int(r.random()*3+1)]
        return base
    return {'types': types, 'home': distro(), 'away': distro()}


@router.get('/{fid}/xthreat-mini')
def xthreat_mini(fid: str, buckets: int = 16):
    r = _rng(fid)
    vals = []
    v = r.random()*0.3 + 0.1
    for _ in range(buckets):
        v = max(0.0, min(1.0, v + r.gauss(0.0, 0.08)))
        vals.append(round(v, 3))
    conf = round(min(1.0, max(0.0, r.random()*0.5 + 0.5)), 3)
    return {'vals': vals, 'unit': 'xT', 'confidence': conf}


@router.get('/{fid}/gk-saves-heat')
def gk_saves_heat(fid: str, rows: int = 6, cols: int = 5):
    r = _rng(fid)
    def grid(scale):
        g = []
        for i in range(rows):
            row = []
            for j in range(cols):
                base = 0.05 if (i in (0, rows-1)) else 0.02
                v = max(0.0, min(1.0, base + r.random()*scale + r.random()*0.1))
                row.append(round(v, 3))
            g.append(row)
        return g
    return {'rows': rows, 'cols': cols, 'home': grid(0.5), 'away': grid(0.5), 'scale': [0.0, 1.0]}


@router.get('/{fid}/xg-cumulative')
def xg_cumulative(fid: str, buckets: int = 16):
    r = _rng(fid)
    def series():
        vals = []
        v = 0.0
        for _ in range(buckets):
            inc = max(0.0, r.random()*0.25 - 0.05)
            v += inc
            vals.append(round(v, 3))
        return vals
    return {'home': series(), 'away': series(), 'unit': 'xG'}


@router.get('/{fid}/setpiece-danger')
def setpiece_danger(fid: str, window_min: int = 10):
    r = _rng(fid)
    def score():
        return int(r.random()*12)  # 0..11 pseudo
    return {'window_min': window_min, 'home': score(), 'away': score()}


@router.get('/{fid}/directness-mini')
def directness_mini(fid: str):
    r = _rng(fid)
    # Higher means more vertical/direct play. 0..1
    return {'home': round(r.random(),3), 'away': round(r.random(),3)}


from datetime import datetime, timedelta

@router.get('/list-paged')
def fixtures_list_paged(cursor: str | None = None, limit: int = 20, status: str | None = None):
    """
    Server-driven paging demo:
    - cursor: opaque string (ISO time). If None → start from now.
    - returns: { items: [{id, home, away, kickoff, status}], nextCursor }
    """
    r = _rng(cursor or "seed")
    if cursor:
        base = datetime.fromisoformat(cursor)
    else:
        base = datetime.utcnow()
    items = []
    for i in range(limit):
        # pseudo fixtures going backwards in time
        kickoff = base - timedelta(minutes=(i+1)*5)
        fid = int(kickoff.timestamp())
        st = status or ( "LIVE" if i % 7 == 0 else "SCHEDULED" if i % 5 == 0 else "FT" if i % 11 == 0 else "HT" if i % 13 == 0 else "FT" )
        items.append({
            "id": str(fid),
            "home": "Home %d" % ((fid // 100) % 1000),
            "away": "Away %d" % ((fid // 10) % 1000),
            "kickoff": kickoff.isoformat() + "Z",
            "status": st
        })
    next_cursor = items[-1]["kickoff"]
    return {"items": items, "nextCursor": next_cursor}


@router.get('/{fid}/xg-time')
def xg_time(fid: str, buckets: int = 18):
    r = _rng(fid + "xgtime")
    def series():
        vals = []
        v = 0.1
        for _ in range(buckets):
            inc = max(0.0, r.random()*0.3 - 0.05)
            v = max(0.0, v + (inc - 0.08*r.random()))
            vals.append(round(max(0.0, min(1.5, v)), 3))
        return vals
    return {'home': series(), 'away': series(), 'unit': 'xG/min'}


@router.get('/{fid}/pass-heat')
def pass_heat(fid: str, rows: int = 6, cols: int = 9):
    r = _rng(fid + "passheat")
    def grid(scale):
        g = []
        for i in range(rows):
            row = []
            for j in range(cols):
                base = 0.01 + (0.03 if j > cols//2 else 0.0)
                v = max(0.0, min(1.0, base + r.random()*scale + r.random()*0.05))
                row.append(round(v, 3))
            g.append(row)
        return g
    return {'rows': rows, 'cols': cols, 'home': grid(0.6), 'away': grid(0.55), 'scale': [0.0, 1.0]}


@router.get('/{fid}/shot-map-full')
def shot_map_full(fid: str, count: int = 22):
    r = _rng(fid + "shotmap")
    def make(team):
        arr = []
        for _ in range(count):
            arr.append({
                "x": round(r.random(), 3),
                "y": round(r.random(), 3),
                "on_target": r.random() > 0.4,
                "goal": r.random() > 0.8,
                "team": team
            })
        return arr
    return {'shots': make("home") + make("away")}
