from fastapi import APIRouter, Query
from typing import List, Dict

router = APIRouter(prefix="/predictions/explain", tags=["predictions-explain"])

@router.get("")
async def explain(fixtureId: str = Query(...)):
    # Demo top feature contributions (name, weight 0..1)
    feats = [
        {"name":"Form(5)", "weight":0.34},
        {"name":"xG trend", "weight":0.27},
        {"name":"Ev sahibi güç", "weight":0.21},
        {"name":"Sakatlık/eksik", "weight":0.10},
        {"name":"Fikstür yoğunluğu", "weight":0.08},
    ]
    return {"fixtureId": fixtureId, "top_features": feats, "rationale": "Son 5 maç formu ve xG trendi tahmini yukarı çekiyor."}
