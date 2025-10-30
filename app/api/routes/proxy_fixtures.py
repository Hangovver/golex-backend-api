from fastapi import APIRouter, HTTPException, Query
from . import rate_limit  # optional if exists
from ..services.apifootball import ApiFootball

router = APIRouter(prefix="/proxy", tags=["proxy"])

@router.get("/fixtures")
async def fixtures(date: str = Query(..., description="YYYY-MM-DD")):
    # This is an example proxy; in production ingestion is preferred.
    try:
        api = ApiFootball()
        data = await api.get("fixtures", params={"date": date})
        # sanitize/minify if needed
        return {"source": "apifootball", "date": date, "count": len(data.get("response", [])), "response": data.get("response", [])[:20]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
