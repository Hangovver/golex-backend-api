from fastapi import APIRouter
router = APIRouter(tags=['admin'], prefix='/admin')

@router.post('/prewarm/fixtures_nextday')
def prewarm_nextday():
    # stub: would call upstream and cache
    return {'ok': True, 'prefetched': 120}
