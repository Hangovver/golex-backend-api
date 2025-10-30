from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db
import httpx, os, datetime

router = APIRouter(tags=["admin"], prefix="/admin" )

@router.post("/prewarm-today-fixtures")
async def prewarm_today(db: Session = Depends(get_db)):
    api = os.getenv('PUBLIC_BASE_URL', 'http://localhost:8000/api/v1')
    today = datetime.datetime.utcnow().date().isoformat()
    urls = [f"{api}/fixtures?date={today}"]
    ok = 0
    async with httpx.AsyncClient(timeout=10) as client:
        for u in urls:
            try:
                r = await client.get(u, headers={"X-Client-Tag":"prewarm"})
                if r.status_code == 200:
                    ok += 1
            except Exception:
                pass
    return {"prewarmed": ok, "date": today}
