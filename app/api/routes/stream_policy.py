from fastapi import APIRouter, Query
router = APIRouter(prefix="/stream", tags=["stream"])

@router.get("/policy")
async def policy(device: str = Query(None), net: str = Query(None)):
    # basit tavsiye: mobilde ws -> sse -> poll; yavaş ağlarda sse -> poll
    order = ["ws","sse","poll"]
    if net in ("2g","slow"): order = ["sse","poll","ws"]
    return {
        "order": order,
        "retryMs": [1000, 2000, 5000, 10000, 20000],
        "heartbeatSec": 25,
        "ssePath": "/api/v1/stream/sse2",
        "wsPath": "/api/v1/stream/ws"
    }
