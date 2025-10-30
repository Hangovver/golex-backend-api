from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db

router = APIRouter(tags=['search'], prefix='/search')

@router.get('/suggest')
def suggest(q: str = Query(..., min_length=1, max_length=60), limit: int = 10, db: Session = Depends(get_db)):
    like = f"%{q}%"
    sql = text("""
      SELECT entity_type, entity_id::text, name, country
      FROM search_index
      WHERE name ILIKE :like OR EXISTS (SELECT 1 FROM unnest(alt_names) a WHERE a ILIKE :like)
      ORDER BY similarity(name, :q) DESC NULLS LAST, name ASC
      LIMIT :limit
    """)
    rows = db.execute(sql, {'like': like, 'q': q, 'limit': limit}).fetchall()
    out = {'teams':[], 'players':[], 'leagues':[]}
    for t, eid, name, country in rows:
        out_key = t + 's' if t.endswith('r') or t.endswith('e') else t + 's'
        if out_key not in out: out_key = 'teams'
        out[out_key].append({'id': eid, 'name': name, 'country': country})
    return out

@router.get('')
def search(q: str, type: str | None = None, limit: int = 20, db: Session = Depends(get_db)):
    like = f"%{q}%"
    params = {'like': like, 'q': q, 'limit': limit}
    where = "WHERE name ILIKE :like OR EXISTS (SELECT 1 FROM unnest(alt_names) a WHERE a ILIKE :like)"
    if type in ('team','player','league'):
        where += " AND entity_type = :type"
        params['type'] = type
    sql = text(f"""
      SELECT entity_type, entity_id::text, name, country
      FROM search_index
      {where}
      ORDER BY similarity(name, :q) DESC NULLS LAST, name ASC
      LIMIT :limit
    """)
    rows = db.execute(sql, params).fetchall()
    return [ {'type': r[0], 'id': r[1], 'name': r[2], 'country': r[3]} for r in rows ]
