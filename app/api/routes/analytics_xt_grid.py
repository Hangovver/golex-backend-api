from fastapi import APIRouter
import random

router = APIRouter(tags=['analytics'], prefix='/analytics')

@router.get('/xt/grid/{fixture_id}')
def xt_grid(fixture_id: str, rows: int = 8, cols: int = 12):
    grid = [[ round(random.uniform(0,1),3) for _ in range(cols) ] for _ in range(rows) ]
    return { "fixture_id": fixture_id, "rows": rows, "cols": cols, "grid": grid }
