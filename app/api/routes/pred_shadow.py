from fastapi import APIRouter
router = APIRouter(tags=['predictions'], prefix='/predictions')

@router.get('/shadow/{fixture_id}')
def shadow(fixture_id: str, canary: float = 0.1):
    # stub: compare prod vs shadow, but return only prod to clients
    prod = {"home": 0.42, "draw": 0.30, "away": 0.28}
    shadow = {"home": 0.45, "draw": 0.28, "away": 0.27}
    return {"fixture_id": fixture_id, "prod": prod, "shadow": shadow, "canary": canary}
