from fastapi import APIRouter, Depends, Query
from typing import List
import hashlib, random
from ...security.deps import get_db  # unused but consistent signature

router = APIRouter(tags=['fixtures'], prefix='/fixtures')

TAGS = ["Kırmızı Kart", "Sarı Kart", "Penaltı", "VAR", "Gol Yağmuru"]

def _tags_for_id(fid: str):
    # deterministic pseudo tags by hash
    h = hashlib.sha256(fid.encode()).digest()[0]
    picks = []
    if h % 7 == 0: picks.append("Kırmızı Kart")
    if h % 5 == 0: picks.append("Sarı Kart")
    if h % 11 == 0: picks.append("Penaltı")
    if h % 13 == 0: picks.append("VAR")
    if h % 17 == 0: picks.append("Gol Yağmuru")
    return picks

@router.get('/summary')
def summary(ids: str = Query(..., description="Comma-separated fixture ids")):
    out = []
    for fid in [x for x in ids.split(',') if x]:
        tags = _tags_for_id(fid)
        out.append({"id": fid, "hasCritical": bool(tags), "tags": tags})
    return {"summary": out}
