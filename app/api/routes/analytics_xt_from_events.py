from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db

router = APIRouter(tags=['analytics'], prefix='/analytics')

@router.get('/xt/from-events/{fixture_id}')
def xt_from_events(fixture_id: str, rows: int = 8, cols: int = 12, db: Session = Depends(get_db)):
    # simple count-based xT proxy: shots weighted 1.0, key passes 0.5
    grid = [[0.0 for _ in range(cols)] for _ in range(rows)]
    def cell(x, y):
        i = min(rows-1, max(0, int((y or 0)/100.0 * rows)))
        j = min(cols-1, max(0, int((x or 0)/100.0 * cols)))
        return i, j
    q = text("""SELECT type, x, y, outcome FROM raw_events WHERE fixture_id=:f""")
    for t, x, y, outcome in db.execute(q, {'f': fixture_id}):
        i, j = cell(float(x or 0), float(y or 0))
        if t == 'shot':
            w = 1.0 if outcome == 'goal' else 0.7
        elif t == 'pass' and outcome == 'key':
            w = 0.5
        else:
            w = 0.1
        grid[i][j] += w
    # normalize 0..1
    m = max([max(r) for r in grid] or [1.0])
    if m > 0:
        grid = [[round(c/m,3) for c in r] for r in grid]
    return {'fixture_id': fixture_id, 'rows': rows, 'cols': cols, 'grid': grid}

@router.get('/pass-network/{fixture_id}')
def pass_network(fixture_id: str, db: Session = Depends(get_db)):
    # build edges team_id->player_id pairs for completed passes
    rows = db.execute(text("""
        SELECT COALESCE(player_id, '00000000-0000-0000-0000-000000000000')::text as src,
               COALESCE(subtype, '') as dst_player_id
        FROM raw_events
        WHERE fixture_id=:f AND type='pass' AND outcome='complete'
    """), {'f': fixture_id}).fetchall()
    # subtype holds 'to_player_id' in this simple schema
    edges = {}
    for src, dst in rows:
        if not dst: continue
        key = (src, dst)
        edges[key] = edges.get(key, 0) + 1
    return {'fixture_id': fixture_id, 'edges': [{'from': a, 'to': b, 'count': w} for (a,b), w in edges.items()]}
