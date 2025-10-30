from fastapi import APIRouter, Query
from typing import List
import hashlib

router = APIRouter(tags=['fixtures'], prefix='/fixtures')

def _seed(s: str) -> int:
    return int(hashlib.sha1(s.encode('utf-8')).hexdigest()[:8], 16)

@router.get('/minimal')
def fixtures_minimal(date: str = Query(None)):
    # Demo: produce 10 minimal fixtures for the date (or generic)
    base = date or "today"
    items = []
    for i in range(10):
        fx = f"{base}-{i}"
        h = _seed(fx)
        fid = str(h)
        home = f"HOME{h%100}"
        away = f"AWAY{(h//7)%100}"
        status = ["SCHEDULED", "LIVE", "HT", "FT"][h % 4]
        items.append({
            "id": fid,
            "home": home,
            "away": away,
            "status": status,
            "score": {"home": (h%4), "away": ((h//3)%4)},
            "kickoff_iso": "2025-10-26T19:00:00Z"
        })
    return items
