from fastapi import APIRouter
from ..routes import fixtures_detail as _fxd
from ...services import proxy_client as PX
import os

router = APIRouter(prefix="/admin/source", tags=["admin-source"])

@router.get("")
async def info():
    return {
        "mode": "proxy" if PX.enabled() else "demo",
        "proxy_base": os.getenv("PROXY_BASE_URL",""),
        "timeout_s": float(os.getenv("PROXY_TIMEOUT_S","6"))
    }
