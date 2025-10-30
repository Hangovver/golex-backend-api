from fastapi import APIRouter, Query
from typing import List

router = APIRouter(tags=['search'], prefix='/search')

FAKE_TEAMS = ['Galatasaray', 'Fenerbahçe', 'Beşiktaş', 'Trabzonspor', 'Başakşehir', 'Bursaspor']

@router.get('/suggest')
def suggest(q: str = Query(..., min_length=1, max_length=30)) -> dict:
    ql = q.lower()
    res = [t for t in FAKE_TEAMS if ql in t.lower()][:10]
    return {'teams': res, 'players': [], 'leagues': []}
