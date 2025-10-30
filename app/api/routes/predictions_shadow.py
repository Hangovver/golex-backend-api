from fastapi import APIRouter, Query
from typing import List, Dict
from ...services import metrics as M
import random, time

router = APIRouter(prefix="/predictions/shadow", tags=["predictions-shadow"])

LOG: List[Dict] = []

def _prod_pred(seed:int)->Dict[str,float]:
    random.seed(seed); return {"1": round(random.random(),3), "X": round(random.random(),3), "2": round(random.random(),3)}

def _canary_pred(seed:int)->Dict[str,float]:
    random.seed(seed+42); return {"1": round(random.random(),3), "X": round(random.random(),3), "2": round(random.random(),3)}

@router.get("/compare")
async def compare(fixtureId: str = Query(...)):
    s = int(''.join(filter(str.isdigit, fixtureId)) or 1)
    p = _prod_pred(s); c = _canary_pred(s)
    diff = {k: round((c.get(k,0)-p.get(k,0)),3) for k in set(p)|set(c)}
    item = {"ts": time.time(), "fixtureId": fixtureId, "prod": p, "canary": c, "diff": diff}
    LOG.append(item)
    M.inc("predictions_requests_total", {"endpoint":"shadow"}); return item

@router.get("/log")
async def log(limit: int = 50):
    M.inc("predictions_shadow_log_reads_total"); return {"items": LOG[-limit:]}
