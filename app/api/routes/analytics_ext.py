from fastapi import APIRouter
import random

router = APIRouter(tags=['analytics'], prefix='/analytics')

@router.get('/xt/{fixture_id}')
def xthreat(fixture_id: str):
    # 12-zone xT heat (stub)
    zones = [round(random.uniform(0,1),3) for _ in range(12)]
    return {"fixture_id": fixture_id, "zones": zones}

@router.get('/passnet/{fixture_id}')
def pass_network(fixture_id: str):
    # simple nodes/links stub
    nodes = [{"id": i, "label": f"P{i}"} for i in range(1,12)]
    links = [{"source": random.randint(1,11), "target": random.randint(1,11), "weight": random.randint(1,5)} for _ in range(20)]
    return {"fixture_id": fixture_id, "nodes": nodes, "links": links}
